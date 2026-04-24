from dataclasses import dataclass
from html import unescape
import json
import re
from urllib.parse import urlencode
from urllib.request import urlopen
from typing import Any, Dict, List, Optional

from app.retrieval.search import search


@dataclass
class RetrievalRequest:
    question: str
    company: Optional[str] = None
    year: Optional[int] = None
    source_type: Optional[str] = None
    top_k: int = 12
    final_k: int = 8
    source: str = "auto"  # auto | local | web


class Retriever:
    def rewrite_question(self, question: str) -> str:
        text = question.strip()
        replacements = {
            "10k": "10-K annual report",
            "10-k": "10-K annual report",
            "qoq": "quarter-over-quarter",
            "yoy": "year-over-year",
            "md&a": "management discussion and analysis",
        }
        lowered = text.lower()
        for key, value in replacements.items():
            if key in lowered:
                lowered = lowered.replace(key, value)
        return lowered

    def retrieve_local(self, request: RetrievalRequest) -> Dict[str, Any]:
        rewritten = self.rewrite_question(request.question)
        rows = search(
            query=rewritten,
            company=request.company,
            year=request.year,
            source_type=request.source_type,
            top_k=request.top_k,
            final_k=request.final_k,
        )
        return {
            "source": "local",
            "query": request.question,
            "rewritten_query": rewritten,
            "results": rows,
        }

    def retrieve_web(self, request: RetrievalRequest) -> Dict[str, Any]:
        rewritten = self.rewrite_question(request.question)
        query = rewritten
        if request.company:
            query = f"{request.company} investor relations {rewritten}"

        raw_results = self._duckduckgo_search(query=query, max_results=request.final_k)
        web_rows: List[Dict[str, Any]] = []
        for idx, item in enumerate(raw_results):
            score = max(0.0, 1.0 - (idx * 0.08))
            web_rows.append(
                {
                    "vector_id": -1,
                    "chunk_id": f"web_{idx}",
                    "document_id": f"web_doc_{idx}",
                    "chunk_index": idx,
                    "page_number": 0,
                    "section_title": item.get("title", "web_result"),
                    "text": item.get("snippet", ""),
                    "token_count": len(item.get("snippet", "").split()),
                    "embedding_model": "web-none",
                    "embedding_dim": 0,
                    "filename": item.get("url", "web_result"),
                    "company": request.company or "web",
                    "year": request.year or 0,
                    "source_type": "web",
                    "upload_time": "",
                    "trust_tier": "external_web",
                    "path": item.get("url", ""),
                    "score": score,
                    "final_score": score,
                }
            )

        return {
            "source": "web",
            "query": request.question,
            "rewritten_query": rewritten,
            "results": web_rows,
            "note": "Web retrieval used DuckDuckGo Instant Answer API.",
        }

    def _duckduckgo_search(self, query: str, max_results: int = 8) -> List[Dict[str, str]]:
        params = urlencode(
            {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1",
            }
        )
        url = f"https://api.duckduckgo.com/?{params}"

        try:
            with urlopen(url, timeout=12) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            payload = {}

        results: List[Dict[str, str]] = []

        abstract_text = payload.get("AbstractText", "").strip()
        abstract_url = payload.get("AbstractURL", "").strip()
        heading = payload.get("Heading", "").strip() or "DuckDuckGo"
        if abstract_text:
            results.append(
                {
                    "title": heading,
                    "url": abstract_url or "https://duckduckgo.com",
                    "snippet": abstract_text,
                }
            )

        def add_topic(topic: Dict[str, Any]) -> None:
            text = str(topic.get("Text", "")).strip()
            first_url = str(topic.get("FirstURL", "")).strip()
            if text:
                results.append(
                    {
                        "title": text[:80],
                        "url": first_url or "https://duckduckgo.com",
                        "snippet": text,
                    }
                )

        for topic in payload.get("RelatedTopics", []):
            nested = topic.get("Topics")
            if isinstance(nested, list):
                for child in nested:
                    add_topic(child)
            else:
                add_topic(topic)

        if not results:
            results.extend(self._duckduckgo_html_fallback(query=query, max_results=max_results))

        if not results:
            results.extend(self._bing_rss_fallback(query=query, max_results=max_results))

        if not results:
            results.append(
                {
                    "title": "No web results",
                    "url": "https://duckduckgo.com",
                    "snippet": "No results were returned from the web search API for this query.",
                }
            )

        return results[:max_results]

    def _duckduckgo_html_fallback(self, query: str, max_results: int) -> List[Dict[str, str]]:
        params = urlencode({"q": query})
        url = f"https://html.duckduckgo.com/html/?{params}"

        try:
            with urlopen(url, timeout=12) as response:
                html = response.read().decode("utf-8", errors="ignore")
        except Exception:
            return []

        anchors = re.findall(
            r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )

        results: List[Dict[str, str]] = []
        for href, title_html in anchors[:max_results]:
            title_text = re.sub(r"<.*?>", "", title_html)
            title_text = unescape(title_text).strip()
            results.append(
                {
                    "title": title_text or "Web result",
                    "url": unescape(href).strip(),
                    "snippet": title_text or "Web result",
                }
            )

        return results

    def _bing_rss_fallback(self, query: str, max_results: int) -> List[Dict[str, str]]:
        params = urlencode({"q": query, "format": "rss"})
        url = f"https://www.bing.com/search?{params}"

        try:
            with urlopen(url, timeout=12) as response:
                xml = response.read().decode("utf-8", errors="ignore")
        except Exception:
            return []

        items = re.findall(r"<item>(.*?)</item>", xml, flags=re.IGNORECASE | re.DOTALL)
        results: List[Dict[str, str]] = []

        for item in items[:max_results]:
            title_match = re.search(r"<title>(.*?)</title>", item, flags=re.IGNORECASE | re.DOTALL)
            link_match = re.search(r"<link>(.*?)</link>", item, flags=re.IGNORECASE | re.DOTALL)
            desc_match = re.search(r"<description>(.*?)</description>", item, flags=re.IGNORECASE | re.DOTALL)

            title = unescape(title_match.group(1).strip()) if title_match else "Web result"
            link = unescape(link_match.group(1).strip()) if link_match else "https://www.bing.com"
            desc = unescape(desc_match.group(1).strip()) if desc_match else title

            results.append(
                {
                    "title": title,
                    "url": link,
                    "snippet": re.sub(r"<.*?>", "", desc),
                }
            )

        return results

    def retrieve(self, request: RetrievalRequest) -> Dict[str, Any]:
        if request.source == "local":
            return self.retrieve_local(request)
        if request.source == "web":
            return self.retrieve_web(request)

        local = self.retrieve_local(request)
        if local["results"]:
            return local
        return self.retrieve_web(request)
