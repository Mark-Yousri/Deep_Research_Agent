import asyncio
import json
from typing import AsyncGenerator

from agents.guardrail import check_guardrail
from agents.planner import plan_queries
from agents.searcher import search_and_extract
from agents.writer import write_report


def _sse(event_type: str, content) -> str:
    payload = json.dumps({"type": event_type, "content": content})
    return f"data: {payload}\n\n"


async def run_research(question: str) -> AsyncGenerator[str, None]:
    # 1. Guardrail check
    yield _sse("status", "Checking query safety...")
    try:
        guard = await check_guardrail(question)
    except Exception as e:
        yield _sse("error", f"Guardrail error: {e}")
        return

    if not guard.get("allowed"):
        yield _sse("error", f"Query blocked: {guard.get('reason', 'Policy violation')}")
        return

    yield _sse("status", "Query approved. Planning research...")

    # 2. Planning
    try:
        queries = await plan_queries(question)
    except Exception as e:
        yield _sse("error", f"Planning error: {e}")
        return

    yield _sse("queries", queries)
    yield _sse("status", f"Launching {len(queries)} parallel searches...")

    # 3. Parallel searches — staggered 2s apart to stay within free-tier TPM limits
    research_data = []
    task_list = []
    for i, q in enumerate(queries):
        if i > 0:
            await asyncio.sleep(2)
        task_list.append(asyncio.create_task(search_and_extract(q)))
    tasks = {t: q for t, q in zip(task_list, queries)}

    for coro in asyncio.as_completed(list(tasks.keys())):
        try:
            result = await coro
            research_data.append(result)
            yield _sse("search_complete", {
                "query": result["query"],
                "source_count": len(result["sources"]),
            })
        except Exception as e:
            # Record partial failure but continue
            yield _sse("search_complete", {"query": "unknown", "error": str(e)})

    if not research_data:
        yield _sse("error", "All searches failed. Please try again.")
        return

    yield _sse("status", f"Searches complete. Synthesizing report from {len(research_data)} strands...")
    yield _sse("report_start", "")

    # 4. Write report (streaming)
    try:
        async for chunk in write_report(question, research_data):
            yield _sse("report_chunk", chunk)
    except Exception as e:
        yield _sse("error", f"Report generation error: {e}")
        return

    yield _sse("done", "Research complete.")
