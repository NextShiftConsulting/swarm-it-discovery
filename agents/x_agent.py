"""
X Agent (Twitter) - Extracts research papers and topics from X/Twitter posts.

Scans priority ML accounts for paper links, arXiv IDs, and research discussions.
Uses MiMoClient for analysis.

Priority Accounts:
- @_akhaliq (MANDATORY) - Daily paper summaries
- @papers_daily - arXiv highlights
- @DrJimFan - NVIDIA AI research
- @huggingface - Model releases
"""

import re
import json
import httpx
from typing import List, Dict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

# P18 v3.0 - Unified credential access
from swarm_auth import get_credential


@dataclass
class TweetAnalysis:
    """Analysis of a single tweet or thread."""
    tweet_id: str
    author: str
    content: str

    # Extracted research
    papers: List[Dict[str, str]]  # [{title, arxiv_id, url}]
    arxiv_ids: List[str]          # Direct arXiv IDs found
    links: List[str]              # URLs in tweet
    topics: List[str]             # AI/ML topics

    # Metadata
    posted_at: str
    analyzed_at: str
    is_priority: bool
    priority_level: str


@dataclass
class BatchTweetAnalysis:
    """Results from analyzing multiple tweets."""
    analyses: List[TweetAnalysis]
    total_papers: int
    total_arxiv_ids: int
    unique_arxiv_ids: List[str]
    errors: List[str] = field(default_factory=list)


