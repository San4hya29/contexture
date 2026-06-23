import os
import yaml
from typing import Dict, Any
from llm.base import BaseLLM
from llm.providers.openai import OpenAILLM
from llm.providers.ollama import OllamaLLM

def get_llm_client() -> BaseLLM:
    # Load configuration
    base_dir = os.path.abspath(__file__)
    for _ in range(5):
        base_dir = os.path.dirname(base_dir)
    config_path = os.path.join(base_dir, "config", "redis_config.yaml")
    
    config = {}
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = yaml.safe_load(f) or {}

    llm_cfg = config.get("llm", {})
    provider = llm_cfg.get("provider", "openai").lower()
    model = llm_cfg.get("model", "gpt-4o-mini")
    api_key = llm_cfg.get("api_key", "mock-key")
    base_url = llm_cfg.get("base_url")

    # Environment variable overrides
    api_key = os.environ.get("OPENAI_API_KEY", api_key)
    model = os.environ.get("LLM_MODEL", model)

    if provider == "openai":
        return OpenAILLM(api_key=api_key, model=model, base_url=base_url)
    elif provider == "ollama":
        base_url = base_url or "http://localhost:11434/v1"
        return OllamaLLM(api_key=api_key, model=model, base_url=base_url)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
