# Deploying वार्तालाप — free public demo

A live demo needs two hosts. Both are truly free and neither asks for a
credit card up front:

| Component | Host | Free tier | URL shape |
| --- | --- | --- | --- |
| **Backend** (FastAPI + RAG) | [Hugging Face Spaces — Docker](https://huggingface.co/new-space) | 16 GB RAM, 2 vCPU, sleeps after ~48 h idle | `https://<owner>-<space>.hf.space` |
| **Frontend** (Next.js) | [Vercel — Hobby](https://vercel.com) | Free forever, no card | `https://<project>.vercel.app` |

MLflow UI in the public demo is optional and self-hosted — see §3 at the
bottom.

> **Why not Fly.io / Render / Railway?** They now require a payment method
> before you can deploy anything, even on their free tiers. Hugging Face
> Spaces + Vercel remain no-card.

---

## 1. Backend → Hugging Face Spaces

### 1.1 Create the Space (2 min, web UI)

1. Go to <https://huggingface.co/new-space>. Sign up if you don't have an
   account — no credit card needed.
2. Fill in:
   - **Owner** — your username or an org you own.
   - **Space name** — e.g. `vartalaap-api`.
   - **License** — MIT.
   - **Space SDK** — **Docker**. **Template** — **Blank**.
   - **Hardware** — **CPU basic — 2 vCPU · 16 GB — FREE**.
   - **Visibility** — Public (so the frontend can call it).
3. Click **Create Space**. HF gives you an empty Space with its own git repo.

### 1.2 Push `backend/` to the Space (5 min)

The Space needs the backend Dockerfile at its **root**. We use `git subtree`
to push our `backend/` subfolder onto the Space's `main` branch.

Create a write-scoped HF token first: <https://huggingface.co/settings/tokens>
→ **New token** → **Write** scope.

Then from the repo root:

**PowerShell (Windows)**:

```powershell
$env:HF_TOKEN = "hf_..."
.\scripts\push-hf-space.ps1 -SpaceOwner <your-hf-username> -SpaceName vartalaap-api
```

**Bash (macOS / Linux / WSL)**:

```bash
export HF_TOKEN=hf_...
./scripts/push-hf-space.sh <your-hf-username> vartalaap-api
```

The script:

1. Adds a temporary git remote (`hf-vartalaap-api`) that includes your token.
2. Runs `git subtree push --prefix=backend hf-vartalaap-api main` — the
   `backend/` folder becomes the Space's root.
3. Prints a cleanup command to remove the tokenized remote.

The Space now builds the image (~5-10 min on first push, then cached).
Watch progress on the Space's **Logs** tab.

### 1.3 Set the runtime secrets (1 min)

On the Space page → **Settings → Repository secrets → Add secret**:

| Name | Value |
| --- | --- |
| `OPENROUTER_API_KEY` | your OpenRouter key |
| `CORS_ORIGINS` | `https://<placeholder>.vercel.app` (updated after Vercel) |
| `RERANKER_ENABLED` | `false` (saves ~280 MB download on first boot) |

HF injects them as environment variables at container start — you don't
need to redeploy after adding them.

### 1.4 Verify

```bash
curl https://<owner>-vartalaap-api.hf.space/health
```

You should see `{"status":"ok", …}`. Take a note of that URL — Vercel needs
it next.

### 1.5 Redeploying on updates

Every time you change files under `backend/` on your GitHub `main`, re-run
the same script. `git subtree push` is incremental and only pushes new
commits.

Optional: automate it with a GitHub Action — sample
[`.github/workflows/hf-space-sync.yml`](../.github/workflows) is left as an
exercise (uses `huggingface_hub` CLI + `HF_TOKEN` secret).

---

## 2. Frontend → Vercel

### 2.1 Import the repo (3 min)

1. Sign in at <https://vercel.com> — GitHub SSO, no card.
2. **Add New → Project → Import Git Repository** → pick `XENO2410/ADI`.
3. **Root Directory** = `frontend`.
4. **Framework** = Next.js (auto-detected).
5. **Environment Variables** — click **Add**:
   - Name: `NEXT_PUBLIC_API_BASE_URL`
   - Value: `https://<owner>-vartalaap-api.hf.space` (from step 1.4)
   - Environments: **Production**, **Preview**, **Development** (all three).
6. Click **Deploy**.

The build takes ~90 seconds. Once green, click the URL — you should see
वार्तालाप ready to chat.

### 2.2 Point the backend's CORS at the new URL

Back on the HF Space → Settings → Repository secrets → edit `CORS_ORIGINS`:

```env
https://<project>.vercel.app,https://<project>-*.vercel.app
```

The wildcard covers preview deploys. HF restarts the container automatically.

### 2.3 Custom domain (optional)

Vercel → Project → Settings → Domains → add yours. Update the backend's
`CORS_ORIGINS` to include it.

---

## 3. Optional — hosted MLflow UI

MLflow tracks locally inside the Space's ephemeral filesystem, which HF
wipes when the machine sleeps. Public MLflow needs a persistent store.
Two options that stay free:

### 3a. View live via `huggingface_hub` port-forward (dev-only)

```bash
huggingface-cli spaces run \
  --owner <you> --space vartalaap-api -- \
  mlflow ui --backend-store-uri /app/mlruns --host 0.0.0.0 --port 5000
```

Then open a tunnel with `hf-space-proxy` or just `curl` against the Space.
Fine for admin inspection, not for the public.

### 3b. Push to a shared cloud store (recommended for a real demo)

Point MLflow at a cloud DB + object store — all free tiers, no card:

- **Backend store**: Neon.tech PostgreSQL (0.5 GB free, no card).
- **Artifact store**: Cloudflare R2 (10 GB free, no card).

Set on the HF Space:

```env
MLFLOW_TRACKING_URI=postgresql://user:pass@neon-host/vartalaap
MLFLOW_ARTIFACT_ROOT=s3://vartalaap-mlflow/
AWS_ACCESS_KEY_ID=<r2-access-key>
AWS_SECRET_ACCESS_KEY=<r2-secret>
MLFLOW_S3_ENDPOINT_URL=https://<account>.r2.cloudflarestorage.com
```

Then run a second HF Space with just `mlflow ui` pointed at the same
`MLFLOW_TRACKING_URI` / `MLFLOW_ARTIFACT_ROOT`. Both Spaces share state.

Skip this if the demo is only for a handful of viewers — locally-run
`mlflow ui` against the docker-compose volume is a much simpler win.

---

## 4. Cutting a release

Container images are built and pushed to GHCR by
[.github/workflows/release.yml](../.github/workflows/release.yml) on any
`v*.*.*` tag:

```bash
git tag -a v1.0.0 -m "First public release"
git push origin v1.0.0
```

That publishes `ghcr.io/xeno2410/vartalaap-backend:v1.0.0` (+ `:latest`)
and `ghcr.io/xeno2410/vartalaap-frontend:v1.0.0` (+ `:latest`), then drafts
a GitHub Release using [docs/RELEASE_NOTES_v1.0.0.md](RELEASE_NOTES_v1.0.0.md).

Anyone can then run:

```bash
docker run -e OPENROUTER_API_KEY=... -p 8000:8000 \
  ghcr.io/xeno2410/vartalaap-backend:latest
```

> **One-time gotcha:** Repo → Settings → Actions → General → **Workflow
> permissions** must be set to **Read and write permissions** for the
> release workflow to publish to GHCR.

---

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Space stuck on "Building" > 15 min | Check the Logs tab — usually `pip install` OOM. Cut `FlagEmbedding` from `requirements.txt` and set `RERANKER_ENABLED=false`. |
| `500` from `/chat` on HF | Almost always missing `OPENROUTER_API_KEY` in Space secrets. Re-check Settings → Repository secrets. |
| CORS error in the browser | `CORS_ORIGINS` must exactly match your Vercel URL (no trailing slash). Include the preview wildcard. |
| Space sleeps and cold start is slow | HF free tier idles after ~48 h. First request wakes it in ~30 s. Upgrade to CPU-upgrade (~$0.05/h) if you need snappy warm starts. |
| First run is slow | Sentence-transformers downloads its 90 MB model on first boot. Subsequent restarts reuse `/root/.cache/huggingface`. |
| `git subtree push` rejects with non-fast-forward | Someone edited the Space's `main` branch directly. Force it with `git push hf-<name> --force $(git subtree split --prefix=backend main):main`. |
| Vercel build fails on missing env var | Add `NEXT_PUBLIC_API_BASE_URL` to **all three** environments (Prod, Preview, Dev). |
