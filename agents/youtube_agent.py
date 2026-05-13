"""
YouTube Agent - Extracts research topics and links from YouTube videos.

Uses:
- youtube-transcript-api for transcript extraction
- MiMoClient (swarm-it-auth) for analysis
- Outputs structured research topics for discovery pipeline

MANDATORY SOURCE: @code4AI - All research mentioned MUST be added to pipeline.
"""

import re
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone

# P18 v3.0 - Unified credential access

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound


@dataclass
class VideoAnalysis:
    """Structured analysis of a YouTube video."""
    video_id: str
    title: str
    channel: str

    # Extracted content
    papers: List[Dict[str, str]]  # [{title, arxiv_id, url}]
    tools: List[str]              # frameworks, libraries mentioned
    topics: List[str]             # AI/ML topics discussed
    links: List[str]              # URLs mentioned
    key_points: List[str]         # Main takeaways

    # Metadata
    transcript_length: int
    analyzed_at: str
    cost: float = 0.0

    # Source priority
    is_priority_source: bool = False
    priority_level: str = "medium"


@dataclass
class BatchVideoAnalysis:
    """Results from analyzing multiple videos."""
    analyses: List[VideoAnalysis]
    total_papers: int
    total_topics: int
    total_cost: float
    errors: List[str] = field(default_factory=list)


