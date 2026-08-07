#!/bin/bash
set -e
REPO="${HOME}/.config/.src/hermes-stack"
GITHUB_REPO="sethengine/hermes-agent-stack"

cd "$REPO" || { echo "Repo not found at $REPO"; exit 1; }

TOKEN=$(python3 -c "
import re
with open('${HOME}/.hermes/config.yaml') as f:
    m = re.search(r'GITHUB_PERSONAL_ACCESS_TOKEN:\s*(\S+)', f.read())
    print(m.group(1) if m else '')
")

if [ -z "$TOKEN" ]; then
    echo "No GitHub token found in Hermes config."
    exit 1
fi

MODE="${1:-all}"

if [ "$MODE" = "configs" ]; then
    echo "Syncing configs..."
    mkdir -p configs/hermes configs/opencode configs/searxng
    cp ~/.hermes/config.yaml configs/hermes/default-config.yaml
    for f in ~/.hermes/profiles/*/config.yaml; do
        [ -f "$f" ] || continue
        name=$(basename "$(dirname "$f")")
        cp "$f" "configs/hermes/${name}-config.yaml"
    done
    cp ~/.config/opencode/opencode.json configs/opencode/opencode.json 2>/dev/null || true
    cp ~/searxng/config/settings.yml configs/searxng/settings.yml 2>/dev/null || true
fi

if [ "$MODE" = "all" ] || [ "$MODE" = "bridge" ]; then
    echo "Syncing bridge..."
    mkdir -p mcp-bridge
    cp ~/.local/bin/mcp-bridge mcp-bridge/mcp-bridge 2>/dev/null || true
    cp ~/.local/bin/searxng-mcp mcp-bridge/searxng-mcp 2>/dev/null || true
fi

if [ "$MODE" = "all" ] || [ "$MODE" = "skills" ]; then
    echo "Syncing skills..."
    rm -rf skills/
    mkdir -p skills
    for skill in ~/.hermes/skills/*/; do
        name=$(basename "$skill")
        [ -f "$skill/SKILL.md" ] && cp -r "$skill" "skills/$name/"
    done
    find ~/.hermes/skills -name "SKILL.md" -not -path "*/skills/*/skills/*" | while read f; do
        dir=$(dirname "$f")
        name=$(basename "$dir")
        if [ ! -d "skills/$name" ]; then
            cp -r "$dir" "skills/$name" 2>/dev/null || true
        fi
    done
fi

if [ "$MODE" = "all" ] || [ "$MODE" = "sessions" ]; then
    echo "Syncing sessions..."
    mkdir -p sessions
    ls -t ~/.hermes/sessions/session_*.json 2>/dev/null | head -5 | while read f; do
        cp "$f" sessions/ 2>/dev/null || true
    done
fi

echo "Redacting secrets..."
find . -name "*.yaml" -o -name "*.json" | while read f; do
    python3 -c "
import re
with open('$f') as fp: c = fp.read()
c = re.sub(r'(GITHUB_PERSONAL_ACCESS_TOKEN[=: ]+)[a-zA-Z0-9_.-]+', r'\1«redacted»', c)
c = re.sub(r'\"GITHUB_PERSONAL_ACCESS_TOKEN\"\s*:\s*\"[^\"]*\"', '\"GITHUB_PERSONAL_ACCESS_TOKEN\": \"«redacted»\"', c)
c = re.sub(r'(BRAVE_API_KEY[=: ]+)[a-zA-Z0-9_.-]+', r'\1«redacted»', c)
c = re.sub(r'(OPENAI_API_KEY[=: ]+)[a-zA-Z0-9_.-]+', r'\1«redacted»', c)
c = re.sub(r'(AUTH_TOKEN[=: ]+)[a-zA-Z0-9_.-]+', r'\1«redacted»', c)
with open('$f', 'w') as fp: fp.write(c)
" 2>/dev/null
done

TIMESTAMP=$(date "+%Y-%m-%d %H:%M")
git add -A
git diff --cached --quiet && echo "No changes to commit." && exit 0

git commit -m "sync: $TIMESTAMP — $MODE" --quiet
git remote set-url origin "https://sethengine:${TOKEN}@github.com/${GITHUB_REPO}.git" 2>/dev/null
git push origin master 2>&1 | tail -2

echo "Synced to github.com/${GITHUB_REPO}"
