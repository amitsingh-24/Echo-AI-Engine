# 🧠 EchoNeuron AI Engine

EchoNeuron AI Engine is a next-generation, unified assistant that brings together:

- **Live Web Lookup** (Tavily)
- **Web Search** (DuckDuckGo)
- **Wikipedia Search** (Wikipedia)
- **Academic Search** (ArXiv)
- **YouTube Video Summarization**
- **PDF Summarization**
- **Personalized Tutoring**
- **On-the-fly Quiz Generation**

---

## 🚀 Features

- **Multi-Source Search:** Web, Wikipedia, ArXiv, Tavily  
- **Video & Document Summaries:** YouTube & PDF  
- **Interactive Tutor:** Tailored Q&A with style & level options  
- **Quiz Generator:** Instant MCQs with answers  
- **Vanilla JS Front-end:** Clean, responsive UI  
- **Secure CI/CD:** Docker + Render.com + Env-safe API key handling  

---

## 📦 Tech Stack

- **Backend:** Python 3.12, FastAPI  
- **LLM Orchestration:** LangChain, ChatGroq (Groq API)  
- **Transcript:** youtube-transcript-api  
- **PDF Parsing:** PyPDF2  
- **Front-end:** HTML, CSS, Vanilla JavaScript  
- **Containerization:** Docker  
- **Deployment:** Render.com (or any Docker-compatible host)  

---

## 🔧 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/EchoNeuron-AI-Engine.git
cd EchoNeuron-AI-Engine
```
### 2. Create & Populate the .env File

```bash
cp .env.example .env
```

Then, edit the .env file:

```bash
# .env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
```
### 3. Install Dependencies

Create a virtual environment and install the required packages:

```bash
python -m venv .venv
```
Activate the virtual environment:

#### Linux/macOS:
```bash
source .venv/bin/activate
```

#### Windows:
```bash
.venv\Scripts\activate
```

Upgrade pip and install dependencies:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run Locally
Start the FastAPI server using:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```
Open your browser and navigate to http://localhost:8000 to access the application.

--- 

## 🐳 Docker

Alternatively, build and run the application using Docker:

```bash
docker build -t echoneuron-ai .
docker run -it --rm -p 8000:8000 \
  -e GROQ_API_KEY="${GROQ_API_KEY}" \
  -e TAVILY_API_KEY="${TAVILY_API_KEY}" \
  echoneuron-ai
```
---
## ☁️ Deployment on Render.com

- Sign up at Render.
- Create a Web Service from your GitHub repository.
- Choose Docker as the deployment environment.
- Set these environment variables in the Render dashboard: GROQ_API_KEY, TAVILY_API_KEY
- Deploy the main branch — Render will build and launch the service automatically.
- You can also use the provided render.yaml for Infrastructure as Code.

---
## 📚 Usage

- **Home**: Overview of capabilities.
- **Live Lookup**: Select an engine and enter your query.
- **Web Search**: Search for things like google.
- **Wikipedia Search** : Wikipedia search engine
- **YouTube Summarizer**: Paste a YouTube video URL.
- **PDF Summarizer**: Upload a PDF file.
- **Tutor**: Ask questions by subject, level, and style.
- **Quiz Generator**: Choose a subject and difficulty to generate quizzes.

---

## ⚖️ License
This project is Apache-license-2.0. See the LICENSE file for details.
