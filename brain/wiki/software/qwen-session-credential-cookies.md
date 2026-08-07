---
title: Qwen Session Credential and Analytics SDK
date: 2026-08-06
source_session: 20260806_190913_656bdb
category: software
tags: [qwen, cookies, oauth, session-credential, analytics, security, omniroute]
---

# Qwen Web Session Credential (for browser-based providers)

Qwen Web (Free) authenticates via a **browser web session**, not an API key. Providers like OmniRoute that offer a Qwen Web route ask for a session credential = the full browser `Cookie` header (must include `cna`, `ssxmod_itna`, `token`).

How to obtain it: sign in at `chat.qwen.ai`, open browser DevTools, copy the full `Cookie` request header.

## Pitfall: analytics JS is NOT the credential

The `aplus` / `goldlog` JavaScript block is Alibaba's **web-analytics SDK** that loads on every `chat.qwen.ai` page. It only *reads* `document.cookie`; it does **not** contain the session credential and there is nothing in it to parse for a cookie.

## Security
Treat a pasted live session credential (JWT + auth cookies) as compromised if visible to others. Do not commit it to git; sign out/in at `chat.qwen.ai` after use to invalidate it.

## Related
- [[omniroute-boot-service-docker]]
- [[llm-audit-prompt-design-principles]]