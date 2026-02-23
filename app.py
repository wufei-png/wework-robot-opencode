"""Enterprise WeChat callback server for self-built applications."""

import json
import logging
import os
import secrets
import time
from pathlib import Path

from flask import Flask, Response, jsonify, request

from config import (
    get_opencode_agent_name,
    get_opencode_api_url,
    get_wework_encoding_aes_key,
    get_wework_receive_id,
    get_wework_token,
)
from opencode_client import ask_opencode
from wework_crypto import get_wxbiz_class

# Load .env from repo root if present
_env = Path(__file__).resolve().parent / ".env"
if _env.exists():
    try:
        from dotenv import load_dotenv

        load_dotenv(_env)
    except ImportError:
        pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)


def _build_crypto():
    token = get_wework_token()
    aes_key = get_wework_encoding_aes_key()
    receive_id = get_wework_receive_id()
    if not token or not aes_key or not receive_id:
        raise ValueError(
            "WEWORK_TOKEN / WEWORK_ENCODING_AES_KEY / WEWORK_RECEIVE_ID must be configured"
        )
    wxbiz_cls = get_wxbiz_class()
    return wxbiz_cls(token, aes_key, receive_id)


def _extract_text_message(message_obj: dict) -> str:
    if not isinstance(message_obj, dict):
        return ""
    content = message_obj.get("Content")
    if isinstance(content, str):
        return content.strip()
    return ""


def _build_passive_reply(incoming: dict, reply_text: str) -> dict:
    return {
        "ToUserName": incoming.get("FromUserName", ""),
        "FromUserName": incoming.get("ToUserName", ""),
        "CreateTime": int(time.time()),
        "MsgType": "text",
        "Content": reply_text,
        "AgentID": incoming.get("AgentID"),
    }


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/webhook/wework", methods=["GET", "POST"])
def webhook_wework():
    crypt = _build_crypto()
    msg_signature = request.args.get("msg_signature", "")
    timestamp = request.args.get("timestamp", "")
    nonce = request.args.get("nonce", "")

    if request.method == "GET":
        echostr = request.args.get("echostr", "")
        if not echostr:
            return Response("missing echostr", status=400, mimetype="text/plain")
        ret, s_echo_str = crypt.VerifyURL(msg_signature, timestamp, nonce, echostr)
        if ret != 0 or s_echo_str is None:
            logger.warning("VerifyURL failed, ret=%s", ret)
            return Response("verify failed", status=403, mimetype="text/plain")
        return Response(s_echo_str, status=200, mimetype="text/plain")

    post_data = request.get_data(as_text=True) or ""
    if not post_data:
        return Response("missing body", status=400, mimetype="text/plain")

    ret, plain_text = crypt.DecryptMsg(post_data, msg_signature, timestamp, nonce)
    if ret != 0 or plain_text is None:
        logger.warning("DecryptMsg failed, ret=%s", ret)
        return Response("decrypt failed", status=403, mimetype="text/plain")

    try:
        message_obj = json.loads(plain_text)
    except json.JSONDecodeError:
        return Response("invalid message json", status=400, mimetype="text/plain")

    user_message = _extract_text_message(message_obj)
    if not user_message:
        reply_text = "请发送文本消息。"
    else:
        reply_text = ask_opencode(
            user_message=user_message,
            api_url=get_opencode_api_url(),
            agent_name=get_opencode_agent_name(),
        )

    reply_obj = _build_passive_reply(message_obj, reply_text)
    reply_json = json.dumps(reply_obj, ensure_ascii=False)

    reply_nonce = secrets.token_hex(8)
    reply_ts = str(int(time.time()))
    ret, encrypted_reply = crypt.EncryptMsg(reply_json, reply_nonce, reply_ts)
    if ret != 0 or encrypted_reply is None:
        logger.warning("EncryptMsg failed, ret=%s", ret)
        return Response("encrypt failed", status=500, mimetype="text/plain")

    return Response(encrypted_reply, status=200, mimetype="application/json")


@app.route("/", methods=["GET"])
def index():
    return (
        jsonify(
            {
                "service": "wework-robot-opencode",
                "callback": "/webhook/wework",
                "mode": "enterprise-wechat-self-built-app",
            }
        ),
        200,
    )


def main():
    port = int(os.environ.get("PORT", "5000"))
    host = os.environ.get("HOST", "0.0.0.0")
    app.run(host=host, port=port, debug=os.environ.get("FLASK_DEBUG", "0") == "1")


if __name__ == "__main__":
    main()
