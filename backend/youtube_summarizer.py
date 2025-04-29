import time
import re
from typing import Optional
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    TooManyRequests,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate

class YouTubeSummarizer:
    def __init__(self, llm):
        self.llm = llm

        # ─── Split the transcript into manageable chunks ─────────────────
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=10000,
            chunk_overlap=1000,
            separators=["\n\n", "\n", " ", ""],
        )

        # ─── Prompts for the map‐reduce summarizer chain ─────────────────
        self.map_prompt = PromptTemplate(
            template="""
            Summarize the following part of a YouTube video transcript:
            "{text}"

            KEY POINTS AND TAKEAWAYS:
            """,
            input_variables=["text"],
        )
        self.combine_prompt = PromptTemplate(
            template="""
            Create a detailed summary of the YouTube video based on these transcript summaries:
            "{text}"

            Please structure the summary as follows:
            1. Main Topic/Theme
            2. Key Points
            3. Important Details
            4. Conclusions/Takeaways

            DETAILED SUMMARY:
            """,
            input_variables=["text"],
        )

        # ─── Build the map‐reduce chain once ──────────────────────────────
        self.chain = load_summarize_chain(
            llm=self.llm,
            chain_type="map_reduce",
            map_prompt=self.map_prompt,
            combine_prompt=self.combine_prompt,
            verbose=False,
        )

    def extract_video_id(self, youtube_url: str) -> Optional[str]:
        """
        Extract video ID from multiple YouTube URL patterns.
        """
        patterns = [
            r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?]*)",
            r"(?:youtube\.com/shorts/)([^&\n?]*)"
        ]
        for pat in patterns:
            m = re.search(pat, youtube_url)
            if m:
                return m.group(1)
        return None

    def get_transcript(self, video_id: str) -> str:
        """
        Try up to 3× on the official API, then fall back to public Invidious mirrors
        if YouTube returns TooManyRequests (429).
        """
        # None = default YouTube endpoint; then try these Invidious hosts:
        hosts = [None, "https://yewtu.be", "https://yewtu.cafe", "https://yewtu.snopyta.org"]
        for host in hosts:
            for attempt in range(3):
                try:
                    if host:
                        entries = YouTubeTranscriptApi.get_transcript(
                            video_id, languages=["en"], host=host
                        )
                    else:
                        entries = YouTubeTranscriptApi.get_transcript(
                            video_id, languages=["en"]
                        )
                    # ─── KEY FIX ─── always index e["text"]
                    return " ".join(e["text"] for e in entries)
                except TooManyRequests:
                    # exponential back-off then retry
                    time.sleep(2 * (attempt + 1))
                except (TranscriptsDisabled, NoTranscriptFound):
                    # no transcript on this host → break to try next host
                    break
        raise RuntimeError(f"Could not retrieve a transcript for video ID {video_id}")

    def summarize_video(self, youtube_url: str) -> dict:
        vid = self.extract_video_id(youtube_url)
        if not vid:
            return {"status": "error", "message": "Invalid YouTube URL"}

        # fetch + fallback logic above
        try:
            transcript = self.get_transcript(vid)
        except Exception as e:
            return {"status": "error", "message": str(e)}

        docs = self.text_splitter.create_documents([transcript])
        summary = self.chain.run(docs)
        return {"status": "success", "summary": summary, "video_id": vid}
