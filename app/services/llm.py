"""LLM service: generate diff and run reflection (two-step workflow)."""
from openai import AsyncOpenAI

from app.services.repo import RepoContext, format_repo_context_for_prompt

SYSTEM_GENERATE = """You are a code assistant that produces unified diffs. Given a GitHub repo's file contents and a user prompt, you must output ONLY a valid unified diff (e.g. starting with "diff --git ...") that implements the requested change. Do not output any explanation, markdown, or text before or after the diff. Output the complete diff only."""

SYSTEM_REFLECT = """You are a reviewer. You will see: (1) the user's original request, (2) a unified diff that was generated to fulfill it. Your job is to decide if the diff is correct and complete, or if it should be corrected.

If the diff is correct and fully addresses the request, respond with exactly: CORRECT

If the diff has mistakes, is incomplete, or does not match the request, respond with: CORRECTED
Then on the next lines, output a replacement unified diff that fixes the issues. Output only CORRECT or CORRECTED followed by the new diff when applicable. No other text."""


async def generate_diff(
    client: AsyncOpenAI,
    repo_context: RepoContext,
    prompt: str,
    reflection_feedback: str | None = None,
) -> str:
    """
    First LLM step: produce a unified diff from repo context and user prompt.
    If reflection_feedback is set, the model is asked to incorporate the correction.
    """
    repo_text = format_repo_context_for_prompt(repo_context)
    user_content = f"""Repo contents:\n{repo_text}\n\nUser request:\n{prompt}"""
    if reflection_feedback:
        user_content += f"\n\nReflection/correction request:\n{reflection_feedback}"

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_GENERATE},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
    )
    text = response.choices[0].message.content or ""
    return _extract_diff_from_response(text)


async def reflect_on_diff(
    client: AsyncOpenAI,
    prompt: str,
    diff: str,
) -> tuple[bool, str]:
    """
    Second LLM step: reflection. Ask the model if the diff is correct or if it
    wants to correct it. Returns (is_correct, corrected_diff_or_empty).
    If is_correct is True, corrected_diff is empty. If False, corrected_diff
    is the new diff to use.
    """
    user_content = f"""User request:\n{prompt}\n\nGenerated diff:\n{diff}"""

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_REFLECT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.1,
    )
    text = (response.choices[0].message.content or "").strip()

    if text.upper().startswith("CORRECT"):
        # Check if it's "CORRECT" only (no correction) or "CORRECTED" + new diff
        rest = text[7:].strip()  # after "CORRECT" or "CORRECTED"
        if text.upper().startswith("CORRECTED") and rest:
            new_diff = _extract_diff_from_response(rest)
            return (False, new_diff)
        return (True, "")

    # Unclear response: treat as correct and keep original
    return (True, "")


def _extract_diff_from_response(text: str) -> str:
    """Extract a unified diff from model output (handle markdown code blocks)."""
    text = text.strip()
    if "```" in text:
        start = text.find("```")
        if start != -1:
            rest = text[start + 3:]
            if rest.startswith("diff"):
                end = rest.find("```")
                return rest[:end].strip() if end != -1 else rest.strip()
            # try after first ```
            next_start = rest.find("```")
            if next_start != -1:
                block = rest[next_start + 3:].split("```")[0]
                if "diff --git" in block:
                    return block.strip()
    if "diff --git" in text:
        start = text.index("diff --git")
        return text[start:].strip()
    return text
