"""
Send text messages to Enterprise WeChat group via webhook.
URL format: https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=KEY
Rate limit: 20 messages per minute per robot.
"""
import logging
import requests

logger = logging.getLogger(__name__)


def send_wework_text(webhook_url: str, content: str) -> bool:
    """
    Send a text message to the group using the webhook URL.

    :param webhook_url: Full URL including key (e.g. .../webhook/send?key=xxx)
    :param content: Message content (UTF-8, max 2048 bytes).
    :return: True if sent successfully, False otherwise.
    """
    if not webhook_url or not webhook_url.strip():
        logger.error("[Wework] webhook_url is empty")
        return False
    if not content or not str(content).strip():
        logger.warning("[Wework] content is empty, not sending")
        return False

    payload = {"msgtype": "text", "text": {"content": str(content)[:2048]}}
    try:
        resp = requests.post(
            webhook_url.strip(),
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("errcode") != 0:
            logger.error("[Wework] API error: %s", data)
            return False
        return True
    except requests.exceptions.RequestException as e:
        logger.exception("[Wework] send failed: %s", e)
        return False
