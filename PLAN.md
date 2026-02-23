# Implementation Plan: Enterprise WeChat Robot @Reply via OpenCode

## 1. Requirements Restatement

- **Goal**: In an Enterprise WeChat (企业微信) group that has a robot with a webhook, when a user **@mentions the robot**, the robot should **reply** using the OpenCode backend.
- **Input**: Incoming trigger when the robot is @mentioned (we need to receive this via an HTTP callback or equivalent).
- **Backend**: Reuse OpenCode API (session + message) as in `opencode_client.py`; config: `OPENCODE_API_URL`, `OPENCODE_AGENT_NAME`.
- **Config**: 
  - `OPENCODE_API_URL` (default `http://127.0.0.1:4096`)
  - `OPENCODE_AGENT_NAME` (default `docs-searcher`)
  - Webhook URL for **sending** replies (default `https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx`)
- **Deliverables**: Implement the feature, add unit tests and E2E tests in this repo.

**Important note on receiving @mentions**: The standard 群机器人 (group robot) webhook only provides a **send** URL. To receive messages when users @ the robot, you typically need either (a) 自建应用 with “接收消息” and a callback URL pointing to our server, or (b) a compatible gateway that forwards such events to our server. This plan implements an **HTTP endpoint that accepts incoming “message” payloads** (e.g. from such a callback or from a test client). We will support a simple JSON body (e.g. `content` or `text.content`) so the same server works for tests and for real WeChat callbacks once the callback URL is configured.

---

## 2. Implementation Phases

### Phase 1: Project layout and config

- Add a minimal Python app at repo root (or a dedicated `app/`/`src/` package) that will run the webhook server.
- Introduce config (env or `.env`) for:
  - `OPENCODE_API_URL` (default `http://127.0.0.1:4096`)
  - `OPENCODE_AGENT_NAME` (default `docs-searcher`)
  - `WEWORK_WEBHOOK_URL` (default the provided webhook URL; used only for **sending** replies).
- Add `requirements.txt` with: `requests`, `flask` (or `fastapi` + `uvicorn`), and any existing deps (e.g. `loguru` if used by `opencode_client`). Prefer a single ASGI/WSGI server so E2E can hit the same app.

### Phase 2: OpenCode “ask” function (reuse + adapt)

- Extract or reuse from `opencode_client.py` the logic that:
  - Creates a session (POST `/session` with title).
  - Sends a user message to the session (POST `/session/{id}/message`) with the configured agent and the user’s text.
  - Waits for and returns the API response.
- Add a single function, e.g. `ask_opencode(user_message: str) -> str`, that returns the **reply text** to send back. Handle:
  - OpenCode API response shape (e.g. extract text from `parts` or whatever the API returns).
  - Timeouts and errors: return a safe fallback string (e.g. “OpenCode 暂时不可用” or “Request failed”) so the robot can still reply.
- Keep optional auth (e.g. `OPENCODE_SERVER_PASSWORD` / `OPENCODE_SERVER_USERNAME`) as in current `opencode_client.py`.

### Phase 3: WeWork “send” via webhook

- Implement a function that sends a **text** message to the group using the WeWork webhook URL:
  - `POST WEWORK_WEBHOOK_URL` with body `{"msgtype": "text", "text": {"content": "<reply_text>"}}`.
- Use the official format (e.g. from wework API docs / `weworkapi_python` reference); respect rate limit (e.g. 20 msg/min) in logging or comments.
- No need to use `weworkapi_python` for this endpoint: the group robot uses the webhook URL with `key=`, not corp `access_token`.

### Phase 4: Webhook server (receive → OpenCode → send)

- Expose one HTTP endpoint (e.g. `POST /webhook/wework` or `POST /`) that:
  1. Accepts JSON body. Support at least:
     - `{"text": {"content": "user message"}}` or
     - `{"content": "user message"}`  
     so both WeChat-like and simple payloads work.
  2. Optionally check that the request is “for” the robot (e.g. only process if `msgtype` is text or a specific field indicates @robot; if WeChat sends more fields, parse them later).
  3. Extracts the user message text; if empty, respond with a short hint (e.g. “请发送要咨询的内容”).
  4. Calls `ask_opencode(user_message)` to get the reply text.
  5. Sends the reply via the WeWork webhook send function.
  6. Returns 200 with a simple JSON (e.g. `{"ok": true}`) so WeChat/gateway does not retry.
