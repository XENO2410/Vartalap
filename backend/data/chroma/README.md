# Bundled Vector Store

This folder ships **pre-computed embeddings** for the sample knowledge base
so the deployed backend does not need to run `sentence-transformers` +
`torch` at runtime. Two files are committed:

- `vartalaap_kb.jsonl` — one JSON record per chunk (id, text, metadata).
- `vartalaap_kb.npy` — an (N, 384) float32 numpy array of L2-normalised
  vectors, row-aligned with the JSONL.

Both were produced with **`sentence-transformers/all-MiniLM-L6-v2`**. At
query time the backend calls the [Hugging Face Inference API](https://huggingface.co/docs/api-inference)
for the *one* query embedding per chat turn (free tier, ~1000 req/day —
set `HF_INFERENCE_TOKEN` in your env).

## Regenerating

Only needed if you change the FAQs or the documents. From `backend/`:

```bash
# Requires torch + sentence-transformers installed locally.
pip install sentence-transformers
python -m scripts.seed_kb --reset
```

The `--reset` flag drops the existing files and writes fresh ones. Commit
the new `vartalaap_kb.jsonl` + `vartalaap_kb.npy`.

If you *don't* have torch locally you can seed via the HF Inference API
instead (slower — one API call per chunk):

```bash
$env:HF_INFERENCE_TOKEN = "hf_..."
$env:EMBEDDING_BACKEND  = "hf_api"
python -m scripts.seed_kb --reset
```
