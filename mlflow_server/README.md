# वार्तालाप — Hosted MLflow tracking server

Standalone MLflow tracking server, deployed on Render Free as a **second**
web service that shares a Neon.tech Postgres backend with the main
वार्तालाप backend.

## Why a separate folder / service?

- The backend's Python deps have zero overlap with what MLflow needs at
  runtime (no `torch`, no `openai`, no `mlflow-skinny` — Render Free has
  512 MB RAM and every megabyte counts).
- A dedicated `mlflow server` process gives us a proper HTTPS-fronted
  tracking endpoint that both the backend (writer) and the browser
  (reader / UI) can hit.

## How the pieces connect

```
 backend  ─┐
           │  MLFLOW_TRACKING_URI = https://vartalaap-mlflow-XXXX.onrender.com
           ▼
   mlflow_server  ─┐
                   │  --backend-store-uri postgresql://...neon.tech/vartalaap
                   ▼
                Neon Postgres  (persists runs / traces / metrics / tags)
```

Artifacts (only used by MLflow's optional `log_text` / `log_dict`) live on
the MLflow server's ephemeral disk — see the caveat below.

## Deploying — see the full walkthrough in [`../docs/DEPLOY.md`](../docs/DEPLOY.md) §3c

TL;DR of the Render service configuration:

- **Root Directory:** `mlflow_server`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:**
  ```bash
  mlflow server \
    --backend-store-uri "$MLFLOW_BACKEND_STORE_URI" \
    --artifacts-destination /tmp/mlflow-artifacts \
    --serve-artifacts \
    --host 0.0.0.0 \
    --port $PORT
  ```
- **Environment Variables:**
  - `MLFLOW_BACKEND_STORE_URI` = your Neon Postgres URL (`postgresql://user:pass@host/dbname?sslmode=require`)

Then on the **backend** service, set:

```env
MLFLOW_TRACKING_URI=https://<your-mlflow-service>.onrender.com
```

The backend's `mlflow_tracking_uri_resolved` property passes any URI
starting with `http://` / `https://` straight through, so no code change
is required.

## Caveat — ephemeral artifacts

Render Free doesn't provide a persistent disk on the mlflow-server side,
so artifacts (any `mlflow.log_text` / `log_dict` calls in the app) will
be lost when the service sleeps or redeploys. In practice, वार्तालाप only
writes an optional `feedback_<id>.md` artifact when a user types a
feedback comment — that's the only thing you'll lose.

Runs / traces / metrics / tags all live in Postgres and are safe.

If you want durable artifacts too, plug in a free S3-compatible bucket
(Cloudflare R2 offers 10 GB free with no CC) and add:

```env
MLFLOW_ARTIFACT_ROOT=s3://<bucket>/mlflow
AWS_ACCESS_KEY_ID=<r2-key>
AWS_SECRET_ACCESS_KEY=<r2-secret>
MLFLOW_S3_ENDPOINT_URL=https://<account>.r2.cloudflarestorage.com
```
