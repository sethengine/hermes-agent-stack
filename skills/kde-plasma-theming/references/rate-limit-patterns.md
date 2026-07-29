# Rate Limit Patterns (OCS / Pling.com)

Findings from bulk-downloading 3,751 KDE Plasma 6 themes from
`store.kde.org` via the `api.kde-look.org` OCS API.

## Rate Limit Profile

| Property | Value |
|----------|-------|
| Limited endpoint | `files*.pling.com/api/files/download/j/<JWT>` |
| Limit type | Per-IP sliding window |
| Window size | ~20 requests per ~200 seconds |
| Body vs resolve | Resolve-only requests (`-o /dev/null`) consume less quota |
| Error format | XML, ~147 bytes |
| Response code | `200` (not 429!) |

## Tested Gap Values

| Gap | Items before limit hit | Verdict |
|-----|----------------------|---------|
| 2s | ~12-15 | ❌ Hits limit |
| 3s | ~12-20 | ❌ Unreliable |
| 4s | ~10-15 | ❌ Hits limit after ~15 |
| 6s | ~5-10 | ❌ Still triggers (IP state from prior tests) |
| 10s | 20/20 tested | ✅ **Stays under window** |
| 20s | 5/5 tested | ✅ Very safe but slow |

## Key Insight: Two-Step Download

The JWT URL does a 302 redirect to a DigitalOcean Spaces CDN URL.
The CDN URL has **no rate limit**. Therefore:

1. Resolve JWT→CDN with 10s gaps (rate-limited step)
2. Download from CDN at full speed (no rate limit)

### Resolve-only pattern

```bash
# Get CDN URL without downloading body:
CDN_URL=$(curl -s -o /dev/null -w "%{redirect_url}" --max-time 30 \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) KDE Plasma 6" \
  -H "Referer: https://store.kde.org/" \
  "$JWT_URL")

# Then download from CDN at full speed:
curl -sL -o output.tar.xz --max-time 120 -H "User-Agent: Mozilla/5.0" "$CDN_URL"
```

## Cooldown Behavior

After hitting the rate limit:
- `retry_after` in XML response: typically 46-60 seconds
- **Actual effective cooldown: ~200 seconds to fully reset the window** — retrying after only `retry_after` seconds usually triggers another rate-limit response immediately
- During cooldown: ALL requests to `files*.pling.com` return rate-limit XML (even on a different JWT URL or with a different HTTP method)
- After full cooldown: the window resets and you get another ~20 requests

**Important:** The `retry_after` value is a soft suggestion, not a hard limit. Full window recovery takes ~3× that value.

## IP State Sensitivity

Rate-limit behavior depends heavily on the current state of your IP at the resolver. Tests from a **clean IP** (no prior requests in the window) show different breakpoints than tests from a **contaminated IP** (after prior requests were made):

| Gap | Clean IP (first window) | Contaminated IP (after hitting limit) |
|-----|------------------------|---------------------------------------|
| 6s  | ~15-20 before limit    | First request may already be blocked  |
| 10s | 20/20 (full window)    | ~5-10 before limit (remaining budget) |

Always let the cooldown expire fully (~200s) before resuming after a hit. Better yet, use the 10s steady strategy to never hit the limit in the first place.

## URL Lifetimes

| URL Type | Lifetime | Notes |
|----------|----------|-------|
| JWT URL (from OCS API) | ~1 hour | Embedded token expires |
| CDN URL (from 302) | 3600s (`X-Amz-Expires=3600`) | Per the AWS SigV4 signed URL |
| Stale JWT behavior | HTTP 500, not 403/404 | Apache returns 500 for expired tokens |
