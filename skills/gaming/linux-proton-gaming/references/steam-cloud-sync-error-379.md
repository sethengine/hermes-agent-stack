# Steam Error -379: ERR_HTTP_RESPONSE_CODE_FAILURE

## Raw Error

```
Error Code: -379
Failed to load web page (unknown error).
```

## Chromium Net Error Definition

From `net/base/net_error_list.h`:
```c
// The server returned a non-2xx HTTP response code.
// Not that this error is only used by certain APIs that interpret the HTTP
// response itself. URLRequest f...
NET_ERROR(HTTP_RESPONSE_CODE_FAILURE, -379)
```

## What Happens

Steam's CEF (Chromium Embedded Framework) browser renders the cloud sync overlay by making an HTTP request to Valve's internal cloud sync API endpoint. When that endpoint returns any non-2xx HTTP status code (502 Bad Gateway, 503 Service Unavailable, redirect loop, etc.), CEF surfaces this as error -379 with "Failed to load web page (unknown error)".

## Confirmed Working Fixes (Manjaro + KDE Wayland)

| Step | Command | Success Rate |
|------|---------|-------------|
| Delete compatdata/0/ | `rm -rf ~/.steam/steam/steamapps/compatdata/0/` | High — most common cause |
| Clear appcache | `rm -rf ~/.steam/steam/appcache/*` | Medium — fixes stale CEF cache |
| Toggle beta/stable | Steam → Settings → Interface | Medium — triggers CEF reinstall |
| `-no-cef-sandbox` | `steam -no-cef-sandbox` | Low — bypasses sandbox issues |

## Diagnostics

```bash
# Check steamloopback.host resolution
getent hosts steamloopback.host

# Check nsswitch.conf for mdns vs mdns_minimal
grep hosts /etc/nsswitch.conf

# Check systemd-resolved status
systemctl is-active systemd-resolved

# Check for bugged compatdata dir
ls -la ~/.steam/steam/steamapps/compatdata/0/
```

## Not Related

- General network connectivity (Steam connects and downloads fine)
- Game-specific issues (affects all games equally)
- DXVK/VKD3D (this is Steam client-side CEF, not game rendering)
