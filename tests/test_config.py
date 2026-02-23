"""Unit tests for config module."""

import pytest


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    """Clear env vars that config reads so tests don't depend on real env."""
    for key in (
        "OPENCODE_API_URL",
        "OPENCODE_AGENT_NAME",
        "WEWORK_WEBHOOK_URL",
        "WEWORK_TOKEN",
        "WEWORK_ENCODING_AES_KEY",
        "WEWORK_RECEIVE_ID",
        "WEWORK_CORP_ID",
        "OPENCODE_SERVER_USERNAME",
        "OPENCODE_SERVER_PASSWORD",
    ):
        monkeypatch.delenv(key, raising=False)


def test_get_opencode_api_url_default(monkeypatch):
    from config import get_opencode_api_url
    assert get_opencode_api_url() == "http://127.0.0.1:4096"


def test_get_opencode_api_url_from_env(monkeypatch):
    monkeypatch.setenv("OPENCODE_API_URL", "http://myhost:4096")
    from config import get_opencode_api_url
    assert get_opencode_api_url() == "http://myhost:4096"


def test_get_opencode_agent_name_default(monkeypatch):
    from config import get_opencode_agent_name
    assert get_opencode_agent_name() == "docs-searcher"


def test_get_opencode_agent_name_from_env(monkeypatch):
    monkeypatch.setenv("OPENCODE_AGENT_NAME", "my-agent")
    from config import get_opencode_agent_name
    assert get_opencode_agent_name() == "my-agent"


def test_get_wework_webhook_url_default(monkeypatch):
    from config import get_wework_webhook_url
    url = get_wework_webhook_url()
    assert "qyapi.weixin.qq.com" in url and "webhook/send" in url and "key=" in url


def test_get_wework_webhook_url_from_env(monkeypatch):
    monkeypatch.setenv("WEWORK_WEBHOOK_URL", "https://example.com/hook")
    from config import get_wework_webhook_url
    assert get_wework_webhook_url() == "https://example.com/hook"


def test_get_wework_token_and_aes(monkeypatch):
    monkeypatch.setenv("WEWORK_TOKEN", "token-1")
    monkeypatch.setenv("WEWORK_ENCODING_AES_KEY", "aes-1")
    from config import get_wework_token, get_wework_encoding_aes_key

    assert get_wework_token() == "token-1"
    assert get_wework_encoding_aes_key() == "aes-1"


def test_get_wework_receive_id_priority(monkeypatch):
    monkeypatch.setenv("WEWORK_CORP_ID", "wwcorp")
    from config import get_wework_receive_id

    assert get_wework_receive_id() == "wwcorp"

    monkeypatch.setenv("WEWORK_RECEIVE_ID", "override-id")
    assert get_wework_receive_id() == "override-id"
