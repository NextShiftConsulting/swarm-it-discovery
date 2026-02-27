"""
Paper Sources - Fetch papers from arXiv, Semantic Scholar, etc.
"""

import os
import httpx
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional
from abc import ABC, abstractmethod


@dataclass
class Paper:
    """Represents a discovered paper."""
    id: str
    title: str
    abstract: str
    authors: List[str]
    source: str  # arxiv, semantic_scholar, etc.
    url: str
    pdf_url: Optional[str]
    published_date: str
    categories: List[str]


class PaperSource(ABC):
    """Abstract base for paper sources."""

    @abstractmethod
    async def fetch_recent(self, days: int = 1, max_results: int = 100) -> List[Paper]:
        """Fetch papers from the last N days."""
        pass


class ArxivSource(PaperSource):
    """Fetch papers from arXiv API."""

    BASE_URL = "https://export.arxiv.org/api/query"

    # Categories relevant to our research
    CATEGORIES = [
        "cs.AI",      # Artificial Intelligence
        "cs.LG",      # Machine Learning
        "cs.CL",      # Computation and Language
        "cs.MA",      # Multiagent Systems
        "stat.ML",    # Machine Learning (stats)
    ]

    async def fetch_recent(self, days: int = 1, max_results: int = 100) -> List[Paper]:
        """Fetch recent papers from arXiv."""
        import xml.etree.ElementTree as ET

        # Build category query
        cat_query = " OR ".join(f"cat:{cat}" for cat in self.CATEGORIES)

        params = {
            "search_query": f"({cat_query})",
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": max_results,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()

        # Parse Atom feed
        root = ET.fromstring(response.text)
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

        papers = []
        cutoff = datetime.utcnow() - timedelta(days=days)

        for entry in root.findall("atom:entry", ns):
            published = entry.find("atom:published", ns).text
            pub_date = datetime.fromisoformat(published.replace("Z", "+00:00"))

            if pub_date.replace(tzinfo=None) < cutoff:
                continue

            arxiv_id = entry.find("atom:id", ns).text.split("/abs/")[-1]

            papers.append(Paper(
                id=f"arxiv:{arxiv_id}",
                title=entry.find("atom:title", ns).text.strip().replace("\n", " "),
                abstract=entry.find("atom:summary", ns).text.strip(),
                authors=[a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)],
                source="arxiv",
                url=f"https://arxiv.org/abs/{arxiv_id}",
                pdf_url=f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                published_date=published[:10],
                categories=[c.get("term") for c in entry.findall("arxiv:primary_category", ns)] or [],
            ))

        return papers


