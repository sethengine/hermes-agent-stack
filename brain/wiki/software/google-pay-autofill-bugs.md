---
source_session: 20260717_212837_8dd700
date: 2026-07-17
category: software
tags: [google-pay, chrome, autofill, payment, bugs]
---

# Google Pay Autofill Verification Issues

Google Pay's browser autofill system has a known class of bugs where CVC verification fails despite the card being valid. This is distinct from card declines or bank-side issues.

## Architecture
Chrome's autofill stores card data locally and validates CVC against Google's servers at checkout time. When this server handshake fails (timeout, mismatch, stale token), the browser blocks the transaction even though the payment processor would accept the card.

## Key Facts
- Manually entering card details always works when autofill fails — proving the card/bank are fine
- The bug is intermittent and often resolves with a re-add cycle
- Google's community forums show years of unresolved reports

## Workarounds
- Manual entry on payment page (immediate fix)
- Remove and re-add card in Chrome settings (medium-term fix)
- Disable third-party autofill interference (conflicts with password managers)

[[chrome-card-verification-fixes]] [[chrome-browser-troubleshooting]]
