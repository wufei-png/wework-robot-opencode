# Roadmap

## Current Status

- Core callback flow for Enterprise WeChat self-built app is implemented.
- URL verification (`GET /webhook/wework`) and encrypted callback handling (`POST /webhook/wework`) are covered by automated tests.
- OpenCode integration and passive encrypted reply path are in place.

## Remaining Work

- **Domain deployment and callback registration**
  - Deploy service behind a public HTTPS domain.
  - Configure Enterprise WeChat callback URL to `https://<your-domain>/webhook/wework`.
  - Validate production ingress/network/security headers.

- **True end-to-end validation in Enterprise WeChat**
  - Perform live message test from Enterprise WeChat client.
  - Verify callback decrypt -> OpenCode reply -> encrypt response full chain with real traffic.
  - Record a reproducible test checklist and sample evidence.

## Notes

- Current CI/local tests are integration-style with mocks and do not replace live domain-based E2E.
