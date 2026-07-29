# OCS API Reference — KDE Store

## Base URL

```
https://api.kde-look.org/ocs/v1/content/data
```

Provider config: `https://autoconfig.kde.org/ocs/providers.xml`

## Sample Response (abbreviated)

```json
{
    "status": "ok",
    "statuscode": 100,
    "totalitems": 292,
    "itemsperpage": 100,
    "data": [
        {
            "id": 2244767,
            "name": "Horizon Dark",
            "version": "1.1.5",
            "typeid": 722,
            "typename": "Global Themes (Plasma 6)",
            "personid": "zayronXIO",
            "created": "2025-01-15T07:48:13+00:00",
            "changed": "2026-02-16T00:50:18+00:00",
            "downloads": "1433",
            "score": 50,
            "summary": "horizon Dark",
            "downloadlink1": "https://files06.pling.com/api/files/download/j/eyJ...",
            "downloadname1": "Horizon.Dark.tar.xz",
            "downloadsize1": 35,
            "downloadmd5sum1": "3bba2944a4bc1d378cd366f3cf08a516",
            "downloadtags1": "data##mimetype=application/x-xz",
            "previewpic1": "https://images.pling.com/cache/770x540-4/img/...",
            "detailpage": "https://store.kde.org/p/2244767",
            "tags": "linux,kde,plasma,plasma##majorversion=6,unix,theme,agplv3"
        }
    ]
}
```

## JSON Cleanup Required

The API returns JSON with embedded control characters (raw HTML in `description` fields). Strip them:

```python
import re
cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', raw_json)
```

Without this, `json.loads()` fails with control-character errors.

## Pagination Quirks

- `pagesize` defaults to **10** if not specified. Always pass `pagesize=100`.
- Last page may return **0 items** even though `totalitems` suggests it should exist.
  - Example: cat=722, total=292, pagesize=100 → page 1: 100, page 2: 92, page 3: 0 items
  - Stop when an empty page is returned, don't rely solely on ceil(total/pagesize) math.
- Some categories have items missing download links (especially color schemes).

## Download URL Chain

1. **API returns** `downloadlink1` → `https://files06.pling.com/api/files/download/j/<JWT_TOKEN>/<filename>`
2. **files06.pling.com** responds with HTTP 302 → `https://ocs-dl.fra1.cdn.digitaloceanspaces.com/data/files/<id>/<filename>?X-Amz-...`
3. **CDN URL** includes `X-Amz-Expires=3600` (1-hour validity from issuance)
4. **curl -sL -o** follows the chain automatically

The JWT tokens appear to support reuse within their lifetime (tested working 30+ seconds after issuance, not tested at full 1-hour expiry).

## Rate-Limit Error Response

When rate-limited, the CDN gateway returns HTTP 200 with XML body:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<response>
    <status>error</status>
    <message>too many requests</message>
    <retry_after>46</retry_after>
</response>
```

- Response size: ~147 bytes
- `retry_after`: 40-60 seconds typical
- Save this check as XML, not as binary — file command shows "XML 1.0 document, ASCII text"
- Detection: check for `"too many requests"` in file text content
