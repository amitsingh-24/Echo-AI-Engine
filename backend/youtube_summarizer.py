from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from typing import Optional
import re

class YouTubeSummarizer:
    def __init__(self, llm):
        
        self.llm = llm

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=10000,
            chunk_overlap=1000,
            separators=["\n\n", "\n", " ", ""]
        )

        self.map_prompt_template = """
        Summarize the following part of a YouTube video transcript:
        "{text}"
        
        KEY POINTS AND TAKEAWAYS:
        """
        
        self.combine_prompt_template = """
        Create a detailed summary of the YouTube video based on these transcript summaries:
        "{text}"
        
        Please structure the summary as follows:
        1. Main Topic/Theme
        2. Key Points
        3. Important Details
        4. Conclusions/Takeaways
        
        DETAILED SUMMARY:
        """

        self.map_prompt = PromptTemplate(
            template=self.map_prompt_template,
            input_variables=["text"]
        )
        
        self.combine_prompt = PromptTemplate(
            template=self.combine_prompt_template,
            input_variables=["text"]
        )
        
        self.chain = load_summarize_chain(
            llm=self.llm,
            chain_type="map_reduce",
            map_prompt=self.map_prompt,
            combine_prompt=self.combine_prompt,
            verbose=False
        )

    def extract_video_id(self, youtube_url: str) -> Optional[str]:
        """
        Extract video ID from various forms of YouTube URLs
        """
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?]*)',
            r'(?:youtube\.com\/shorts\/)([^&\n?]*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, youtube_url)
            print(match)
            if match:
                return match.group(1)
        return None
    
    def _fetch(self, video_id: str, languages: list) -> str:
        entries = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        return " ".join([e["text"] for e in entries])


    def get_transcript(self, video_id: str) -> str:
        """
        Fetch a transcript for video_id, preferring English but smoothly
        falling back to any generated/manual transcript or translation.
        """
        try:
            entries = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
            return " ".join([e["text"] for e in entries])
        except (TranscriptsDisabled, NoTranscriptFound):
            transcripts = YouTubeTranscriptApi.list_transcripts(video_id)

            try:
                gen = transcripts.find_generated_transcript(
                    [t.language_code for t in transcripts]
                )
                snippets = gen.fetch()
                return " ".join([snippet["text"] for snippet in snippets])
            except NoTranscriptFound:
                pass

            try:
                man = transcripts.find_manually_created_transcript(
                    [t.language_code for t in transcripts]
                )
                snippets = man.fetch()
                return " ".join([snippet["text"] for snippet in snippets])
            except NoTranscriptFound:
                pass

            tr = transcripts.find_transcript(["en"])
            snippets = tr.fetch()
            return " ".join([snippet["text"] for snippet in snippets])
        
    def summarize_video(self, youtube_url: str) -> dict:
        """
        Summarize a YouTube video given its URL
        """
        try:
            video_id = self.extract_video_id(youtube_url)
            if not video_id:
                return {
                    "status": "error",
                    "message": "Invalid YouTube URL"
                }

            transcript = self.get_transcript(video_id)
            
            texts = self.text_splitter.create_documents([transcript])

            summary = self.chain.run(texts)
            
            return {
                "status": "success",
                "summary": summary,
                "video_id": video_id
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
