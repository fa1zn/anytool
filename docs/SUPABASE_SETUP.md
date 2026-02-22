# Supabase setup for Anytool

Follow these steps to attach Supabase so Anytool stores each request/response.

---

## 1. Get your project URL and API key

1. Go to [Supabase Dashboard](https://supabase.com/dashboard) and open your project.
2. In the left sidebar click **Project Settings** (gear icon).
3. Open **API** in the left menu.
4. Copy:
   - **Project URL** → use as `SUPABASE_URL`
   - **Project API keys** → use the **`service_role`** key (under "Project API keys") as `SUPABASE_SERVICE_KEY`  
     ⚠️ Keep this secret; it bypasses Row Level Security. Do not commit it or expose it in the frontend.

---

## 2. Create the table

1. In the dashboard left sidebar click **SQL Editor**.
2. Click **New query**.
3. Paste and run this SQL:

```sql
create table if not exists anytool_records (
  id uuid default gen_random_uuid() primary key,
  created_at timestamptz default now(),
  repo_url text not null,
  prompt text not null,
  diff text not null
);
```

4. Click **Run** (or Cmd+Enter). You should see "Success. No rows returned."

---

## 3. Wire it to the app

**Local:**

1. In the project root, copy the example env if you haven’t already:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and add (use your real values):
   ```
   SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
   SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9....
   ```
3. Restart the app. Every successful `/generate-diff` call will insert a row into `anytool_records`.

**Deployed (Railway / Render / Fly.io etc.):**

Add the same two variables in the host’s **Environment** / **Env vars** section. Redeploy so the new env is picked up.

---

## 4. Check that it works

- In Supabase: **Table Editor** → open `anytool_records`. After a few `/generate-diff` requests you should see new rows with `repo_url`, `prompt`, `diff`, and `created_at`.
- If the table is empty, confirm `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` are set and the app was restarted (or redeployed) after adding them.