class SemanticScholarSource(PaperSource):
    """Fetch papers from Semantic Scholar API."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    FIELDS_OF_STUDY = [
        "Computer Science",
        "Artificial Intelligence",
        "Machine Learning",
    ]

    async def fetch_recent(self, days: int = 1, max_results: int = 100) -> List[Paper]:
        """Fetch recent papers from Semantic Scholar."""
        api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        headers = {"x-api-key": api_key} if api_key else {}

        # Search for recent AI/ML papers
        params = {
            "query": "machine learning OR artificial intelligence OR neural network",
            "fields": "paperId,title,abstract,authors,url,publicationDate,fieldsOfStudy,openAccessPdf",
            "limit": max_results,
            "publicationDateOrYear": f"{datetime.utcnow().year}",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/paper/search",
                params=params,
                headers=headers,
                timeout=30,
            )

            if response.status_code == 429:
                print("Semantic Scholar rate limited")
                return []

            response.raise_for_status()

        data = response.json()
        papers = []
        cutoff = datetime.utcnow() - timedelta(days=days)

        for item in data.get("data", []):
            if not item.get("abstract"):
                continue

            pub_date = item.get("publicationDate")
            if pub_date:
                try:
                    if datetime.fromisoformat(pub_date) < cutoff:
                        continue
                except:
                    pass

            pdf_info = item.get("openAccessPdf") or {}

            papers.append(Paper(
                id=f"s2:{item['paperId']}",
                title=item["title"],
                abstract=item["abstract"],
                authors=[a.get("name", "") for a in item.get("authors", [])],
                source="semantic_scholar",
                url=item.get("url", f"https://www.semanticscholar.org/paper/{item['paperId']}"),
                pdf_url=pdf_info.get("url"),
                published_date=pub_date or "",
                categories=item.get("fieldsOfStudy") or [],
            ))

        return papers


class OpenAlexSource(PaperSource):
    """Fetch papers from OpenAlex API (free, comprehensive)."""

    BASE_URL = "https://api.openalex.org"

    # Concept IDs for AI/ML topics
    CONCEPTS = [
        "C154945302",  # Machine Learning
        "C119857082",  # Artificial Intelligence
        "C108583219",  # Deep Learning
        "C50644808",   # Neural Network
    ]

    async def fetch_recent(self, days: int = 1, max_results: int = 100) -> List[Paper]:
        """Fetch recent AI/ML papers from OpenAlex."""
        from_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

        params = {
            "filter": f"concepts.id:{'|'.join(self.CONCEPTS)},from_publication_date:{from_date}",
            "sort": "publication_date:desc",
            "per_page": min(max_results, 200),
            "select": "id,title,abstract_inverted_index,authorships,primary_location,publication_date,concepts",
        }

        # Add polite email for better rate limits
        email = os.getenv("OPENALEX_EMAIL", "research@swarms.network")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/works",
                params=params,
                headers={"User-Agent": f"SwarmIt/1.0 (mailto:{email})"},
                timeout=30,
            )

            if response.status_code != 200:
                print(f"OpenAlex error: {response.status_code}")
                return []

        data = response.json()
        papers = []

        for item in data.get("results", []):
            # Reconstruct abstract from inverted index
            abstract = ""
            if item.get("abstract_inverted_index"):
                words = {}
                for word, positions in item["abstract_inverted_index"].items():
                    for pos in positions:
                        words[pos] = word
                abstract = " ".join(words[i] for i in sorted(words.keys()))

            if not abstract:
                continue

            # Get primary URL/PDF
            location = item.get("primary_location") or {}
            source_info = location.get("source") or {}

            papers.append(Paper(
                id=f"openalex:{item['id'].split('/')[-1]}",
                title=item.get("title", ""),
                abstract=abstract,
                authors=[a.get("author", {}).get("display_name", "") for a in item.get("authorships", [])[:10]],
                source="openalex",
                url=item.get("id", ""),
                pdf_url=location.get("pdf_url"),
                published_date=item.get("publication_date", ""),
                categories=[c.get("display_name", "") for c in item.get("concepts", [])[:5]],
            ))

        return papers


class BioRxivSource(PaperSource):
    """Fetch preprints from bioRxiv/medRxiv."""

    BASE_URL = "https://api.biorxiv.org/details"

    async def fetch_recent(self, days: int = 1, max_results: int = 100, server: str = "biorxiv") -> List[Paper]:
        """Fetch recent preprints from bioRxiv or medRxiv."""
        from_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        to_date = datetime.utcnow().strftime("%Y-%m-%d")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/{server}/{from_date}/{to_date}/0/{max_results}",
                timeout=30,
            )

            if response.status_code != 200:
                print(f"{server} error: {response.status_code}")
                return []

        data = response.json()
        papers = []

        for item in data.get("collection", []):
            # Filter for AI/ML/computational topics
            category = item.get("category", "").lower()
            title_lower = item.get("title", "").lower()

            relevant_terms = ["machine learning", "neural", "deep learning", "ai",
                            "computational", "algorithm", "model", "prediction"]
            if not any(t in category or t in title_lower for t in relevant_terms):
                continue

            papers.append(Paper(
                id=f"{server}:{item.get('doi', '').split('/')[-1]}",
                title=item.get("title", ""),
                abstract=item.get("abstract", ""),
                authors=item.get("authors", "").split("; ")[:10],
                source=server,
                url=f"https://www.{server}.org/content/{item.get('doi')}",
                pdf_url=f"https://www.{server}.org/content/{item.get('doi')}.full.pdf",
                published_date=item.get("date", ""),
                categories=[item.get("category", "")],
            ))

        return papers


class MedRxivSource(BioRxivSource):
    """Fetch preprints from medRxiv."""

    async def fetch_recent(self, days: int = 1, max_results: int = 100) -> List[Paper]:
        return await super().fetch_recent(days, max_results, server="medrxiv")


class PubMedSource(PaperSource):
    """Fetch papers from PubMed/NCBI."""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    async def fetch_recent(self, days: int = 1, max_results: int = 100) -> List[Paper]:
        """Fetch recent AI/ML papers from PubMed."""
        # Search for AI/ML papers
        query = "(machine learning[Title/Abstract] OR artificial intelligence[Title/Abstract] OR deep learning[Title/Abstract] OR neural network[Title/Abstract])"

        async with httpx.AsyncClient() as client:
            # Step 1: Search for IDs
            search_response = await client.get(
                f"{self.BASE_URL}/esearch.fcgi",
                params={
                    "db": "pubmed",
                    "term": query,
                    "retmax": max_results,
                    "reldate": days,
                    "datetype": "edat",
                    "retmode": "json",
                },
                timeout=30,
            )

            if search_response.status_code != 200:
                print(f"PubMed search error: {search_response.status_code}")
                return []

            search_data = search_response.json()
            ids = search_data.get("esearchresult", {}).get("idlist", [])

            if not ids:
                return []

            # Step 2: Fetch details
            fetch_response = await client.get(
                f"{self.BASE_URL}/efetch.fcgi",
                params={
                    "db": "pubmed",
                    "id": ",".join(ids),
                    "retmode": "xml",
                },
                timeout=30,
            )

            if fetch_response.status_code != 200:
                print(f"PubMed fetch error: {fetch_response.status_code}")
                return []

        # Parse XML
        import xml.etree.ElementTree as ET
        root = ET.fromstring(fetch_response.text)
        papers = []

        for article in root.findall(".//PubmedArticle"):
            try:
                medline = article.find(".//MedlineCitation")
                pmid = medline.find("PMID").text
                art = medline.find("Article")

                title = art.find("ArticleTitle").text or ""

                abstract_elem = art.find(".//AbstractText")
                abstract = abstract_elem.text if abstract_elem is not None else ""

                if not abstract:
                    continue

                authors = []
                for author in art.findall(".//Author"):
                    last = author.find("LastName")
                    first = author.find("ForeName")
                    if last is not None:
                        name = last.text
                        if first is not None:
                            name = f"{first.text} {name}"
                        authors.append(name)

                pub_date = ""
                date_elem = art.find(".//PubDate")
                if date_elem is not None:
                    year = date_elem.find("Year")
                    month = date_elem.find("Month")
                    if year is not None:
                        pub_date = year.text
                        if month is not None:
                            pub_date = f"{year.text}-{month.text}"

                papers.append(Paper(
                    id=f"pubmed:{pmid}",
                    title=title,
                    abstract=abstract,
                    authors=authors[:10],
                    source="pubmed",
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    pdf_url=None,  # PubMed doesn't provide direct PDF links
                    published_date=pub_date,
                    categories=["Life Sciences"],
                ))
            except Exception as e:
                continue

        return papers


async def fetch_all_sources(days: int = 1, max_per_source: int = 50) -> List[Paper]:
    """Fetch papers from all configured sources."""
    import asyncio

    sources = [
        ArxivSource(),
        SemanticScholarSource(),
        OpenAlexSource(),
        BioRxivSource(),
        MedRxivSource(),
        PubMedSource(),
    ]

    results = await asyncio.gather(
        *[s.fetch_recent(days=days, max_results=max_per_source) for s in sources],
        return_exceptions=True,
    )

    papers = []
    for result in results:
        if isinstance(result, Exception):
            print(f"Source error: {result}")
        else:
            papers.extend(result)

    # Deduplicate by title similarity
    seen_titles = set()
    unique = []
    for p in papers:
        title_key = p.title.lower()[:50]
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique.append(p)

    return unique
