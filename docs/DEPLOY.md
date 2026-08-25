# Deploying वार्तालाप — free public demo

A live demo needs two hosts. Both are **truly free forever, with no credit
card required at signup**:

| Component | Host | Free tier | URL shape |
| --- | --- | --- | --- |
| **Backend** (FastAPI + RAG) | [Render — Free Web Service](https://render.com) | 512 MB RAM, 0.1 CPU, sleeps after 15 min idle | `https://<service>.onrender.com` |
| **Frontend** (Next.js) | [Vercel — Hobby](https://vercel.com) | Free forever, no card | `https://<project>.vercel.app` |

> Everything else we looked at — Fly.io, Hugging Face Docker / Gradio SDK,
> Railway, Modal.com — has moved the truly-free tier behind a payment
> method for new accounts. Render is currently the exception and stays
> genuinely free.

## Why this fits Render Free

Render Free is capped at 512 MB RAM. Our runtime steady-state is now
**~150 MB** because:

- Chunk embeddings are **pre-computed and shipped in the repo**
  ([`backend/data/chroma/vartalaap_kb.npy`](../backend/data/chroma/README.md)).
- Query embeddings hit the free **Hugging Face Inference API**
  (~1 outbound call per chat turn, ~1000 req/day allowance).
- `sentence-transformers`, `FlagEmbedding` and `torch` are removed from
  `requirements.txt`. If HF is temporarily unreachable the pipeline falls
  through to a deterministic hash embedder so requests never 500.

Peak RAM during a chat turn is ~250 MB, well inside the 512 MB envelope.

---

## 1. Backend → Render Free

### 1.1 Create the Render account (2 min)

1. Go to <https://render.com/register>.
2. Sign up with **GitHub** — no credit card is asked for.

### 1.2 Get a Hugging Face inference token (2 min, free)

Query embeddings use HF's free inference API.

1. Sign up at <https://huggingface.co/join> (free, no card).
2. Go to <https://huggingface.co/settings/tokens>.
3. **New token** → name it `vartalaap`, **Role: Read**, click *Create*.
4. Copy the `hf_...` token — you'll paste it into Render in a moment.

### 1.3 Create the web service (3 min)

1. Render dashboard → **New → Web Service**.
2. **Connect a repository** → pick `XENO2410/ADI` (authorise if prompted).
3. Fill in:
   - **Name**: `vartalaap-api` (public URL will be `https://vartalaap-api.onrender.com`).
   - **Region**: closest to you.
   - **Branch**: `main`.
   - **Root Directory**: `backend`.
   - **Runtime**: **Python 3**.
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: **Free**.
4. Scroll to **Environment Variables** and add:
   - `OPENROUTER_API_KEY` = `sk-or-v1-...`
   - `HF_INFERENCE_TOKEN` = `hf_...` (from 1.2)
   - `LLM_MODEL` = `openai/gpt-4o-mini`
   - `RERANKER_ENABLED` = `false`
   - `MLFLOW_ENABLED` = `true`
   - `CORS_ORIGINS` = `https://placeholder.vercel.app` *(updated in step 2.2)*
5. Click **Create Web Service**.

Render builds and deploys. First build takes ~4-6 min (installing numpy,
mlflow etc.). Follow the **Logs** tab.

### 1.4 Verify

Once you see `Uvicorn running on http://0.0.0.0:10000` in the logs and the
service is green:

```bash
curl https://vartalaap-api.onrender.com/health
# → {"status":"ok","llm_configured":true,...}
```

Note the URL — Vercel needs it next.

### 1.5 Free-tier caveats

- **Sleeps after 15 min of inactivity.** First request after sleep takes
  ~30-60 s to wake up (Render shows a spinner in the browser).
- **Ephemeral filesystem** — MLflow runs stored on the instance are wiped
  on each redeploy / restart. See §3 if you need a persistent MLflow UI.
- **750 instance-hours / month** across all your free services. One
  service always-on = 720 h/month, well within budget.

---

## 2. Frontend → Vercel

### 2.1 Import the repo (3 min)

1. Sign in at <https://vercel.com> — GitHub SSO, no card.
2. **Add New → Project → Import Git Repository** → `XENO2410/ADI`.
3. **Root Directory** = `frontend`.
4. **Framework** = Next.js (auto-detected).
5. **Environment Variables**:
   - Name: `NEXT_PUBLIC_API_BASE_URL`
   - Value: `https://vartalaap-api.onrender.com` (from step 1.4)
   - Environments: **Production**, **Preview**, **Development** (all three).
6. Click **Deploy**.

### 2.2 Point the backend's CORS at the new URL

Render → your service → **Environment** → edit `CORS_ORIGINS`:

```env
https://<project>.vercel.app,https://<project>-*.vercel.app
```

Render restarts the service automatically. Visit your Vercel URL — chat
should work end-to-end.

### 2.3 Optional — custom domain

Vercel → Project → Settings → Domains → add yours. Update Render's
`CORS_ORIGINS` to include it.

---

## 3. Optional — hosted MLflow UI

MLflow tracks locally inside the Render instance's ephemeral filesystem, so
runs / traces are wiped on redeploy. Two ways around it, both free:

### 3a. View via the local docker-compose stack

The simplest path — nothing to deploy. From the repo root:

```bash
docker compose up --build
```

Backend runs at `http://localhost:8000`, MLflow UI at `http://localhost:5000`,
frontend at `http://localhost:3000`. This is the full experience; use it
whenever you want to inspect traces / eval metrics / cost roll-ups.

### 3b. Point MLflow at a free cloud store

For persistent hosted MLflow:

- **Backend store**: Neon.tech PostgreSQL (0.5 GB free, no card).
- **Artifact store**: Cloudflare R2 (10 GB egress-free, no card).

Set on Render → Environment:

```env
MLFLOW_TRACKING_URI=postgresql://user:pass@neon-host/vartalaap
MLFLOW_ARTIFACT_ROOT=s3://vartalaap-mlflow/
AWS_ACCESS_KEY_ID=<r2-access-key>
AWS_SECRET_ACCESS_KEY=<r2-secret>
MLFLOW_S3_ENDPOINT_URL=https://<account>.r2.cloudflarestorage.com
```

Then run a second Render Free web service (Python) with:

- Build: `pip install "mlflow>=2.15,<3.0" psycopg2-binary boto3`
- Start: `mlflow ui --backend-store-uri "$MLFLOW_TRACKING_URI" --default-artifact-root "$MLFLOW_ARTIFACT_ROOT" --host 0.0.0.0 --port $PORT`
- Same env vars as above.

Both services now share the same MLflow store.

Skip this unless the demo is going public — locally-run `mlflow ui`
against the docker-compose volume covers 95 % of use cases.

---

## 4. Cutting a release

Container images are built and pushed to GHCR on any `v*.*.*` tag by
[.github/workflows/release.yml](../.github/workflows/release.yml):

```bash
git tag -a v1.0.0 -m "First public release"
git push origin v1.0.0
```

That publishes `ghcr.io/xeno2410/vartalaap-backend:v1.0.0` (+ `:latest`)
and `ghcr.io/xeno2410/vartalaap-frontend:v1.0.0` (+ `:latest`), then drafts
a GitHub Release using [docs/RELEASE_NOTES_v1.0.0.md](RELEASE_NOTES_v1.0.0.md).

> **One-time gotcha:** Repo → Settings → Actions → General → **Workflow
> permissions** must be set to **Read and write permissions** for the
> release workflow to publish to GHCR.

---

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Render build fails on `pip install` | Almost always memory pressure — comment out the `# --- Optional (developer-only) ---` block in `requirements.txt` if you enabled it. |
| `500` from `/chat` on Render | Almost always missing `OPENROUTER_API_KEY` env var. Also check `HF_INFERENCE_TOKEN` — the query embedding call will fail without it and fall back to hash embeddings (retrieval quality drops noticeably). |
| CORS error in the browser | `CORS_ORIGINS` on Render must exactly match your Vercel URL (no trailing slash). Include the preview wildcard `https://<project>-*.vercel.app` too. |
| First request after 15 min is very slow | Render Free sleeps aggressively. The wake takes ~30-60 s. Consider Render Starter ($7/mo) if you need always-on for a live demo. |
| `Falling back to hash pseudo-embeddings` warning in logs | `HF_INFERENCE_TOKEN` is missing / invalid. Retrieval quality drops to keyword-only matches. |
| `data/chroma/vartalaap_kb.npy not found` on first boot | The pre-computed KB isn't in the repo. Locally: `pip install sentence-transformers && python -m scripts.seed_kb --reset`, then commit the two files under `backend/data/chroma/`. |
| Vercel build fails on missing env var | Add `NEXT_PUBLIC_API_BASE_URL` to **all three** environments (Prod, Preview, Dev). |
