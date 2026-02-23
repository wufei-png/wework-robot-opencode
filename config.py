"""
Configuration for wework-robot-opencode.
Reads from environment variables; defaults match plan.
"""
import os


def get_opencode_api_url() -> str:
    return os.environ.get("OPENCODE_API_URL", "http://127.0.0.1:4096")


def get_opencode_agent_name() -> str:
    return os.environ.get("OPENCODE_AGENT_NAME", "docs-searcher")


def get_wework_webhook_url() -> str:
    return os.environ.get(
        "WEWORK_WEBHOOK_URL",
        "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx",
    )


def get_opencode_username() -> str:
    return os.environ.get("OPENCODE_SERVER_USERNAME", "opencode")


def get_opencode_password() -> str:
    return os.environ.get("OPENCODE_SERVER_PASSWORD", "")


def get_wework_token() -> str:
    """企业微信「接收消息」配置里的 Token。"""
    return os.environ.get("WEWORK_TOKEN", "")


def get_wework_encoding_aes_key() -> str:
    """企业微信「接收消息」配置里的 EncodingAESKey。"""
    return os.environ.get("WEWORK_ENCODING_AES_KEY", "")


def get_wework_receive_id() -> str:
    """回调接收方 ID：自建应用通常是企业 CorpID。"""
    return os.environ.get("WEWORK_RECEIVE_ID", os.environ.get("WEWORK_CORP_ID", ""))
