import os
import logging
from app.AI_agents.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class WebSearchTool(BaseTool):
    """
    Web search tool with Tavily as primary and DuckDuckGo as fallback.
    
    Tavily requires TAVILY_API_KEY in environment.
    Fallback uses DuckDuckGo Instant Answer API (no key needed).
    """
    name = "web_search_tool"
    description = "Search the web for up-to-date information on topics outside BabyCare AI's knowledge base."

    def _search_tavily(self, query: str, max_results: int = 3) -> list[dict]:
        """Primary: Tavily Search API."""
        from tavily import TavilyClient
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY not set in environment.")
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query,
            search_depth="basic",
            max_results=max_results,
            include_answer=True,
        )
        results = []
        # Include Tavily's AI-generated answer if available
        if response.get("answer"):
            results.append({
                "title": "Tổng hợp từ Tavily AI",
                "snippet": response["answer"],
                "url": "",
                "source": "tavily_answer",
            })
        for r in response.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "snippet": r.get("content", ""),
                "url": r.get("url", ""),
                "source": "tavily",
            })
        return results

    def _search_duckduckgo(self, query: str, max_results: int = 3) -> list[dict]:
        """Fallback: DuckDuckGo Instant Answer API (free, no key required)."""
        import urllib.request
        import urllib.parse
        import json
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
        req = urllib.request.Request(url, headers={"User-Agent": "BabyCareAI/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        results = []
        # Abstract (best answer)
        if data.get("AbstractText"):
            results.append({
                "title": data.get("Heading", "Kết quả"),
                "snippet": data["AbstractText"],
                "url": data.get("AbstractURL", ""),
                "source": "duckduckgo_abstract",
            })
        # Related topics
        for topic in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append({
                    "title": topic.get("Text", "")[:80],
                    "snippet": topic.get("Text", ""),
                    "url": topic.get("FirstURL", ""),
                    "source": "duckduckgo",
                })
        if not results:
            results.append({
                "title": "Không tìm thấy kết quả cụ thể",
                "snippet": f"Không có kết quả tức thì cho '{query}'. Hãy thử tìm kiếm trực tiếp trên Google hoặc trang web chuyên ngành.",
                "url": f"https://www.google.com/search?q={encoded_query}",
                "source": "duckduckgo_fallback",
            })
        return results[:max_results]

    def _run(self, query: str, max_results: int = 3) -> dict:
        """
        Run web search: Tavily primary → DuckDuckGo fallback.
        Returns: {"query": str, "results": list[dict], "provider": str}
        """
        # Try Tavily first
        try:
            results = self._search_tavily(query, max_results=max_results)
            logger.info(f"[WebSearch] Tavily success for query: '{query}' ({len(results)} results)")
            return {"query": query, "results": results, "provider": "tavily"}
        except Exception as e:
            logger.warning(f"[WebSearch] Tavily failed: {e}. Falling back to DuckDuckGo.")

        # Fallback: DuckDuckGo
        try:
            results = self._search_duckduckgo(query, max_results=max_results)
            logger.info(f"[WebSearch] DuckDuckGo fallback for query: '{query}' ({len(results)} results)")
            return {"query": query, "results": results, "provider": "duckduckgo"}
        except Exception as e:
            logger.error(f"[WebSearch] Both providers failed: {e}")
            return {
                "query": query,
                "results": [{
                    "title": "Lỗi tìm kiếm",
                    "snippet": f"Không thể thực hiện tìm kiếm web lúc này. Vui lòng thử lại sau.",
                    "url": "",
                    "source": "error",
                }],
                "provider": "none",
            }
