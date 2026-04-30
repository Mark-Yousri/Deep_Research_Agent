import os
from typing import List, Dict
import httpx
from dotenv import load_dotenv

load_dotenv()

BRAVE_API_KEY = os.getenv("BRAVE_SEARCH_API_KEY")
BRAVE_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"


async def brave_search(query: str, count: int = 5) -> List[Dict]:
    if not BRAVE_API_KEY:
        raise ValueError("BRAVE_SEARCH_API_KEY not set")

    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": BRAVE_API_KEY,
    }
    params = {"q": query, "count": count, "text_decorations": False}

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(BRAVE_ENDPOINT, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

    results = []
    for item in data.get("web", {}).get("results", []):
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "description": item.get("description", ""),
            "extra_snippets": item.get("extra_snippets", []),
        })
    return results
