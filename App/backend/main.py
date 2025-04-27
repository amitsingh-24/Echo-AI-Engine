import os
import tempfile
from fastapi import FastAPI, HTTPException, UploadFile, Form, File, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from pydantic import BaseModel, Field
from dotenv import load_dotenv
from backend.tutor_engine import generate_tutoring_response, generate_quiz
from backend.youtube_summarizer import YouTubeSummarizer, youtube_summarize

from langchain_groq import ChatGroq
from langchain.agents import initialize_agent, Tool

from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_community.tools.arxiv.tool import ArxivQueryRun
from langchain_community.tools.file_management.read import ReadFileTool
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
import markdown as md
from PyPDF2 import PdfReader
from tavily import TavilyClient

load_dotenv()
app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins = ["*"], allow_methods = ["*"], allow_headers = ["*"])
llm = ChatGroq(model= "gemma2-9b-it", temperature = 0.1, max_tokens = 3000)

UPLOAD_DIR = tempfile.gettempdir()
print(f"Temp dir: {UPLOAD_DIR}")
PDF_PATH = os.path.join(UPLOAD_DIR, "uploaded.pdf")

class Query(BaseModel):
    source: str
    query: str

class TutorRequest(BaseModel):
    subject: str
    level: str
    question: str
    learning_style: str = Field("Text-based")
    background: str = Field("Unknown")
    language: str = Field("English")

class QuizRequest(BaseModel):
    subject: str
    level: str
    num_questions: int = Field(5, ge=1, le=10)


def youtube_summarize(youtube_url: str) -> dict:
    summarizer = YouTubeSummarizer(llm)
    result = summarizer.summarize_video(youtube_url)
    print(result)
    if result["status"] == "success":
        unfiltered_text =  (result["summary"])
        return unfiltered_text
    
    return result["message"]

def search_duckduckgo(q: str) -> str:
    tool = Tool(name = "DuckDuckGO Search", func = DuckDuckGoSearchRun().run, description = "Perform Web Searches using DuckDuckGo")
    agent = initialize_agent([tool], llm, agent = "zero-shot-react-description", verbose = True)

    detailed_prompt = q + "\n\nPlease provide a thorough explanation amounting to roughly 1000 words."
    
    return agent.run(detailed_prompt)

def search_wikipedia(q :str) -> str:
    tool = Tool(name = "Wikipedia Search", func = WikipediaAPIWrapper().run, description = "Search Wikipedia for summaries")
    agent = initialize_agent([tool], llm, agent = "zero-shot-react-description", verbose = True)

    detailed_prompt = q + "\n\nPlease provide a thorough explanation amounting to roughly 1000 words."

    return agent.run(detailed_prompt)

def search_arxiv(q: str) -> str:
    tool = Tool(name = "Arxiv Search", func = ArxivQueryRun().run, description = "Search academic papers on arXiv")
    agent = initialize_agent([tool], llm, agent = "zero-shot-react-description", verbose = True)

    detailed_prompt = q + "\n\nPlease provide 5 latest papers and 5 top cited papers."
    return agent.run(detailed_prompt)

def search_tavily(q: str) -> str:
    tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    response = tavily_client.search(q, limit = 50)

    formatted_results = []
    for result in response.get("results", []):
        formatted_results.append(f"Title: {result['title']}\nURL: {result['url']}\nContent: {result['content']}\n")
    return "\n".join(formatted_results)


map_prompt = PromptTemplate(
    template="""
You are summarizing a part of a document:

{text}

Provide a concise 2–3 sentence summary:
""",
    input_variables=["text"],
)

combine_prompt = PromptTemplate(
    template="""
You have these summaries of each section:
{text}

Combine them into one coherent, well-structured final summary (10 -12 paragraphs):
""",
    input_variables=["text"],
)

pdf_summarize_chain = load_summarize_chain(
    llm=llm,
    chain_type="map_reduce",
    map_prompt=map_prompt,
    combine_prompt=combine_prompt,
    verbose=False,
)

MAX_TOKENS = 1024
CHARS_PER_TOKEN = 4

def intelligent_split(text: str):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n\n", "\n", " ", ""],
    )
    docs = splitter.create_documents([text])
    total_tokens = sum(len(d.page_content) // CHARS_PER_TOKEN for d in docs)
    if total_tokens <= MAX_TOKENS:
        return docs

    max_chars = MAX_TOKENS * CHARS_PER_TOKEN
    cum = 0
    safe = []
    for d in docs:
        cum += len(d.page_content)
        if cum > max_chars:
            break
        safe.append(d)
    return safe

async def llm_summarize_text(text: str) -> str:
    docs = intelligent_split(text)
    result = await pdf_summarize_chain.ainvoke(docs)
    if isinstance(result, dict):
        summary = result.get("output_text") or result.get("summary") or ""
    else:
        summary = result
    return summary.strip()

@app.post("/api/pdf-summarize")
async def pdf_summarize(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        return JSONResponse({"error": "Only PDF allowed"}, status_code=400)

    contents = await file.read()
    with open(PDF_PATH, "wb") as f:
        f.write(contents)

    try:
        reader = PdfReader(PDF_PATH)
        full_text = "\n\n".join(p.extract_text() or "" for p in reader.pages)
        summary = await llm_summarize_text(full_text)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(PDF_PATH):
            os.remove(PDF_PATH)


# Tutor endpoint
@app.post("/tutor")
async def tutor_endpoint(data: TutorRequest):
    try:
        resp = generate_tutoring_response(
            data.subject,
            data.level,
            data.question,
            data.learning_style,
            data.background,
            data.language
        )
        html = md.markdown(resp, extensions=["fenced_code", "tables"])
        # 3) return it
        return {"html": html}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/quiz")
async def quiz_endpoint(data: QuizRequest):
    try:
        quiz_list = generate_quiz(data.subject, data.level, data.num_questions)
        md_lines = []
        for i, q in enumerate(quiz_list, 1):
            md_lines.append(f"### {i}. {q['question']}\n")
            for letter, opt in zip(["A", "B", "C", "D"], q["options"]):
                md_lines.append(f"- **{letter}.** {opt}")
            md_lines.append(f"\n**Answer: {q['correct_answer']}**\n")
        md_text = "\n".join(md_lines)

        html = md.markdown(md_text, extensions=["fenced_code", "tables"])

        return {"html": html}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search")
def api_search(body: Query):
    src = body.source.lower()
    if src == "youtube":
        raw = youtube_summarize(body.query)
    elif src == "duckduckgo":
        raw = search_duckduckgo(body.query)
    elif src == "wikipedia":
        raw = search_wikipedia(body.query)
    elif src == "arxiv":
        raw = search_arxiv(body.query)
    elif src == "tavily":
        raw = search_tavily(body.query) 
    else:
        raise HTTPException(404, f"Unknown source '{body.source}'")

    html = md.markdown(raw, extensions=["fenced_code", "tables"])
    return {"html": html}


FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend"))
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
