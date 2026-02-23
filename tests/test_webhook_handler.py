"""Unit tests for enterprise wechat callback endpoint."""

import json

import pytest


class DummyCrypt:
    def __init__(self):
        self.encrypt_calls = []
        self.last_decrypt = None

    def VerifyURL(self, msg_signature, timestamp, nonce, echostr):
        if msg_signature == "ok-sign":
            return 0, "verified-echo"
        return -1, None

    def DecryptMsg(self, post_data, msg_signature, timestamp, nonce):
        self.last_decrypt = (post_data, msg_signature, timestamp, nonce)
        if msg_signature != "ok-sign":
            return -1, None
        return 0, json.dumps(
            {
                "ToUserName": "wwcorp",
                "FromUserName": "zhangsan",
                "MsgType": "text",
                "Content": "你好机器人",
                "AgentID": 1000002,
            },
            ensure_ascii=False,
        )

    def EncryptMsg(self, sReplyMsg, sNonce, timestamp=None):
        self.encrypt_calls.append((sReplyMsg, sNonce, timestamp))
        return 0, '{"encrypt":"cipher","msgsignature":"abc","timestamp":"1","nonce":"2"}'


@pytest.fixture
def client(monkeypatch):
    from app import app

    dummy = DummyCrypt()
    app.config["TESTING"] = True
    monkeypatch.setattr("app._build_crypto", lambda: dummy)
    monkeypatch.setattr("app.ask_opencode", lambda **kwargs: "这是 AI 回复")
    return app.test_client(), dummy


def test_health(client):
    c, _ = client
    r = c.get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_verify_url_success(client):
    c, _ = client
    r = c.get(
        "/webhook/wework?msg_signature=ok-sign&timestamp=1&nonce=2&echostr=ENCSTR"
    )
    assert r.status_code == 200
    assert r.data.decode("utf-8") == "verified-echo"


def test_verify_url_failed(client):
    c, _ = client
    r = c.get(
        "/webhook/wework?msg_signature=bad&timestamp=1&nonce=2&echostr=ENCSTR"
    )
    assert r.status_code == 403


def test_callback_post_encrypt_reply(client):
    c, dummy = client
    r = c.post(
        "/webhook/wework?msg_signature=ok-sign&timestamp=1&nonce=2",
        data='{"encrypt":"xxx"}',
        content_type="application/json",
    )
    assert r.status_code == 200
    assert "encrypt" in r.data.decode("utf-8")

    assert len(dummy.encrypt_calls) == 1
    reply_plaintext = json.loads(dummy.encrypt_calls[0][0])
    assert reply_plaintext["Content"] == "这是 AI 回复"
    assert reply_plaintext["ToUserName"] == "zhangsan"
