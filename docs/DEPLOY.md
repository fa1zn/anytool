# Deploy Anytool

## Option 1: Railway (recommended, ~5 min)

1. **Sign up / log in**  
   Go to [railway.app](https://railway.app) and sign in with GitHub.

2. **New project from repo**  
   - Click **“New Project”**.  
   - Choose **“Deploy from GitHub repo”**.  
   - Select **fa1zn/anytool** (authorize Railway if asked).  
   - Railway will detect the `Dockerfile` and start a build.

3. **Set environment variables**  
   - Open your new service (the Anytool deployment).  
   - Go to **Variables** (or **Settings** → **Variables**).  
   - Add:
     - `OPENAI_API_KEY` = your OpenAI API key (required).  
     - `SUPABASE_URL` = `https://esluownlxizfamxdtgaw.supabase.co` (optional).  
     - `SUPABASE_SERVICE_KEY` = your Supabase service_role key (optional).  
   - Save. Railway will redeploy if needed.

4. **Get the public URL**  
   - In the service, open **Settings** → **Networking** (or **Generate domain**).  
   - Click **Generate domain** (or use the default).  
   - Copy the URL, e.g. `https://anytool-production-xxxx.up.railway.app`.

5. **Test**  
   ```bash
   curl https://YOUR-RAILWAY-URL/health
   curl -X POST "https://YOUR-RAILWAY-URL/generate-diff" \
     -H "Content-Type: application/json" \
     -d '{"repoUrl":"https://github.com/jayhack/llm.sh","prompt":"Use dir on Windows."}'
   ```

6. **Update README**  
   In the repo, edit **README.md** and replace `<YOUR_PUBLIC_URL>` (or the placeholder) with your Railway URL. Commit and push.

---

## Option 2: Render

1. Go to [render.com](https://render.com) and sign in with GitHub.

2. **New → Web Service** → connect **fa1zn/anytool**.

3. **Build & deploy**  
   - **Environment:** Docker (Render will use your `Dockerfile`).  
   - **Instance type:** Free or paid.

4. **Environment variables** (in the Render dashboard):  
   - `OPENAI_API_KEY` = your key.  
   - `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` = optional.

5. **Deploy** → copy the URL (e.g. `https://anytool-xxxx.onrender.com`).

6. Put that URL in the README “Public API” section and push.

---

## Notes

- **PORT:** Railway and Render set `PORT` automatically; the Dockerfile uses it.
- **Cold starts:** On free tiers the first request after idle can be slow; retry if needed.
- **Secrets:** Never commit `.env`. Set all keys in the platform’s Variables/Env vars.
