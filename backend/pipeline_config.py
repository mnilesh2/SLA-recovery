"""Centralized pipeline configuration — single source of truth for all configurable pipeline behavior."""

from .config import settings


class PipelineConfig:
    """All pipeline magic values in one place, configurable via .env/Settings."""

    # DuckDB table name — must match what's referenced in prompts and code
    TABLE_NAME = settings.sql_table_name

    # Cost-type suffix convention — maps suffix to cost-type metadata
    COST_SUFFIXES = {
        "_monetary": {"type": "monetary", "currency": settings.default_currency},
        "_credits": {"type": "credits", "currency": None},
        "_units": {"type": "units", "currency": None},
    }

    # LLM configuration
    LLM_MODEL = settings.llm_model
    LLM_MAX_TOKENS = settings.llm_max_tokens
    LLM_TEMPERATURE = settings.llm_temperature

    @classmethod
    def get_cost_type_info(cls, suffix: str) -> dict:
        """Look up cost-type info by suffix. Returns {"type": str, "currency": Optional[str]}."""
        return cls.COST_SUFFIXES.get(suffix, {})

    @classmethod
    def get_suffix_for_cost_type(cls, cost_type: str) -> str:
        """Reverse lookup: find the suffix for a given cost-type string."""
        for suffix, info in cls.COST_SUFFIXES.items():
            if info["type"] == cost_type:
                return suffix
        return None

    @classmethod
    def suffix_list(cls) -> list:
        """Return list of all recognized suffixes."""
        return list(cls.COST_SUFFIXES.keys())
