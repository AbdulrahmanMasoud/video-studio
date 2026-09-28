"""LLM routing settings: the implementation lives in vs_api.core.llm_settings (shared with the admin endpoint); re-exported here."""
from vs_api.core.llm_settings import DEFAULTS_BY_AVAILABILITY, PROVIDER_ENV, SETTING_KEYS, LLMSettings, provider_of, provider_status

__all__ = ["DEFAULTS_BY_AVAILABILITY", "PROVIDER_ENV", "SETTING_KEYS", "LLMSettings", "provider_of", "provider_status"]
