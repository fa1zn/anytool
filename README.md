# Anytool

**An API that turns a GitHub repo and a sentence into a unified diff.** You send a repo URL and a natural-language instruction (e.g. “use `dir` on Windows instead of `ls`”, “convert this to TypeScript”); you get back a diff you can apply with `git apply` or feed into any tool that speaks unified diffs. Built with a two-step LLM pipeline: generate the diff, then reflect and optionally correct before returning.

---

## What I built

- A **single API**: `POST /generate-diff` with `repoUrl` and `prompt` → returns `{ "diff": "..." }`.
- **Two LLM steps**: (1) Generate a unified diff from the repo contents + your prompt. (2) **Reflection** — the model reviews its own diff and can output a corrected version; the API returns that final result.
- **Repo context** from the GitHub API (no local clone). Optional **Supabase** storage for inputs/outputs. Deployable (e.g. Railway, Render).

So: **instruction in, diff out.** No UI — you call the API from the terminal, from `/docs`, or from another app.

---

## What it solves

**“I know what change I want; I don’t want to hunt for the right file and the right line.”**

You have a repo and a clear intent: “fix Windows support”, “switch to TypeScript”, “add error handling here”. Doing it by hand means opening files, searching, editing, and hoping you didn’t miss a spot. Anytool takes the **intent** and the **repo** and gives you a **concrete diff** — the same format every version-control tool understands. You (or your tooling) can review it, apply it, and iterate. It’s a building block for “describe the change, get the patch.”

---

## Why that problem is a headache

- **Scattered context:** Repos have many files; one logical change often touches several. Figuring out *where* to edit is tedious and error-prone.
- **Repetition:** Similar changes across files (e.g. “use this pattern everywhere”) are boring and easy to get wrong when done manually.
- **Intent vs. implementation:** You know *what* you want; translating that into exact edits is the friction. One wrong line can break the build or the behavior.
- **Tooling expects diffs:** Review flows, CI, and automation work in diffs. Getting from “I want X” to a proper diff usually means doing the edits yourself first. Anytool short-circuits that: you describe X, you get the diff.

---

## Public API

When deployed, you can hit the API at:

- **Base URL:** `https://<your-deployment-url>` (e.g. Railway, Render, or Fly.io)
- **Health:** `GET /health`
- **Generate diff:** `POST /generate-diff`

### Example request

```bash
curl -X POST "https://<YOUR_PUBLIC_URL>/generate-diff" \
  -H "Content-Type: application/json" \
  -d '{
    "repoUrl": "https://github.com/jayhack/llm.sh",
    "prompt": "The program does not output anything on Windows 10. Make it detect OS/shell and use the appropriate command (e.g. dir on Windows instead of ls)."
  }'
```

### Example response

```json
{
  "diff": "diff --git a/src/main.py b/src/main.py\nindex 58d38b6..23b0827 100644\n--- a/src/main.py\n+++ b/src/main.py\n..."
}
```

Use the `diff` string with `git apply` or any tool that accepts unified diffs.

---

## Running on your machine (macOS)

Assume Python 3.11+ and a shell (zsh/bash).

### 1. Clone and enter the repo

```bash
git clone <this-repo-url>
cd anytool
```

### 2. Create a virtualenv and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Set environment variables

Copy the example env and add your OpenAI key:

```bash
cp .env.example .env
```

Edit `.env` and set:

- `OPENAI_API_KEY=sk-...` (required for the LLM steps)

Optional (bonus: store inputs/outputs in Supabase):

- `SUPABASE_URL=https://xxx.supabase.co`
- `SUPABASE_SERVICE_KEY=eyJ...`

### 4. Run the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: **http://localhost:8000**
- Docs: **http://localhost:8000/docs**

### 5. Try it locally

```bash
curl -X POST "http://localhost:8000/generate-diff" \
  -H "Content-Type: application/json" \
  -d '{"repoUrl": "https://github.com/jayhack/llm.sh", "prompt": "Use dir on Windows instead of ls and detect OS."}'
```

---

## Bonus: Supabase storage

If `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` are set, each request/response is stored in Supabase.

Create a table (e.g. in SQL Editor):

```sql
create table if not exists anytool_records (
  id uuid default gen_random_uuid() primary key,
  created_at timestamptz default now(),
  repo_url text not null,
  prompt text not null,
  diff text not null
);

-- Optional: enable RLS and add a policy if you use anon key
-- alter table anytool_records enable row level security;
```

---

## Project layout

- `app/main.py` — FastAPI app and `POST /generate-diff` endpoint
- `app/models.py` — Request/response schemas (`repoUrl`, `prompt` → `diff`)
- `app/config.py` — Settings from env (OpenAI, optional Supabase)
- `app/services/repo.py` — Fetches public GitHub repo contents via GitHub API
- `app/services/llm.py` — Two LLM steps: generate diff, then reflect (and optionally correct)
- `app/services/storage.py` — Optional Supabase write for inputs/outputs

---

## Deploying so it’s “live on the web”

You can deploy this app to any host that runs Python and sets `OPENAI_API_KEY`:

- **Railway:** Connect repo, set env vars, run `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Render:** New Web Service, same run command, add env vars
- **Fly.io:** Use a `Dockerfile` or `fly.toml` with a Python runtime and the same uvicorn command

Replace `<YOUR_PUBLIC_URL>` in the “Public API” section above with the URL your host gives you.

---

## Design notes

- **Two LLM steps:** (1) Generate a unified diff from repo + prompt. (2) Reflection: the model reviews the diff and either confirms (CORRECT) or outputs a corrected diff (CORRECTED + new diff). The API returns the final diff after reflection.
- **Repo context:** Repo contents are fetched via GitHub’s API (no local git clone). Only text/code files under a size limit are included; common binary and dependency dirs are skipped.
- **Small repos:** The implementation assumes relatively small repos so that context fits in the model. For larger repos you could add chunking, file selection by relevance, or multi-step edits.
