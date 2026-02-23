"""Unit tests for wework_send.send_wework_text."""
import pytest


@pytest.fixture
def mock_post(monkeypatch):
    calls = []
    def fake_post(url, *args, **kwargs):
        calls.append({"url": url, "json": kwargs.get("json")})
        class R:
            status_code = 200
            def raise_for_status(self): pass
            def json(self): return {"errcode": 0}
        return R()
    monkeypatch.setattr("wework_send.requests.post", fake_post)
    return calls


def test_send_wework_text_success(mock_post):
    from wework_send import send_wework_text
    ok = send_wework_text("https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test", "hello")
    assert ok is True
    assert len(mock_post) == 1
    assert mock_post[0]["json"]["msgtype"] == "text"
    assert mock_post[0]["json"]["text"]["content"] == "hello"


def test_send_wework_text_empty_content_returns_false(mock_post):
    from wework_send import send_wework_text
    ok = send_wework_text("https://example.com/hook", "")
    assert ok is False
    assert len(mock_post) == 0


def test_send_wework_text_empty_url_returns_false(mock_post):
    from wework_send import send_wework_text
    ok = send_wework_text("", "hello")
    assert ok is False
    assert len(mock_post) == 0


def test_send_wework_text_api_errcode_nonzero(monkeypatch):
    def fake_post(*args, **kwargs):
        class R:
            status_code = 200
            def raise_for_status(self): pass
            def json(self): return {"errcode": 40001}
        return R()
    monkeypatch.setattr("wework_send.requests.post", fake_post)
    from wework_send import send_wework_text
    ok = send_wework_text("https://example.com/hook", "hi")
    assert ok is False
