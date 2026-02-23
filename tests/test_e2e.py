"""E2E: callback decrypt -> OpenCode call -> encrypted passive reply."""

import json

import pytest


class FakeCrypt:
    def __init__(self):
        self.encrypted_payload = None

    def VerifyURL(self, msg_signature, timestamp, nonce, echostr):
        return 0, "echo"

    def DecryptMsg(self, post_data, msg_signature, timestamp, nonce):
        plaintext = {
            "ToUserName": "wwcorp",
            "FromUserName": "lisi",
            "MsgType": "text",
            "Content": "帮我查文档",
            "AgentID": 1000002,
        }
        return 0, json.dumps(plaintext, ensure_ascii=False)

    def EncryptMsg(self, sReplyMsg, sNonce, timestamp=None):
        self.encrypted_payload = sReplyMsg
        return 0, '{"encrypt":"ENC","msgsignature":"SIG","timestamp":"T","nonce":"N"}'


@pytest.fixture
def setup_e2e(monkeypatch):
    fake_crypt = FakeCrypt()
    post_calls = []

    def fake_post(url, *args, **kwargs):
        post_calls.append({"url": url, "json": kwargs.get("json")})
        if url.endswith("/session"):
            class R:
                def raise_for_status(self):
                    return None

                def json(self):
                    return {"id": "s-1"}

            return R()
        if "/session/s-1/message" in url:
            class R:
                def raise_for_status(self):
                    return None

                def json(self):
                    return {"parts": [{"type": "text", "text": "文档在 docs/README.md"}]}

            return R()
        raise RuntimeError(f"unexpected url: {url}")

    monkeypatch.setattr("app._build_crypto", lambda: fake_crypt)
    monkeypatch.setattr("opencode_client.requests.post", fake_post)
    return fake_crypt, post_calls


def test_e2e_enterprise_callback_flow(setup_e2e):
    fake_crypt, post_calls = setup_e2e
    from app import app

    c = app.test_client()
    r = c.post(
        "/webhook/wework?msg_signature=ok&timestamp=1&nonce=2",
        data='{"encrypt":"xxx"}',
        content_type="application/json",
    )
    assert r.status_code == 200
    body = r.data.decode("utf-8")
    assert "encrypt" in body

    assert len(post_calls) == 2
    assert post_calls[0]["url"].endswith("/session")
    assert post_calls[1]["url"].endswith("/session/s-1/message")

    passive_reply = json.loads(fake_crypt.encrypted_payload)
    assert passive_reply["ToUserName"] == "lisi"
    assert "docs/README.md" in passive_reply["Content"]
