"""Optional Supabase storage for request/response records."""
from typing import Optional

from supabase import create_client, Client


def get_supabase_client(url: str, key: str) -> Optional[Client]:
    """Return a Supabase client if URL and key are set; otherwise None."""
    if not url or not key:
        return None
    return create_client(url, key)


async def store_record(
    client: Optional[Client],
    repo_url: str,
    prompt: str,
    diff: str,
) -> None:
    """Store one generate-diff request/response in Supabase. No-op if client is None."""
    if client is None:
        return
    table = "anytool_records"
    try:
        client.table(table).insert({
            "repo_url": repo_url,
            "prompt": prompt,
            "diff": diff,
        }).execute()
    except Exception:
        # Best-effort; don't fail the request if DB is misconfigured
        pass
