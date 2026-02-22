"""Request/response models for the API."""
from pydantic import BaseModel, Field


class GenerateDiffRequest(BaseModel):
    """POST body for the generate-diff endpoint."""

    model_config = {"populate_by_name": True}

    repo_url: str = Field(..., alias="repoUrl", description="GitHub repo URL")
    prompt: str


class GenerateDiffResponse(BaseModel):
    """Response containing the unified diff."""

    diff: str
