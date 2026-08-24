from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    app_name: str = "AI 知识库问答后端"
    database_path: Path = Path(os.getenv("DATABASE_PATH", "data/assistant.db"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    alert_service_url: str = os.getenv("ALERT_SERVICE_URL", "").rstrip("/")

@dataclass(frozen=True)
class LLMConfig:
    provider: str
    base_url: str
    api_key: str | None
    model: str


def get_llm_config() -> LLMConfig:
    """读取兼容 OpenAI Chat Completions 协议的模型配置。"""
    provider = os.getenv("LLM_PROVIDER", "custom").strip().lower()
    custom_base_url = os.getenv("LLM_BASE_URL", "").strip()
    custom_model = os.getenv("LLM_MODEL", "").strip()
    if provider == "deepseek":
        return LLMConfig(
            provider="deepseek",
            base_url=custom_base_url or "https://api.deepseek.com/v1",
            api_key=os.getenv("DEEPSEEK_API_KEY") or os.getenv("LLM_API_KEY"),
            model=custom_model or "deepseek-chat",
        )
    if provider == "qwen":
        return LLMConfig(
            provider="qwen",
            base_url=custom_base_url
            or "https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=(
                os.getenv("DASHSCOPE_API_KEY")
                or os.getenv("QWEN_API_KEY")
                or os.getenv("LLM_API_KEY")
            ),
            model=custom_model or "qwen-plus",
        )
    return LLMConfig(
        provider="custom",
        base_url=custom_base_url,
        api_key=os.getenv("LLM_API_KEY"),
        model=custom_model,
    )


settings = Settings()
