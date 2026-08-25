# Deploying वार्तालाप

A live public demo needs two hosts:

| Component | Recommended host | Cost | Cold start |
| --- | --- | --- | --- |
| **Frontend** (Next.js) | [Vercel](https://vercel.com) — Hobby | Free | ~200 ms |
| **Backend** (FastAPI) | [Fly.io](https://fly.io) — free tier | Free (auto-stop) | ~5 s |
| **MLflow UI** | Local for now (see notes at the bottom) | — | — |

The whole thing takes ~20 minutes end-to-end the first time. Instructions below
assume the repo is already on GitHub (it is — [XENO2410/ADI](https://github.com/XENO2410/ADI)).

---

## 1. Backend → Fly.io

### Fly prereqs

- Install `flyctl`: <https://fly.io/docs/hands-on/install-flyctl/>
- `flyctl auth signup` (or `login`).
- A working OpenRouter key.

### Fly deploy

```bash
cd backend
flyctl launch --copy-config --no-deploy       # picks up the existing fly.toml
```

`launch` will ask for:

- **App name** — pick something unique like `vartalaap-<yourhandle>`. Update the
  `app = "..."` line in `fly.toml` to match.
- **Region** — pick closest to you and your users; e.g. `iad`, `sin`, `bom`, `fra`.
- **Postgres / Redis** — say **no** to both.
- **Deploy now?** — say **no**; we need to create a volume first.

Create the persistent volume that will hold `mlruns/`, `chroma/`, `logs/`:

```bash
flyctl volumes create vartalaap_data --size 3 --region <same-region-as-above>
```

Set the runtime secrets:

```bash
flyctl secrets set \
  OPENROUTER_API_KEY=sk-or-v1-... \
  CORS_ORIGINS=https://<your-frontend>.vercel.app
```

Deploy:

```bash
flyctl deploy
```

The first deploy pushes ~2 GB of image (torch + sentence-transformers) and
takes 5–10 min. Subsequent deploys are incremental.

Once done, `flyctl status` shows the public URL — typically
`https://<app-name>.fly.dev`. Verify:

```bash
curl https://<app-name>.fly.dev/health
```

Take note of that URL — it goes into Vercel next.

### Free-tier tips

- `auto_stop_machines = "stop"` + `min_machines_running = 0` (already set in
  `fly.toml`) means the VM sleeps after ~5 min idle and wakes on the next
  request. Cold wake ≈ 5–10 s.
- If you want the demo always-warm, set `min_machines_running = 1` (costs a
  couple of dollars a month).

---

## 2. Frontend → Vercel

### Vercel prereqs

- Free account at <https://vercel.com>.
- `npm i -g vercel` (optional — the web UI works too).

### One-time setup

The `frontend/vercel.json` uses a shared env var `@vartalaap_api_url`. Set it
first so both preview and production builds pick it up:

```bash
vercel env add vartalaap_api_url production
# When prompted, paste: https://<your-fly-app>.fly.dev
```

(Or set it via the Vercel UI: Project → Settings → Environment Variables →
add `NEXT_PUBLIC_API_BASE_URL` = `https://<your-fly-app>.fly.dev` for
Production, Preview and Development.)

### Vercel deploy

Either link and deploy from CLI:

```bash
cd frontend
vercel link
vercel --prod
```

…or point Vercel at the GitHub repo (recommended):

1. New Project → **Import Git Repository** → pick `XENO2410/ADI`.
2. **Root Directory** = `frontend`.
3. **Framework** = Next.js (auto-detected).
4. **Environment Variables** → add `NEXT_PUBLIC_API_BASE_URL` =
   `https://<your-fly-app>.fly.dev` for all environments.
5. Deploy. Every push to `main` now redeploys automatically.

Once live, come back to Fly and update `CORS_ORIGINS`:

```bash
flyctl secrets set CORS_ORIGINS=https://<vercel-project>.vercel.app,https://<vercel-project>-*.vercel.app
```

Refresh the Vercel URL — you should see वार्तालाप ready to chat.

---

## 3. Optional — hosted MLflow UI

Getting the MLflow UI publicly reachable requires a shared store because
Fly volumes are per-app. Two workable approaches:

### 3a. Simple: view via `flyctl ssh`

```bash
flyctl ssh console
mlflow ui --backend-store-uri /data/mlruns --host 0.0.0.0 --port 5000
```

Then locally:

```bash
flyctl proxy 5000:5000 -a <your-fly-app>
open http://localhost:5000
```

Zero extra services. Fine for admin-only inspection.

### 3b. Proper: SQLite + object store

Point MLflow at a SQLite DB for the backend store and an S3-compatible object
store for artifacts:

```bash
flyctl secrets set \
  MLFLOW_TRACKING_URI=sqlite:////data/mlflow.db \
  MLFLOW_ARTIFACT_ROOT=s3://<bucket>/mlflow \
  AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... \
  MLFLOW_S3_ENDPOINT_URL=https://<your-r2-endpoint>
```

Then deploy a second tiny Fly app running `mlflow ui` with the same env
vars — both apps point at the same SQLite (from the volume) and S3.
Cloudflare R2 free tier (10 GB egress-free) works well here.

Skip this if the demo is only for a handful of viewers — `3a` is enough.

---

## 4. Cutting a release

Container images are built automatically by
[.github/workflows/release.yml](../.github/workflows/release.yml) whenever
you push a tag matching `v*.*.*`.

```bash
git tag -a v1.0.0 -m "First public release"
git push origin v1.0.0
```

The workflow builds `ghcr.io/xeno2410/vartalaap-backend:v1.0.0` and
`ghcr.io/xeno2410/vartalaap-frontend:v1.0.0`, tags them `:latest` too, and
opens a draft GitHub Release with the notes from
[`docs/RELEASE_NOTES_v1.0.0.md`](RELEASE_NOTES_v1.0.0.md).

Go to **Releases** → the draft → click **Publish**.

Anyone can then run:

```bash
docker run -e OPENROUTER_API_KEY=... -p 8000:8000 ghcr.io/xeno2410/vartalaap-backend:latest
```

---

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `500` from `/chat` on Fly | `flyctl logs` → almost always missing `OPENROUTER_API_KEY` secret. |
| CORS error in the browser | Set `CORS_ORIGINS` on Fly to your exact Vercel URL (no trailing slash). |
| Long cold starts | Bump `min_machines_running` to `1` in `fly.toml`. |
| First deploy fails on OOM | Raise the VM to `4gb` in `[[vm]]`, or keep `RERANKER_ENABLED=false`. |
| Vercel build fails on missing env var | Add `NEXT_PUBLIC_API_BASE_URL` to **all** environments (Prod, Preview, Dev). |
| `bad interpreter: /bin/sh^M` on Docker | Make sure `.gitattributes` is committed and the entrypoint has LF endings. |
