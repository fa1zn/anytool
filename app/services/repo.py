"""Fetch public GitHub repo contents via GitHub API."""
import re
from dataclasses import dataclass
from typing import Optional

import httpx

GITHUB_API = "https://api.github.com"
MAX_FILE_BYTES = 100_000  # Skip files larger than this for context
TEXT_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".rb",
    ".php", ".c", ".h", ".cpp", ".hpp", ".cs", ".swift", ".kt", ".scala",
    ".sh", ".bash", ".zsh", ".yaml", ".yml", ".json", ".toml", ".ini",
    ".md", ".txt", ".html", ".css", ".scss", ".vue", ".svelte", ".rkt",
    ".r", ".sql", ".graphql", ".proto", ".mdx", ".env",
}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}


@dataclass
class RepoContext:
    """Fetched repo metadata and file contents for LLM context."""

    owner: str
    repo: str
    default_branch: str
    files: list[tuple[str, str]]  # (path, content)


def parse_github_url(repo_url: str) -> Optional[tuple[str, str]]:
    """Extract (owner, repo) from a GitHub URL. Returns None if invalid."""
    repo_url = repo_url.strip().rstrip("/")
    # https://github.com/owner/repo or git@github.com:owner/repo.git
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?$", repo_url, re.I)
    if m:
        return (m.group(1), m.group(2).removesuffix(".git"))
    m = re.match(r"git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$", repo_url)
    if m:
        return (m.group(1), m.group(2).removesuffix(".git"))
    return None


def _skip_path(path: str) -> bool:
    parts = path.split("/")
    if any(p in SKIP_DIRS for p in parts):
        return True
    return False


def _is_likely_text(path: str) -> bool:
    if "." not in path.split("/")[-1]:
        return True  # no extension, include (e.g. Dockerfile, Makefile)
    ext = "." + path.split(".")[-1].lower()
    return ext in TEXT_EXTENSIONS


async def fetch_repo_context(repo_url: str) -> RepoContext:
    """
    Fetch a public GitHub repo's file tree and contents.
    Raises ValueError for invalid URL or API errors.
    """
    parsed = parse_github_url(repo_url)
    if not parsed:
        raise ValueError(f"Invalid GitHub repo URL: {repo_url}")

    owner, repo = parsed

    async with httpx.AsyncClient(
        headers={"Accept": "application/vnd.github.v3+json"},
        timeout=30.0,
    ) as client:
        # Get default branch
        r = await client.get(f"{GITHUB_API}/repos/{owner}/{repo}")
        r.raise_for_status()
        data = r.json()
        default_branch = data.get("default_branch", "main")

        # Get tree recursively
        r = await client.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/{default_branch}",
            params={"recursive": "1"},
        )
        r.raise_for_status()
        tree = r.json()
        entries = tree.get("tree", [])

        # Collect blob SHAs for text files
        blobs = [
            (e["path"], e["sha"])
            for e in entries
            if e.get("type") == "blob"
            and not _skip_path(e["path"])
            and _is_likely_text(e["path"])
        ]

        files: list[tuple[str, str]] = []
        for path, sha in blobs:
            r = await client.get(f"{GITHUB_API}/repos/{owner}/{repo}/git/blobs/{sha}")
            r.raise_for_status()
            blob = r.json()
            if blob.get("encoding") != "base64":
                continue
            import base64
            raw = base64.b64decode(blob["content"])
            if len(raw) > MAX_FILE_BYTES:
                continue
            try:
                content = raw.decode("utf-8", errors="replace")
            except Exception:
                continue
            files.append((path, content))

    return RepoContext(
        owner=owner,
        repo=repo,
        default_branch=default_branch,
        files=files,
    )


def format_repo_context_for_prompt(ctx: RepoContext) -> str:
    """Format repo files as a single string for the LLM prompt."""
    lines = [f"# Repo: {ctx.owner}/{ctx.repo} (branch: {ctx.default_branch})\n"]
    for path, content in ctx.files:
        lines.append(f"\n## File: {path}\n```\n{content}\n```")
    return "\n".join(lines)
