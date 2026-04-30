import os
from typing import List, Dict
import httpx
from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
TAVILY_ENDPOINT = "https://api.tavily.com/search"


async def tavily_search(query: str, count: int = 5) -> List[Dict]:
    if not TAVILY_API_KEY:
        raise ValueError("TAVILY_API_KEY not set")

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "max_results": count,
        "search_depth": "advanced",
        "include_answer": False,
    }

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(TAVILY_ENDPOINT, json=payload)
        response.raise_for_status()
        data = response.json()

    results = []
    for item in data.get("results", []):
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "description": item.get("content", ""),
            "extra_snippets": [],
        })
    return results
