import os
from typing import AsyncGenerator
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()

client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

WRITER_SYSTEM = """You are an expert research analyst producing comprehensive, well-structured research reports.

Your reports must follow this structure:
1. **Executive Summary** — 2–3 sentence overview of the key answer
2. **Key Findings** — bullet-point list of the most important facts discovered
3. **Detailed Analysis** — in-depth discussion organized by theme or sub-topic
4. **Conclusion** — synthesized takeaway and implications
5. **Sources** — numbered list matching inline citations

Formatting rules:
- Use Markdown (headers, bold, bullet lists)
- Cite sources inline as [1], [2], etc., matching the source numbers in the provided research data
- Be analytical, not just descriptive — draw connections and highlight tensions between sources
- Maintain an objective, encyclopedic tone
- Aim for 600–1000 words of substantive content"""


async def write_report(
    question: str, research_data: list[dict]
) -> AsyncGenerator[str, None]:
    source_list = []
    findings_parts = []
    source_idx = 1

    for item in research_data:
        findings_parts.append(f"### Research strand: {item['query']}\n{item['findings']}")
        for src in item["sources"]:
            source_list.append(f"[{source_idx}] {src['title']} — {src['url']}")
            source_idx += 1

    context = (
        f"Research question: {question}\n\n"
        + "\n\n".join(findings_parts)
        + "\n\n---\nAvailable sources for citation:\n"
        + "\n".join(source_list)
    )

    stream = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=4000,
        stream=True,
        messages=[
            {"role": "system", "content": WRITER_SYSTEM},
            {"role": "user", "content": context},
        ],
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
