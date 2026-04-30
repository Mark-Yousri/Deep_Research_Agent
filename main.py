import os
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv

from agents.orchestrator import run_research

load_dotenv()

app = FastAPI(title="Deep Research Agent")
app.mount("/static", StaticFiles(directory="static"), name="static")


class ResearchRequest(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def question_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Question cannot be empty")
        return v


@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.post("/research")
async def research(req: ResearchRequest):
    return StreamingResponse(
        run_research(req.question),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
