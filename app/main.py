"""FastAPI app: POST endpoint that returns a unified diff for a repo + prompt."""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.config import get_settings
from app.models import GenerateDiffRequest, GenerateDiffResponse
from app.services.repo import fetch_repo_context
from app.services.llm import generate_diff, reflect_on_diff
from app.services.storage import get_supabase_client, store_record

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure OpenAI key is present at startup when handling requests
    yield
    # no cleanup needed


app = FastAPI(
    title="Anytool",
    description="Generate a unified diff for a public GitHub repo given a code prompt (with reflection).",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate-diff", response_model=GenerateDiffResponse)
async def generate_diff_endpoint(body: GenerateDiffRequest):
    """
    Accepts a public GitHub repo URL and a prompt; returns a unified diff
    that implements the requested change. Uses a two-step LLM workflow:
    (1) generate diff, (2) reflection — if the model wants to correct, it returns a new diff.
    """
    settings = get_settings()
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not configured",
        )

    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    # 1) Fetch repo context
    try:
        repo_ctx = await fetch_repo_context(body.repo_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch repo: {e!s}",
        )

    if not repo_ctx.files:
        raise HTTPException(
            status_code=400,
            detail="Repo has no text files we could load (or URL invalid).",
        )

    # 2) First LLM step: generate diff
    diff = await generate_diff(client, repo_ctx, body.prompt)

    # 3) Second LLM step: reflection
    is_correct, corrected_diff = await reflect_on_diff(client, body.prompt, diff)
    if not is_correct and corrected_diff:
        diff = corrected_diff

    # 4) Optional: store in Supabase
    supabase = get_supabase_client(settings.supabase_url, settings.supabase_service_key)
    await store_record(supabase, body.repo_url, body.prompt, diff)

    return GenerateDiffResponse(diff=diff)
