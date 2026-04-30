import os
import asyncio
import re
from groq import AsyncGroq, RateLimitError
from dotenv import load_dotenv
from tools.tavily_search import tavily_search

load_dotenv()

client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

EXTRACTOR_SYSTEM = """You are a research assistant. Given a search query and raw search results, extract the most relevant facts and insights.

Write a concise paragraph (100–200 words) summarizing the key findings relevant to the query. Focus on facts, data, and expert opinions. Avoid filler phrases."""


def _parse_retry_seconds(error_message: str) -> float:
    match = re.search(r"try again in ([\d.]+)s", error_message)
    return float(match.group(1)) + 1.0 if match else 30.0


async def search_and_extract(query: str) -> dict:
    results = await tavily_search(query, count=5)

    if not results:
        return {"query": query, "findings": "No results found.", "sources": []}

    snippets = []
    sources = []
    for i, r in enumerate(results, 1):
        snippets.append(f"[{i}] {r['title']}\n{r['description']}")
        sources.append({"title": r["title"], "url": r["url"]})

    context = f"Query: {query}\n\nSearch results:\n" + "\n\n".join(snippets)

    for attempt in range(3):
        try:
            response = await client.chat.completions.create(
                model="llama-3.1-8b-instant",
                max_tokens=300,
                messages=[
                    {"role": "system", "content": EXTRACTOR_SYSTEM},
                    {"role": "user", "content": context},
                ],
            )
            findings = response.choices[0].message.content.strip()
            return {"query": query, "findings": findings, "sources": sources}

        except RateLimitError as e:
            if attempt == 2:
                raise
            wait = _parse_retry_seconds(str(e))
            await asyncio.sleep(wait)
