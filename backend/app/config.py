"""Runtime configuration loaded from environment / .env."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_ROOT.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[REPO_ROOT / ".env", BACKEND_ROOT / ".env"],
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM ---
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL"
    )
    llm_model: str = Field(default="openai/gpt-4o-mini", alias="LLM_MODEL")
    llm_fallback_model: str = Field(
        default="google/gemini-flash-1.5", alias="LLM_FALLBACK_MODEL"
    )
    llm_temperature: float = Field(default=0.2, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=800, alias="LLM_MAX_TOKENS")

    # --- Embeddings / reranker ---
    embedding_backend: str = Field(default="auto", alias="EMBEDDING_BACKEND")
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2", alias="EMBEDDING_MODEL"
    )
    embedding_device: str = Field(default="cpu", alias="EMBEDDING_DEVICE")
    hf_inference_token: str = Field(default="", alias="HF_INFERENCE_TOKEN")
    reranker_enabled: bool = Field(default=False, alias="RERANKER_ENABLED")
    reranker_model: str = Field(default="BAAI/bge-reranker-base", alias="RERANKER_MODEL")

    # --- Vector store ---
    chroma_path: str = Field(default="./data/chroma", alias="CHROMA_PATH")
    chroma_collection: str = Field(default="vartalaap_kb", alias="CHROMA_COLLECTION")

    # --- Retrieval knobs ---
    retriever_top_k_candidates: int = Field(default=50, alias="RETRIEVER_TOP_K_CANDIDATES")
    retriever_top_k_final: int = Field(default=5, alias="RETRIEVER_TOP_K_FINAL")
    faq_high_confidence: float = Field(default=0.85, alias="FAQ_HIGH_CONFIDENCE")
    faq_medium_confidence: float = Field(default=0.60, alias="FAQ_MEDIUM_CONFIDENCE")

    # --- History ---
    history_turns: int = Field(default=2, alias="HISTORY_TURNS")
    history_relevance_threshold: float = Field(
        default=0.80, alias="HISTORY_RELEVANCE_THRESHOLD"
    )

    # --- Reflexion loop ---
    reflexion_enabled: bool = Field(default=True, alias="REFLEXION_ENABLED")
    reflexion_max_iterations: int = Field(default=2, alias="REFLEXION_MAX_ITERATIONS")

    # --- Observability ---
    observability_log_dir: str = Field(default="./logs", alias="OBSERVABILITY_LOG_DIR")
    observability_stdout: bool = Field(default=True, alias="OBSERVABILITY_STDOUT")

    # --- MLflow ---
    mlflow_enabled: bool = Field(default=True, alias="MLFLOW_ENABLED")
    mlflow_tracking_uri: str = Field(default="./mlruns", alias="MLFLOW_TRACKING_URI")
    mlflow_experiment: str = Field(default="vartalaap", alias="MLFLOW_EXPERIMENT")

    # --- API ---
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    # Kept as a plain string here so pydantic-settings does not try to JSON-decode it.
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    # Resolved absolute paths
    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def chroma_abs_path(self) -> Path:
        p = Path(self.chroma_path)
        return p if p.is_absolute() else (BACKEND_ROOT / p)

    @property
    def log_abs_dir(self) -> Path:
        p = Path(self.observability_log_dir)
        return p if p.is_absolute() else (BACKEND_ROOT / p)

    @property
    def mlflow_tracking_uri_resolved(self) -> str:
        uri = self.mlflow_tracking_uri
        # Local path shorthand → absolute file:// URI so mlflow writes under backend/.
        if uri.startswith(("http://", "https://", "file:", "sqlite:", "databricks:")):
            return uri
        p = Path(uri)
        if not p.is_absolute():
            p = BACKEND_ROOT / p
        p.mkdir(parents=True, exist_ok=True)
        return p.absolute().as_uri()

    @property
    def has_llm_key(self) -> bool:
        return bool(self.openrouter_api_key and not self.openrouter_api_key.endswith("REPLACE_ME"))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