- Run the server with a configurable host/port (e.g. `0.0.0.0:5000` or env `PORT`). For production, document that this URL must be set as the “接收消息” callback (or equivalent) in 企业微信 so that when users @ the robot, WeChat POSTs to this endpoint.

### Phase 5: Unit tests

- **Config**: Test that defaults and env overrides for `OPENCODE_API_URL`, `OPENCODE_AGENT_NAME`, `WEWORK_WEBHOOK_URL` are applied correctly (e.g. via a small config module or env mocks).
- **OpenCode client**: 
  - Mock `requests.post`/`requests.get` for session creation and message send; assert the right URLs and payloads; simulate success and failure (timeout, 4xx/5xx); assert `ask_opencode` returns the extracted reply or a fallback string.
- **WeWork send**: 
  - Mock `requests.post` to the webhook URL; assert body is `msgtype: text` and `content` is the given string; assert 200 handling.
- **Webhook handler**: 
  - With mocked `ask_opencode` and WeWork send, send `POST /webhook/wework` with sample JSON; assert 200, reply content sent to WeWork, and optional JSON response body.

Use `pytest` and keep tests in `tests/` (e.g. `tests/test_opencode_ask.py`, `tests/test_wework_send.py`, `tests/test_webhook_handler.py`).

### Phase 6: E2E test

- **Local E2E**: 
  - Start the webhook server in the background (or in-process with a test client).
  - Optionally start a mock OpenCode server (e.g. Flask route that returns a fixed session id and a fixed message response) if we don’t want to depend on a real OpenCode instance.
  - Send `POST` to the webhook endpoint with a test message; assert that the server returns 200 and that the WeWork send was called with the expected content (mock the WeWork webhook in E2E so we don’t post to real WeChat).
- **Real E2E (optional, documented)**: 
  - Run server against real OpenCode and real WeWork webhook; @ the robot in the group and verify reply. Document in README as manual/optional.

---

## 3. Dependencies

- **Internal**: `opencode_client.py` (refactor or import from it for session + message logic).
- **External**: OpenCode Serve (running and reachable at `OPENCODE_API_URL`), 企业微信 webhook (only for sending; no dependency for receiving beyond our HTTP endpoint).

---

## 4. Risks and Mitigations

| Risk | Level | Mitigation |
|------|--------|-------------|
| OpenCode response schema differs from assumption | Medium | Inspect real API response or doc; make reply extraction defensive (e.g. try `parts[0].text` or `content`), fallback to “暂无回复”. |
| WeChat callback format differs (e.g. encrypted) | Medium | Phase 1 endpoint accepts simple JSON; later add a separate path or parser for WeChat 自建应用 encrypted callback if needed (e.g. use `weworkapi_python` callback_json decrypt). |
| Rate limit 20 msg/min | Low | Log warnings when sending; optional: simple in-memory throttle per webhook key. |
| No “receive” for 群机器人 in docs | Low | Document that users must configure 自建应用 接收消息 callback to our URL, or use a gateway; keep endpoint generic for tests. |

---

## 5. File / Component Overview

- `config.py` or `env` – load `OPENCODE_API_URL`, `OPENCODE_AGENT_NAME`, `WEWORK_WEBHOOK_URL`, optional auth.
- `opencode_client.py` – keep existing; add or import `ask_opencode(user_message) -> str` (or in a new `opencode_ask.py` that uses the same session/message logic).
- `wework_send.py` – send text to group via `WEWORK_WEBHOOK_URL`.
- `app.py` or `server.py` – Flask/FastAPI app with `POST /webhook/wework` (or `/`) that ties receive → ask_opencode → wework_send.
- `main.py` or `__main__` – run the server (e.g. `flask run` or `uvicorn app:app`).
- `tests/` – unit tests for config, opencode ask, wework send, webhook handler; E2E test that posts to the endpoint and asserts behavior with mocks.

---

## 6. Estimated Complexity

- **Backend (opencode + wework send + server)**: 2–3 hours  
- **Unit tests**: 1–2 hours  
- **E2E test**: ~1 hour  
- **Total**: about 4–6 hours.

---

## 7. Out of Scope (for this plan)

- Encrypted callback (自建应用 接收消息 解密): can be added later with `weworkapi_python` callback_json.
- Persisting conversation per user/chat: current design is stateless (one message → one OpenCode session → one reply).
- Rate limiting and retries beyond logging.

---

**Next step**: Confirm this plan (yes / modify / skip phases). After confirmation, implementation will proceed in the order above, then add tests and a short README update for config and run instructions.
