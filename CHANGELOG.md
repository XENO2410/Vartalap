# Changelog

All notable changes to **वार्तालाप (Vartalaap)** are documented here. The format
is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] — 2026-08-25

First public release. Feature-complete dummy chatbot mirroring the ADI
architecture end-to-end, with proper MLflow-based GenAI observability.

### Added

- **Architecture pipeline** — preprocessing (language detect → translate →
  spell correct → glossary), input & output guardrails, supervisor agent
  with reactive tool selection, reflexion review loop, three tools (RAG
  Knowledge Base, mock Status Retrieval, in-memory Text2SQL).
- **Message schema** matching the ADI doc §3 / §12 — every field emitted as
  JSONL under `backend/logs/events-YYYY-MM-DD.jsonl`.
- **MLflow tracing** — one run per session, one trace per turn, one span per
  stage (LLM / RETRIEVER / TOOL / AGENT / CHAIN) with inputs, outputs,
  attributes and latency.
- **Eval metrics** per turn — context relevance, faithfulness, answer
  relevance, chat history relevance, tone appropriateness, toxicity,
  composite RAG score. Written both as trace tags and as step-indexed
  `turn.*` / `eval.*` metrics on the session run.
- **Cost tracking** — per-model USD/1M-token pricing (`backend/app/metrics/costs.py`)
  aggregated into `turn.cost_usd` and `system.total_cost_usd`.
- **System roll-up run** — a single `system::vartalaap` run in the same
  experiment that receives cross-session totals + rolling averages
  (turns, sessions, tokens, likes/dislikes, RAG score, etc.).
- **Feedback attached to the trace** — 👍 / 👎 / ⬜ None sets `feedback`,
  `feedback_score` and `feedback_comment` tags on the existing trace via
  `MlflowClient.set_trace_tag`; no new trace spawned.
- **Dummy login** — display-name modal on first load, stable `user_id`
  stored in `localStorage`, attached to every `/chat` and `/feedback` call.
- **Next.js 14 frontend** in the Axis pink/maroon theme — bubble tabs, landing
  hero, chat window with source cards (Relevancy / Type), suggestion chips,
  message-id + trace-id chips, feedback buttons.
- **FastAPI backend** exposing `/chat`, `/feedback`, `/kb/reindex`, `/health`
  and OpenAPI docs at `/docs`.
- **Pure-Python vector store** — numpy + JSONL persistence, no `hnswlib`
  MSVC dependency on Windows.
- **Sample corpus** — 40+ FAQs and 11 synthetic policy docs across HR, Law,
  IT Helpdesk, Aha, CR, Financial Advisor, Axis Phone, Conversational BI,
  Download plus two Wikipedia-derived background docs (KYC, RAG).
- **Docker + docker-compose** — one-command bring-up of backend + frontend +
  MLflow UI with volume-persisted state.
- **MIT license**.

### Notes

- The bundled OpenRouter key referenced in early notes was rotated. Users
  must supply their own `OPENROUTER_API_KEY` via `.env`.

[Unreleased]: https://github.com/XENO2410/ADI/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/XENO2410/ADI/releases/tag/v1.0.0