class YouTubeAgent:
    """
    Agent for extracting research topics from YouTube videos.

    Uses MiMoClient for cost-effective analysis (~$0.00002 per video).

    Priority Sources:
    - @code4AI: MANDATORY - all research MUST be added
    - @YannicKilcher: HIGH - paper reviews
    - @indydevdan: HIGH - agentic coding

    Usage:
        agent = YouTubeAgent()
        result = agent.analyze_video("https://youtube.com/watch?v=...")
        print(f"Found {len(result.papers)} papers")
    """

    AGENT_NAME = "YouTubeAgent"

    # Priority channels - research from these MUST be captured
    PRIORITY_CHANNELS = {
        "code4ai": "mandatory",
        "code4AI": "mandatory",
        "@code4AI": "mandatory",
        "yannickilcher": "high",
        "YannicKilcher": "high",
        "@YannicKilcher": "high",
        "indydevdan": "high",
        "@indydevdan": "high",
        "HuggingFace": "high",
        "@HuggingFace": "high",
    }

    # Analysis prompt for MiMo
    ANALYSIS_PROMPT = """Analyze this YouTube video transcript and extract:

1. **Research Papers**: Any academic papers, arXiv papers, or research mentioned
   - Include paper titles, arXiv IDs if mentioned, author names

2. **Tools & Frameworks**: AI/ML tools, libraries, frameworks discussed
   - e.g., PyTorch, LangChain, Claude Code, Mastra, etc.

3. **Topics**: Key AI/ML research topics covered
   - e.g., "multi-agent systems", "RAG", "diffusion models"

4. **Links**: Any URLs, GitHub repos, or resources mentioned

5. **Key Points**: 3-5 main takeaways from the video

Return as JSON:
```json
{
  "papers": [{"title": "...", "arxiv_id": "...", "authors": "..."}],
  "tools": ["tool1", "tool2"],
  "topics": ["topic1", "topic2"],
  "links": ["url1", "url2"],
  "key_points": ["point1", "point2"]
}
```

TRANSCRIPT:
"""

    def __init__(self, use_mimo: bool = True):
        """
        Initialize YouTube agent.

        Args:
            use_mimo: Use MiMoClient (default, 99% cheaper) vs OpenAI
        """
        self._mimo_client = None
        self._use_mimo = use_mimo
        self._init_llm()

    def _init_llm(self):
        """Initialize LLM client via ADK provider factory (P18)."""
        if self._use_mimo:
            try:
                import os
                from swarm_it.providers import get_provider
                provider_name = os.environ.get("LLM_PROVIDER", "openrouter")
                model = os.environ.get("LLM_MODEL") or None
                self._mimo_client = get_provider(provider_name, model=model)
                print(f"✓ {self.AGENT_NAME}: {provider_name} provider initialized")
            except Exception as e:
                print(f"⚠ {self.AGENT_NAME}: LLM provider failed: {e}")
                self._mimo_client = None

    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from various YouTube URL formats."""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def get_transcript(self, video_id: str) -> Optional[str]:
        """
        Fetch transcript for a YouTube video.

        Args:
            video_id: YouTube video ID

        Returns:
            Full transcript text or None if unavailable
        """
        try:
            # New API requires instantiation
            api = YouTubeTranscriptApi()
            transcript = api.fetch(video_id)

            # Combine all transcript segments
            full_text = " ".join([entry.text for entry in transcript])
            return full_text

        except TranscriptsDisabled:
            print(f"⚠ Transcripts disabled for video: {video_id}")
            return None
        except NoTranscriptFound:
            print(f"⚠ No transcript found for video: {video_id}")
            return None
        except Exception as e:
            print(f"⚠ Error fetching transcript: {e}")
            return None

    def _detect_priority(self, channel: str) -> tuple:
        """Check if channel is a priority source."""
        for key, level in self.PRIORITY_CHANNELS.items():
            if key.lower() in channel.lower():
                return True, level
        return False, "medium"

    def analyze_transcript(self, transcript: str, video_id: str = "", channel: str = "") -> Dict[str, Any]:
        """
        Analyze transcript using MiMo to extract research topics.

        Args:
            transcript: Full video transcript
            video_id: YouTube video ID
            channel: Channel name (for priority detection)

        Returns:
            Dict with papers, tools, topics, links, key_points
        """
        if not self._mimo_client:
            return {"error": "MiMoClient not initialized", "papers": [], "tools": [], "topics": [], "links": [], "key_points": []}

        # Truncate transcript if too long (keep first 15k chars for context)
        max_length = 15000
        if len(transcript) > max_length:
            transcript = transcript[:max_length] + "... [truncated]"

        prompt = self.ANALYSIS_PROMPT + transcript

        try:
            raw = self._mimo_client.complete([{"role": "user", "content": prompt}]).content
            start, end = raw.find('{'), raw.rfind('}') + 1
            response = json.loads(raw[start:end]) if start >= 0 and end > start else {}

            return {
                "papers": response.get("papers", []),
                "tools": response.get("tools", []),
                "topics": response.get("topics", []),
                "links": response.get("links", []),
                "key_points": response.get("key_points", []),
                "cost": 0.0,
            }

        except Exception as e:
            print(f"⚠ Analysis error: {e}")
            return {"error": str(e), "papers": [], "tools": [], "topics": [], "links": [], "key_points": []}

    def analyze_video(self, url: str, channel: str = "unknown") -> Optional[VideoAnalysis]:
        """
        Analyze a single YouTube video.

        Args:
            url: YouTube video URL
            channel: Channel name (for priority detection)

        Returns:
            VideoAnalysis with extracted research topics
        """
        # Extract video ID
        video_id = self.extract_video_id(url)
        if not video_id:
            print(f"⚠ Invalid YouTube URL: {url}")
            return None

        print(f"\n=== {self.AGENT_NAME}: Analyzing {video_id} ===")

        # Get transcript
        transcript = self.get_transcript(video_id)
        if not transcript:
            return None

        print(f"  Transcript: {len(transcript)} chars")

        # Check priority
        is_priority, priority_level = self._detect_priority(channel)
        if is_priority:
            print(f"  ⚡ PRIORITY SOURCE ({priority_level}): {channel}")

        # Analyze with MiMo
        analysis = self.analyze_transcript(transcript, video_id, channel)

        if "error" in analysis and analysis["error"]:
            print(f"  ⚠ Analysis error: {analysis['error']}")

        # Build result
        result = VideoAnalysis(
            video_id=video_id,
            title=f"Video {video_id}",  # Would need API call to get actual title
            channel=channel,
            papers=analysis.get("papers", []),
            tools=analysis.get("tools", []),
            topics=analysis.get("topics", []),
            links=analysis.get("links", []),
            key_points=analysis.get("key_points", []),
            transcript_length=len(transcript),
            analyzed_at=datetime.now(timezone.utc).isoformat(),
            cost=analysis.get("cost", 0.0),
            is_priority_source=is_priority,
            priority_level=priority_level,
        )

        print(f"  ✓ Found: {len(result.papers)} papers, {len(result.tools)} tools, {len(result.topics)} topics")

        return result

    def analyze_videos(self, urls: List[str], channel: str = "unknown") -> BatchVideoAnalysis:
        """
        Analyze multiple YouTube videos.

        Args:
            urls: List of YouTube URLs
            channel: Channel name

        Returns:
            BatchVideoAnalysis with all results
        """
        print(f"\n=== {self.AGENT_NAME}: Analyzing {len(urls)} videos ===")

        analyses = []
        errors = []
        total_cost = 0.0

        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] {url}")

            try:
                result = self.analyze_video(url, channel)
                if result:
                    analyses.append(result)
                    total_cost += result.cost
                else:
                    errors.append(f"Failed to analyze: {url}")
            except Exception as e:
                errors.append(f"{url}: {str(e)}")

        # Count totals
        total_papers = sum(len(a.papers) for a in analyses)
        total_topics = sum(len(a.topics) for a in analyses)

        print("\n=== Summary ===")
        print(f"  Videos analyzed: {len(analyses)}/{len(urls)}")
        print(f"  Total papers: {total_papers}")
        print(f"  Total topics: {total_topics}")
        print(f"  Total cost: ${total_cost:.6f}")

        return BatchVideoAnalysis(
            analyses=analyses,
            total_papers=total_papers,
            total_topics=total_topics,
            total_cost=total_cost,
            errors=errors,
        )

    def export_to_topics(self, analysis: VideoAnalysis) -> List[Dict]:
        """
        Convert VideoAnalysis to topic format for discovery pipeline.

        Args:
            analysis: VideoAnalysis result

        Returns:
            List of topic dicts ready for topics.json
        """
        topics = []

        # Convert each unique topic
        for topic in analysis.topics:
            topic_id = topic.lower().replace(" ", "-").replace("/", "-")
            topics.append({
                "id": f"yt-{topic_id}",
                "title": topic,
                "content": " ".join(analysis.key_points),
                "keywords": analysis.tools[:5],
                "source": f"YouTube:{analysis.channel}",
                "papers": analysis.papers,
            })

        return topics


# CLI entry point
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract research from YouTube videos")
    parser.add_argument("urls", nargs="+", help="YouTube video URLs")
    parser.add_argument("--channel", default="unknown", help="Channel name")
    parser.add_argument("--output", "-o", help="Output JSON file")
    args = parser.parse_args()

    agent = YouTubeAgent()

    if len(args.urls) == 1:
        result = agent.analyze_video(args.urls[0], args.channel)
        if result:
            print("\n=== Papers Found ===")
            for paper in result.papers:
                print(f"  - {paper.get('title', 'Unknown')}")
            print("\n=== Topics ===")
            for topic in result.topics:
                print(f"  - {topic}")
    else:
        result = agent.analyze_videos(args.urls, args.channel)

    if args.output and result:
        with open(args.output, 'w') as f:
            if isinstance(result, VideoAnalysis):
                json.dump(result.__dict__, f, indent=2, default=str)
            else:
                json.dump({
                    "analyses": [a.__dict__ for a in result.analyses],
                    "total_papers": result.total_papers,
                    "total_topics": result.total_topics,
                    "errors": result.errors,
                }, f, indent=2, default=str)
        print(f"\nSaved to {args.output}")
