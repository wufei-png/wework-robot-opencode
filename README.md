# wework-robot-opencode

企业微信「自建应用」回调机器人：用户消息进入企业微信回调后，服务解密消息、调用 OpenCode、再按企业微信协议加密被动回复。

## 架构

1. 企业微信回调 `GET /webhook/wework` 做 URL 验证  
2. 企业微信回调 `POST /webhook/wework` 推送加密消息  
3. 服务直接引用 `weworkapi_python/callback_json_python3` 的 `WXBizJsonMsgCrypt`  
4. 调用 OpenCode (`/session` + `/session/{id}/message`)  
5. 将回复按企业微信格式加密后原路返回

## 环境变量

### 企业微信回调必填

- `WEWORK_TOKEN`：回调配置里的 Token
- `WEWORK_ENCODING_AES_KEY`：回调配置里的 EncodingAESKey
- `WEWORK_RECEIVE_ID`：接收方 ID（自建应用一般为 CorpID）
  - 或用 `WEWORK_CORP_ID` 作为兜底

### OpenCode

- `OPENCODE_API_URL`（默认 `http://127.0.0.1:4096`）
- `OPENCODE_AGENT_NAME`（默认 `docs-searcher`）
- `OPENCODE_SERVER_USERNAME` / `OPENCODE_SERVER_PASSWORD`（可选）

## 运行

```bash
uv sync
uv run python app.py
```

首次使用请准备官方子仓库（避免重复造轮子）：

```bash
git submodule update --init --recursive
```

默认监听 `0.0.0.0:5000`，回调地址配置为：

`https://你的域名/webhook/wework`

## 接口

- `GET /health`：健康检查
- `GET /webhook/wework`：企业微信 URL 验证
- `POST /webhook/wework`：企业微信加密回调处理

## 测试

```bash
uv run pytest tests/ -v
```

## .env 示例

可直接复制：

```bash
cp .env.example .env
```

## 说明

- 当前实现以文本消息为主（`MsgType=text`）。
- 加解密逻辑直接来自官方 `weworkapi_python/callback_json_python3`，本仓库通过 `wework_crypto.py` 进行加载。
- 目前尚未完成“公网域名部署 + 企业微信真实流量”端到端验证；详见 [`roadmap.md`](roadmap.md)。
