# Hermes & OpenCode CLI — Ready-to-Use Agent Tooling

Community-curated resources for Hermes Agent and OpenCode CLI: skills, MCP servers, workflows, and config tweaks. All sources are community-driven (GitHub repos, awesome lists, Discord communities), not big-company websites. Updated June 2026.

---

## 1. Ready-to-Use Skills (Drop-in `.md` files)

| Repository | Description |
|---|---|
| `seaworld008/Commonly-used-high-value-skills` | 41★, 111 commits. Has a dedicated `openclaw-skills/` directory with real Hermes/OpenClaw skill files. CI pipeline auto-maintains them. Updated daily. |
| `Martin-Hausleitner/martins-awesome-skills` | 1★, 64 commits. "Public-safe Hermes and OpenClaw agent skills with Telegram approval workflows." Has `skills/` + `config-templates/` directories with ready-to-use skill configs. |
| `phamduchuong517-hub/hermes-self-evolution` | 1★, v4.1.0. "7 skills for self-evolving agents" — remember experiences, correct behavior, optimize costs. MIT license, zero dependencies. Has a `skills/` directory. |
| `AashmanShukla3223/Antigravity-and-OpenCode-CLI-Prompts-and-Skills` | 2★, 278 commits. "High-efficiency AGENTS.md and SKILL.md recipes for OpenCode CLI." Zero-token-waste optimized. Updated daily. |
| `SHENG5411/grimoire-of-tools` | New. "Multi-platform AI assistant skills & workflows" framework for OpenCode, Claude Code, Codex, Cursor. CI-driven, updated every few minutes. |
| `nexu-io/open-design` | **62.3k★**, 2,136 commits, 824 branches. 259+ skills for 17+ CLIs (OpenCode, Hermes, Claude Code, Codex, etc.). Per-agent MCP installer — plugin marketplace for 14+ agent platforms. Updated 38m ago. |

---

## 2. MCP Server Registries (Drop-in Configs)

| Repository | What It Is |
|---|---|
| `punkpeye/awesome-mcp-servers` | The definitive community directory. Hundreds of categorized MCP servers with descriptions and links. |
| `punkpeye/awesome-mcp-devtools` | 459★. Testing utilities, SDKs, debugging tools for MCP integration. |
| `rohitg00/awesome-devops-mcp-servers` | 996★. DevOps-focused MCP servers — cloud, k8s, infrastructure tooling. |
| `JSONbored/awesome-claude` ("HeyClaude") | 262★, 944 commits. Full catalog of MCP servers + skills + hooks + rules + jobs. npm MCP package + Raycast feeds. Submission gate = quality controlled. |
| `toolsdk-ai/toolsdk-mcp-registry` | 176★. Structured JSON database of every MCP server with configurations. Machine-readable. |
| `Smithery` — `https://smithery.ai` | Web UI registry, one-click install MCP servers. |
| `mcp.so` — `https://mcp.so` | Search engine for MCP servers by name/description/keyword. |

### Individual MCP Servers Worth Knowing

| Repository | What It Does |
|---|---|
| `JorG18/agentcrawl` | Self-hosted web scraping + Markdown extraction as an MCP server. Dockerized, Playwright-based. Tagged `hermes-agent`. |
| `grossiweb/ToolRoute` | Intelligent MCP routing layer — recommends best MCP server + LLM for any task, scored on 132+ benchmarks. Useful as a meta-MCP. |

---

## 3. Pre-Built Workflows

| Repository | What It Does |
|---|---|
| `round-comfortfood117/codex-workflows` | Automates Codex workflows with subagents for requirements, design, implementation, tests, traceable commits. Outputs `openclaw-skills`. |
| `cenglin123/dynamic-workflow-skill` | Agent-agnostic multi-agent orchestration workflow. For frameworks without native workflow runtimes. |
| `niallyoung/agentic-engineers` | "Orchestrator + Team of Engineers + SDLC-CICD Workflow." Claims ~50% token reduction. |
| `RBraga01/a-team` | "Universal multi-agent infrastructure" — 25 specialist agents, 16 enforced workflows, lead orchestrator. Uses OpenCode CLI. |
| `Interstellar-code/hermes-switchui` | **Hermes Switch UI** — full web frontend for Hermes Agent (chat, terminal, memory, skills, MCP, workflows). Has `/.archon/workflows/`, `/.claude/`, `/.omc/` directories. v2.3.34, 2,375 commits. Deployable via Docker all-in-one. Updated every few minutes. |

---

## 4. Config Tweaks & Ecosystem

| Repository | What It Is |
|---|---|
| `LiHongwei-cn/lihongwei-cn` ("MUNDO") | 8★. **1,208 skills**, 25 capability modules, self-evolving, collective consciousness. Runs on GitHub Actions 24/7. Tagged `hermes-agent`, `claude-skills`. |
| `bdhhsx/hermes-companion` | "Hermes Agent 2026 — AI Assistant That Learns & Adapts." Open source Hermes companion. Tagged `openclaw`, `hermes-agent`. |
| `Interstellar-code/hermes-switchui` | (See above — spans workflows + ecosystem) |
| `sifted-network/sifted-awesome-ai-agents` | 7★, **5,006 commits**. Auto-updated daily — ranking of most-starred AI agent repos on GitHub. Generates CSV data daily, VitePress website, feeds from marktechpost. The living replacement for stale awesome-lists. Updated every hour. |

---

## 5. Community Hubs for Hermes/OpenCode News

| Place | What's There |
|---|---|
| GitHub Topics: `hermes-agent` — `https://github.com/topics/hermes-agent?o=desc&s=updated` | **1,318 repos** tagged hermes-agent, sorted by recency. New tools appear daily. |
| GitHub Topics: `mcp` — `https://github.com/topics/mcp?o=desc&s=stars` | All MCP-related repos sorted by stars. |
| GitHub Search: `opencode+skills` — `https://github.com/search?q=opencode+skills&type=repositories&s=updated&o=desc` | New OpenCode skill repos appear daily. |
| GitHub Search: `openclaw-skills` — `https://github.com/search?q=openclaw-skills&type=repositories&s=updated&o=desc` | Direct hit for repos with openclaw-skills directories. |
| Reddit `r/AI_Agents` — `https://reddit.com/r/AI_Agents` | People post new skills, MCP servers, Hermes/OpenCode tweaks. |
| Reddit `r/LocalLLaMA` — `https://reddit.com/r/LocalLLaMA` | Agent-tooling discussed and tested before mainstream. |
| Hacker News (Algolia) — `https://hn.algolia.com/?q=agent+skill+MCP&sort=byDate&type=story&dateRange=lastMonth` | Show HN posts for new agent platforms appear constantly. |

---

## Methodology for Discovery

When asked to find "ready-to-use" resources for a specific agent platform:

1. **Start with GitHub Topics** — `https://github.com/topics/{platform-name}?o=desc&s=updated` surfaces every repo the community has tagged for that platform.
2. **Filter by directory names** — repos containing `skills/`, `openclaw-skills/`, `config-templates/`, `workflows/` directories are more likely to be ready-to-use.
3. **Check activity signals** — last commit date, star count, and issue responsiveness tell you if a repo is maintained.
4. **Cross-reference with awesome lists** — `punkpeye/awesome-mcp-servers` or `JSONbored/awesome-claude` act as quality filters.
5. **Verify with raw content extraction** — use `browser_console(expression="document.body.innerText.substring(0, 10000)")` on raw READMEs to confirm the repo actually contains usable artifacts (not just links or stubs).
