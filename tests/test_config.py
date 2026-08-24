from app.config import get_llm_config


def test_deepseek_config(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    config = get_llm_config()
    assert config.base_url == "https://api.deepseek.com/v1"
    assert config.model == "deepseek-chat"
    assert config.api_key == "test-key"

def test_qwen_config(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "qwen")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
    config = get_llm_config()
    assert config.base_url.endswith("/compatible-mode/v1")
    assert config.model == "qwen-plus"
    assert config.api_key == "test-key"