class XAgent:
    """
    Agent for extracting research papers from X/Twitter.

    Monitors priority ML accounts and extracts:
    - arXiv paper links and IDs
    - Paper titles and authors
    - Research topics and tools
    - GitHub repository links

    Usage:
        agent = XAgent()
        result = agent.scan_account("_akhaliq", days=1)
        print(f"Found {len(result.unique_arxiv_ids)} papers")
    """

    AGENT_NAME = "XAgent"

    # Priority accounts - research from these gets special treatment
    PRIORITY_ACCOUNTS = {
        "_akhaliq": "mandatory",      # Daily paper summaries
        "ak92501": "mandatory",       # Alt account
        "papers_daily": "high",       # arXiv highlights
        "DrJimFan": "high",           # NVIDIA AI
        "huggingface": "high",        # Model releases
        "ylaboratory": "high",        # Yannic Kilcher
        "GoogleDeepMind": "high",     # DeepMind research
        "AnthropicAI": "high",        # Anthropic research
        "OpenAI": "high",             # OpenAI research
        "kaborimike": "medium",       # AI roundups
        "AlphaSignalAI": "medium",    # AI news
        "ai__pub": "medium",          # AI publications
    }

    # Regex patterns for extracting arXiv IDs
    ARXIV_PATTERNS = [
        r'arxiv\.org/abs/(\d{4}\.\d{4,5}(?:v\d+)?)',
        r'arxiv\.org/pdf/(\d{4}\.\d{4,5}(?:v\d+)?)',
        r'huggingface\.co/papers/(\d{4}\.\d{4,5}(?:v\d+)?)',  # HuggingFace papers
        r'hf\.co/papers/(\d{4}\.\d{4,5}(?:v\d+)?)',           # Short HF URL
        r'arxiv:(\d{4}\.\d{4,5}(?:v\d+)?)',
        r'\[(\d{4}\.\d{4,5}(?:v\d+)?)\]',
    ]

    # Analysis prompt for MiMo
    ANALYSIS_PROMPT = """Analyze this X/Twitter post about ML/AI research.

Extract:
1. **Papers**: Any research papers mentioned (title, arXiv ID if present)
2. **Topics**: Key ML/AI research topics (e.g., "transformers", "RLHF", "diffusion")
3. **Tools**: Frameworks, libraries, models mentioned
4. **Key Claims**: Main research findings or announcements

Return as JSON:
```json
{
  "papers": [{"title": "...", "arxiv_id": "..."}],
  "topics": ["topic1", "topic2"],
  "tools": ["tool1", "tool2"],
  "key_claims": ["claim1", "claim2"]
}
```

TWEET:
"""

    def __init__(self, use_mimo: bool = True):
        """
        Initialize X agent.

        Args:
            use_mimo: Use MiMoClient for analysis
        """
        self._mimo_client = None
        self._use_mimo = use_mimo
        self._http_client = None
        self._init_clients()

    def _init_clients(self):
        """Initialize LLM and HTTP clients."""
        # LLM for analysis (ADK provider factory, P18)
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

        # HTTP client for API calls
        self._http_client = httpx.Client(timeout=30)

    def _get_priority(self, username: str) -> tuple:
        """Check if account is a priority source."""
        username_clean = username.lstrip('@').lower()
        for account, level in self.PRIORITY_ACCOUNTS.items():
            if account.lower() == username_clean:
                return True, level
        return False, "low"

    def extract_arxiv_ids(self, text: str) -> List[str]:
        """
        Extract arXiv IDs from text.

        Args:
            text: Tweet or post text

        Returns:
            List of arXiv IDs found
        """
        arxiv_ids = []
        for pattern in self.ARXIV_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            arxiv_ids.extend(matches)

        # Deduplicate while preserving order
        seen = set()
        unique = []
        for aid in arxiv_ids:
            if aid not in seen:
                seen.add(aid)
                unique.append(aid)

        return unique

    def extract_links(self, text: str) -> List[str]:
        """Extract all URLs from text."""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.findall(url_pattern, text)

    def fetch_tweets_nitter(self, username: str, days: int = 1) -> List[Dict]:
        """
        Fetch tweets using Nitter (open source Twitter frontend).

        Args:
            username: Twitter username (without @)
            days: Days to look back

        Returns:
            List of tweet dicts
        """
        # Try multiple Nitter instances
        nitter_instances = [
            "nitter.net",
            "nitter.privacydev.net",
            "nitter.poast.org",
        ]

        tweets = []
        username = username.lstrip('@')

        for instance in nitter_instances:
            try:
                url = f"https://{instance}/{username}/rss"
                response = self._http_client.get(url)

                if response.status_code == 200:
                    # Parse RSS feed
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(response.text)

                    for item in root.findall('.//item'):
                        title = item.find('title')
                        link = item.find('link')
                        pubdate = item.find('pubDate')
                        description = item.find('description')

                        if title is not None and description is not None:
                            tweets.append({
                                'id': link.text.split('/')[-1] if link is not None else '',
                                'author': username,
                                'content': description.text or title.text,
                                'posted_at': pubdate.text if pubdate is not None else '',
                                'url': link.text if link is not None else '',
                            })

                    if tweets:
                        print(f"  ✓ Fetched {len(tweets)} tweets from {instance}")
                        break

            except Exception as e:
                print(f"  ⚠ {instance} failed: {e}")
                continue

        return tweets

    def fetch_tweets_api(self, username: str, days: int = 1) -> List[Dict]:
        """
        Fetch tweets using X API v2.

        Requires SWARM_X_BEARER_TOKEN environment variable.

        Args:
            username: Twitter username
            days: Days to look back

        Returns:
            List of tweet dicts
        """
        try:
            bearer_token = get_credential("X_BEARER_TOKEN")

            if not bearer_token:
                print("  ⚠ No X API token found, falling back to Nitter")
                return self.fetch_tweets_nitter(username, days)

            headers = {"Authorization": f"Bearer {bearer_token}"}

            # Get user ID
            user_url = f"https://api.twitter.com/2/users/by/username/{username}"
            user_response = self._http_client.get(user_url, headers=headers)

            if user_response.status_code != 200:
                print("  ⚠ User lookup failed, falling back to Nitter")
                return self.fetch_tweets_nitter(username, days)

            user_id = user_response.json()['data']['id']

            # Get tweets - X API requires RFC3339 format without microseconds
            start_time = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
            tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
            params = {
                "start_time": start_time,
                "max_results": 100,
                "tweet.fields": "created_at,text,entities",
            }

            tweets_response = self._http_client.get(tweets_url, headers=headers, params=params)

            if tweets_response.status_code != 200:
                print(f"  ⚠ Tweets fetch failed ({tweets_response.status_code})")
                return self.fetch_tweets_nitter(username, days)

            tweets = []
            for tweet in tweets_response.json().get('data', []):
                tweets.append({
                    'id': tweet['id'],
                    'author': username,
                    'content': tweet['text'],
                    'posted_at': tweet.get('created_at', ''),
                    'url': f"https://twitter.com/{username}/status/{tweet['id']}",
                    'entities': tweet.get('entities', {}),  # Include entities for URL expansion
                })

            print(f"  ✓ Fetched {len(tweets)} tweets via API")
            return tweets

        except Exception as e:
            print(f"  ⚠ API failed: {e}, falling back to Nitter")
            return self.fetch_tweets_nitter(username, days)

    def analyze_tweet(self, tweet: Dict) -> TweetAnalysis:
        """
        Analyze a single tweet for research content.

        Args:
            tweet: Tweet dict with content

        Returns:
            TweetAnalysis with extracted research
        """
        content = tweet.get('content', '')
        author = tweet.get('author', 'unknown')

        # Extract arXiv IDs from tweet text
        arxiv_ids = self.extract_arxiv_ids(content)
        links = self.extract_links(content)

        # Also check expanded URLs from entities (X API provides these)
        entities = tweet.get('entities', {})
        for url_entity in entities.get('urls', []):
            expanded_url = url_entity.get('expanded_url', '')
            arxiv_ids.extend(self.extract_arxiv_ids(expanded_url))
            if expanded_url and expanded_url not in links:
                links.append(expanded_url)

        # Check priority
        is_priority, priority_level = self._get_priority(author)

        # Use MiMo for deeper analysis if available
        papers = []
        topics = []

        if self._mimo_client and len(content) > 50:
            try:
                prompt = self.ANALYSIS_PROMPT + content[:2000]
                raw = self._mimo_client.complete([{"role": "user", "content": prompt}]).content
                start, end = raw.find('{'), raw.rfind('}') + 1
                response = json.loads(raw[start:end]) if start >= 0 and end > start else {}

                papers = response.get('papers', [])
                topics = response.get('topics', [])

            except Exception as e:
                print(f"  ⚠ LLM analysis failed: {e}")

        # Add arXiv papers found via regex
        for arxiv_id in arxiv_ids:
            if not any(p.get('arxiv_id') == arxiv_id for p in papers):
                papers.append({
                    'title': f"arXiv:{arxiv_id}",
                    'arxiv_id': arxiv_id,
                    'url': f"https://arxiv.org/abs/{arxiv_id}"
                })

        return TweetAnalysis(
            tweet_id=tweet.get('id', ''),
            author=author,
            content=content[:500],
            papers=papers,
            arxiv_ids=arxiv_ids,
            links=links,
            topics=topics,
            posted_at=tweet.get('posted_at', ''),
            analyzed_at=datetime.now(timezone.utc).isoformat(),
            is_priority=is_priority,
            priority_level=priority_level,
        )

    def scan_account(self, username: str, days: int = 1) -> BatchTweetAnalysis:
        """
        Scan an X account for research papers.

        Args:
            username: Twitter/X username
            days: Days to look back

        Returns:
            BatchTweetAnalysis with all papers found
        """
        username = username.lstrip('@')
        is_priority, priority_level = self._get_priority(username)

        print(f"\n=== {self.AGENT_NAME}: Scanning @{username} ===")
        if is_priority:
            print(f"  ⚡ PRIORITY SOURCE ({priority_level})")

        # Fetch tweets
        tweets = self.fetch_tweets_api(username, days)

        if not tweets:
            print("  ⚠ No tweets found")
            return BatchTweetAnalysis(
                analyses=[],
                total_papers=0,
                total_arxiv_ids=0,
                unique_arxiv_ids=[],
                errors=[f"No tweets found for @{username}"]
            )

        # Analyze each tweet
        analyses = []
        all_arxiv_ids = []

        for tweet in tweets:
            analysis = self.analyze_tweet(tweet)
            if analysis.arxiv_ids or analysis.papers:
                analyses.append(analysis)
                all_arxiv_ids.extend(analysis.arxiv_ids)

        # Deduplicate arXiv IDs
        unique_arxiv = list(dict.fromkeys(all_arxiv_ids))

        total_papers = sum(len(a.papers) for a in analyses)

        print(f"  ✓ Found {total_papers} papers, {len(unique_arxiv)} unique arXiv IDs")

        return BatchTweetAnalysis(
            analyses=analyses,
            total_papers=total_papers,
            total_arxiv_ids=len(all_arxiv_ids),
            unique_arxiv_ids=unique_arxiv,
        )

    def scan_priority_accounts(self, days: int = 1) -> BatchTweetAnalysis:
        """
        Scan all priority accounts for research papers.

        Args:
            days: Days to look back

        Returns:
            Combined BatchTweetAnalysis
        """
        print(f"\n=== {self.AGENT_NAME}: Scanning priority accounts ===")

        all_analyses = []
        all_arxiv_ids = []
        errors = []

        for username, level in self.PRIORITY_ACCOUNTS.items():
            try:
                result = self.scan_account(username, days)
                all_analyses.extend(result.analyses)
                all_arxiv_ids.extend(result.unique_arxiv_ids)
                errors.extend(result.errors)
            except Exception as e:
                errors.append(f"@{username}: {str(e)}")

        unique_arxiv = list(dict.fromkeys(all_arxiv_ids))
        total_papers = sum(len(a.papers) for a in all_analyses)

        print("\n=== Summary ===")
        print(f"  Accounts scanned: {len(self.PRIORITY_ACCOUNTS)}")
        print(f"  Total papers: {total_papers}")
        print(f"  Unique arXiv IDs: {len(unique_arxiv)}")

        return BatchTweetAnalysis(
            analyses=all_analyses,
            total_papers=total_papers,
            total_arxiv_ids=len(all_arxiv_ids),
            unique_arxiv_ids=unique_arxiv,
            errors=errors,
        )

    def get_arxiv_papers(self, result: BatchTweetAnalysis) -> List[str]:
        """
        Get list of arXiv IDs to feed into academic pipeline.

        Args:
            result: BatchTweetAnalysis from scanning

        Returns:
            List of arXiv IDs for ScannerAgent
        """
        return result.unique_arxiv_ids


# CLI entry point
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scan X/Twitter for ML papers")
    parser.add_argument("--account", "-a", help="Single account to scan")
    parser.add_argument("--priority", "-p", action="store_true", help="Scan all priority accounts")
    parser.add_argument("--days", "-d", type=int, default=1, help="Days to look back")
    parser.add_argument("--output", "-o", help="Output JSON file")
    args = parser.parse_args()

    agent = XAgent()

    if args.account:
        result = agent.scan_account(args.account, args.days)
    elif args.priority:
        result = agent.scan_priority_accounts(args.days)
    else:
        print("Specify --account or --priority")
        exit(1)

    if args.output:
        with open(args.output, 'w') as f:
            json.dump({
                'analyses': [a.__dict__ for a in result.analyses],
                'unique_arxiv_ids': result.unique_arxiv_ids,
                'total_papers': result.total_papers,
            }, f, indent=2, default=str)
        print(f"\nSaved to {args.output}")

    print("\n=== arXiv IDs for Pipeline ===")
    for arxiv_id in result.unique_arxiv_ids[:10]:
        print(f"  {arxiv_id}")
