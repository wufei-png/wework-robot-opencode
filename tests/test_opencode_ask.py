"""Unit tests for opencode_client.ask_opencode and reply extraction."""
import pytest


@pytest.fixture
def mock_requests(monkeypatch):
    """Mock requests.post and requests.get."""
    post_calls = []
    get_calls = []

    def fake_post(url, *args, **kwargs):
        post_calls.append({"url": url, "json": kwargs.get("json")})
        if "/session" in url and "/message" not in url:
            # create session
            class R:
                status_code = 200
                def raise_for_status(self): pass
                def json(self): return {"id": "session-123"}
            return R()
        if "/message" in url:
            class R:
                status_code = 200
                def raise_for_status(self): pass
                def json(self): return {"parts": [{"type": "text", "text": "Hello from agent."}]}
            return R()
        raise NotImplementedError(url)

    def fake_get(url, *args, **kwargs):
        get_calls.append({"url": url})
        return None

    monkeypatch.setattr("opencode_client.requests.post", fake_post)
    monkeypatch.setattr("opencode_client.requests.get", fake_get)
    return {"post": post_calls, "get": get_calls}


def test_ask_opencode_returns_reply_text(mock_requests, monkeypatch):
    monkeypatch.setenv("OPENCODE_API_URL", "http://localhost:4096")
    monkeypatch.setenv("OPENCODE_AGENT_NAME", "docs-searcher")
    from opencode_client import ask_opencode

    out = ask_opencode("hello")
    assert out == "Hello from agent."
    assert len(mock_requests["post"]) == 2  # session + message
    assert mock_requests["post"][0]["json"]["title"] == "Wework Robot"
    assert mock_requests["post"][1]["json"]["parts"][0]["text"] == "hello"


def test_ask_opencode_empty_message_returns_hint(monkeypatch):
    from opencode_client import ask_opencode
    monkeypatch.setenv("OPENCODE_API_URL", "http://localhost:4096")
    out = ask_opencode("")
    assert "请发送要咨询的内容" in out


def test_extract_reply_text_from_response():
    from opencode_client import _extract_reply_text_from_response

    assert _extract_reply_text_from_response({"parts": [{"type": "text", "text": "  ok  "}]}) == "ok"
    assert _extract_reply_text_from_response({"content": "direct"}) == "direct"
    assert _extract_reply_text_from_response({}) == ""
    assert _extract_reply_text_from_response(None) == ""
