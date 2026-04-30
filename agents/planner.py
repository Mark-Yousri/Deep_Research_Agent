import os
import json
import re
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()

client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

PLANNER_SYSTEM = """You are a research planning expert. Given a complex research question, break it down into 3–5 focused web search queries that together will provide comprehensive coverage of the topic.

Rules:
- Each query should target a different angle or sub-topic
- Queries should be specific enough to return useful results
- Use concise, keyword-rich phrasing (as you would type into a search engine)
- Do NOT repeat the same concept in multiple queries
- Cover: background/definition, current state, key debates, recent developments, and expert perspectives where relevant

Respond ONLY with a valid JSON array of strings. No markdown, no explanation.
Example: ["query one", "query two", "query three"]"""


async def plan_queries(question: str) -> list[str]:
    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=400,
        messages=[
            {"role": "system", "content": PLANNER_SYSTEM},
            {"role": "user", "content": f"Research question: {question}"},
        ],
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    queries = json.loads(raw)
    if not isinstance(queries, list):
        raise ValueError("Planner did not return a list")
    return [str(q) for q in queries[:5]]
