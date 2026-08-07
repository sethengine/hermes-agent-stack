---
source_session: 20260717_212837_8dd700
date: 2026-07-17
category: software
tags: [chrome, google-pay, autofill, cvc, payment, troubleshooting]
---

# Chrome CVC/Card Verification Error Fixes

The error *"This card can't be verified right now"* or *"Check your CVC and try again"* in Chrome is a **Google Pay/Wallet autofill issue**, not a card or bank problem.

## Root Causes
- **Stale cached card data** — saved card out of sync with Google's backend
- **VPN/firewall/ad blocker** — interferes with Google's verification handshake
- **Browser cache corruption** — stale cookies break the verification flow
- **Google server-side hiccup** — verification endpoint temporarily errors
- **Payment processor mismatch** — merchant gateway doesn't fully support Google Pay
- **Card not linked** — saved in Chrome but not associated with Google Wallet

## Fixes (ordered by effectiveness)
1. **Remove and re-add the card** in Chrome Settings → Autofill → Payment Methods (stale CVC is the #1 culprit)
2. **Manually type card details** on the payment page instead of using autofill
3. **Disable VPN/firewall/ad blocker** temporarily
4. **Clear Chrome cache and cookies** at `chrome://settings/clearBrowserData`
5. **Update Chrome** to latest version
6. **Log out and back into Google account** in Chrome

## Known Bug
[Chromium issue #40142861](https://issues.chromium.org/issues/40142861) tracks this exact failure, especially with Mastercard.

[[google-pay-autofill-bugs]] [[chrome-browser-troubleshooting]]
