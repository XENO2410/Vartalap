# BI Platform Architecture

## Layers
1. Sources: core banking, CRM, cards, payments and HR systems.
2. Lakehouse: raw, curated and semantic layers on the analytics platform.
3. Serving: semantic models consumed by dashboards, notebooks and the
   conversational BI assistant.

## Data Flow
Change-data-capture and batch pipelines land data within defined freshness
SLAs. Transformations produce the curated and semantic layers.

## Access Paths
The conversational BI assistant reads only the semantic layer. No query
touches source systems directly.

## Resilience
Pipelines carry retries, dead-letter handling and data-quality gates.

Policy code: BI-ARCH-2026-01 | Owner: Data Platform team.
