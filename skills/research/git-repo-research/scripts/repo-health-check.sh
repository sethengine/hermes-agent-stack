#!/usr/bin/env bash
# repo-health-check.sh
# Check one or more GitHub repos: fast metadata + health signals
# Usage: ./repo-health-check.sh owner/repo [owner/repo2 ...]
# Cache: results cached for 5 min in /tmp/repo-health-cache/

set -euo pipefail

CACHE_DIR=/tmp/repo-health-cache
mkdir -p "$CACHE_DIR"

check_repo() {
  local REPO="$1"
  local SLUG="${REPO//\//_}"
  local CACHE_FILE="$CACHE_DIR/$SLUG"

  # Use cache if fresh (< 5 min)
  local DATA
  if [ -f "$CACHE_FILE" ] && [ "$(($(date +%s) - $(stat -c %Y "$CACHE_FILE")))" -lt 300 ]; then
    DATA=$(cat "$CACHE_FILE")
  else
    DATA=$(curl -sf "https://api.github.com/repos/$REPO") || {
      echo "[$REPO] API error — may not exist or rate limited"
      return
    }
    echo "$DATA" > "$CACHE_FILE"
  fi

  echo "$DATA" | python3 -c "
import sys, json, datetime

d = json.load(sys.stdin)
if isinstance(d, dict) and d.get('message','') == 'Not Found':
    print(f'[$REPO] Not found')
    sys.exit(1)

stars    = d.get('stargazers_count', 0)
forks    = d.get('forks_count', 0)
lic      = d.get('license', {})
license_name = lic.get('spdx_id', 'None') if lic else 'None'
lang     = d.get('language', '-')
pushed   = d.get('pushed_at', '')[:10]
issues   = d.get('open_issues_count', 0)
topics   = ', '.join(d.get('topics', []))
desc     = d.get('description', '') or ''
archived = d.get('archived', False)

print(f'--- $REPO ---')
print(f'  Stars      {stars}')
print(f'  Forks      {forks}')
print(f'  License    {license_name}')
print(f'  Language   {lang}')
print(f'  Last Push  {pushed}')
print(f'  Issues     {issues}')
if topics: print(f'  Topics     {topics}')
if desc:   print(f'  About      {desc[:120]}')
if archived: print(f'  ** ARCHIVED **')

if pushed:
    try:
        now = datetime.datetime.now(datetime.timezone.utc)
        pd = datetime.datetime.fromisoformat(pushed.replace('Z', '+00:00'))
        days = (now - pd).days
        if days < 30:     tag = 'active'
        elif days < 90:   tag = 'moderate'
        elif days < 365:  tag = 'stale'
        else:             tag = 'abandoned'
        print(f'  Health     {tag} ({days}d since push)')
    except: pass
" 2>&1
}

for repo in "$@"; do
  check_repo "$repo"
  echo
done
