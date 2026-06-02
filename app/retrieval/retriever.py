from dataclasses import dataclass
from html import unescape
import json
import re
from urllib.parse import urlencode
from urllib.request import urlopen
from typing import Any, Dict, List, Optional, Tuple

from app.retrieval.search import search


_TRUST_SCORES = {
    "official_filing": 0.9,
    "official_ir": 0.85,
    "regulator_gov": 0.9,
    "reputable_news": 0.65,
    "unknown_blog": 0.35,
    "external_web": 0.4,
}


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
            url = item.get("url", "")
            trust_tier, trust_score = self._web_trust_tier(url)
            final_score = score + (trust_score * 0.1)
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
                    "filename": url or "web_result",
                    "company": request.company or "web",
                    "year": request.year or 0,
                    "source_type": "web",
                    "upload_time": "",
                    "trust_tier": trust_tier,
                    "path": url,
                    "source_bucket": "web",
                    "score": score,
                    "final_score": final_score,
                    "trust_score": trust_score,
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
            local = self.retrieve_local(request)
            for row in local.get("results", []):
                row["source_bucket"] = "local"
            return local
        if request.source == "web":
            return self.retrieve_web(request)

        local = self.retrieve_local(request)
        local_rows = local.get("results", [])
        for row in local_rows:
            row["source_bucket"] = "local"

        if not self._needs_web_fallback(local_rows, request):
            return local

        web = self.retrieve_web(request)
        web_rows = web.get("results", [])
        merged = self._merge_results(local_rows, web_rows, request.final_k)

        return {
            "source": "hybrid",
            "query": local.get("query", request.question),
            "rewritten_query": local.get("rewritten_query", request.question),
            "local_results": local_rows,
            "web_results": web_rows,
            "results": merged,
            "note": "Hybrid retrieval used local evidence with web fallback.",
        }

    def _needs_web_fallback(self, local_rows: List[Dict[str, Any]], request: RetrievalRequest) -> bool:
        if not local_rows:
            return True

        min_rows = max(3, int(request.final_k / 2))
        if len(local_rows) < min_rows:
            return True

        scores: List[float] = []
        for row in local_rows:
            try:
                scores.append(float(row.get("final_score", row.get("score", 0.0))))
            except (TypeError, ValueError):
                scores.append(0.0)
        avg_score = sum(scores) / max(len(scores), 1)
        return avg_score < 0.32

    def _merge_results(
        self,
        local_rows: List[Dict[str, Any]],
        web_rows: List[Dict[str, Any]],
        final_k: int,
    ) -> List[Dict[str, Any]]:
        merged = local_rows + web_rows
        merged.sort(key=lambda row: row.get("final_score", row.get("score", 0.0)), reverse=True)
        return merged[:final_k]

    def _web_trust_tier(self, url: str) -> Tuple[str, float]:
        host = url.lower()
        if "sec.gov" in host or "sec-report" in host or "sec" in host and "edgar" in host:
            return "official_filing", _TRUST_SCORES["official_filing"]
        if host.endswith(".gov") or ".gov/" in host:
            return "regulator_gov", _TRUST_SCORES["regulator_gov"]

        reputable = (
            "reuters.com",
            "bloomberg.com",
            "wsj.com",
            "ft.com",
            "cnbc.com",
            "marketwatch.com",
            "finance.yahoo.com",
        )
        if any(domain in host for domain in reputable):
            return "reputable_news", _TRUST_SCORES["reputable_news"]

        if not host:
            return "unknown_blog", _TRUST_SCORES["unknown_blog"]
        return "unknown_blog", _TRUST_SCORES["unknown_blog"]
