# Agentic LLM Tools — Free Resource Map

Comprehensive directory of free resources for agentic LLM development: frameworks, MCP, evaluation harnesses, training materials, and news. Updated June 2026.

---

## 1. Agent Frameworks / Harnesses

### Major / Popular

| Resource | URL | Notes |
|----------|-----|-------|
| OpenAI Agents SDK | `https://github.com/openai/openai-agents-python` | 27k★ — multi-agent orchestration by OpenAI. Very active. |
| LangGraph | `https://github.com/langchain-ai/langgraph` | 34k★ — stateful graph-based agents. Extremely active. |
| CrewAI | `https://github.com/crewAIInc/crewAI` | 53k★ — role-based multi-agent. Very active. |
| smolagents (HuggingFace) | `https://github.com/huggingface/smolagents` | 27.8k★ — agents that "think in code." |
| DSPy (Stanford) | `https://github.com/stanfordnlp/dspy` | 35k★ — compiler for LM programs. |
| AutoGen (Microsoft) | `https://github.com/microsoft/autogen` | 58.8k★ — **now in maintenance mode**. Community fork: AG2. |
| Agno (was PhiData) | `https://github.com/agno-ai/agno` | Full-stack, multi-modal, MCP support. |

### Lesser-Known but Quality

| Resource | URL | Notes |
|----------|-----|-------|
| Pydantic AI | `https://github.com/pydantic/pydantic-ai` | Type-safe agents from the Pydantic team. |
| Atomic Agents | `https://github.com/BrainBlend-AI/atomic-agents` | Modular, provider-agnostic agents. |
| Bee Agent Framework (IBM) | `https://github.com/i-am-bee/bee-agent-framework` | Solid MCP support, multi-modal. |
| Camel | `https://github.com/camel-ai/camel` | Research-focused role-playing agents. |
| Maestro | `https://github.com/Doriandarko/maestro` | Lightweight multi-agent. BSD licensed. |
| Google ADK | `https://github.com/google/adk-python` | Google's Agent Dev Kit — multi-agent, Gemini+A2A+MCP. |

---

## 2. Model Context Protocol (MCP)

### Official / Canonical

| Resource | URL | Notes |
|----------|-----|-------|
| MCP Specification & Docs | `https://modelcontextprotocol.io` | Full documentation, quickstart, SDK docs. |
| MCP Servers Repo | `https://github.com/modelcontextprotocol/servers` | 87k★ — 100+ pre-built servers. Extremely active. |
| Python SDK | `https://github.com/modelcontextprotocol/python-sdk` | Build MCP servers/clients in Python. |
| TypeScript SDK | `https://github.com/modelcontextprotocol/typescript-sdk` | Build MCP servers/clients in TS. |
| MCP Registry | `https://github.com/modelcontextprotocol/registry` | Registry of community MCP servers. |
| MCP Inspector | `https://modelcontextprotocol.io/docs/tools/inspector` | Debugging tool for MCP servers. |
| Anthropic Announcement | `https://www.anthropic.com/news/model-context-protocol` | Original announcement (Nov 2024). |

### Community / Discovery

| Resource | URL | Notes |
|----------|-----|-------|
| Awesome MCP Servers | `https://github.com/punkpeye/awesome-mcp-servers` | Curated community server list. |
| MCP.so | `https://mcp.so` | Search engine / directory. |
| Smithery | `https://smithery.ai` | One-click install registry. |
| GitHub MCP Marketplace | `https://github.com/marketplace?type=&category=mcp` | GitHub's MCP category. |

---

## 3. Evaluation & Observability Harnesses

| Resource | URL | Notes |
|----------|-----|-------|
| lm-evaluation-harness (EleutherAI) | `https://github.com/EleutherAI/lm-evaluation-harness` | **The standard.** 12.9k★, 400+ tasks. |
| Phoenix (Arize) | `https://github.com/Arize-AI/phoenix` | 10.1k★ — open-source traces & evals. Very active. |
| Weave (W&B) | `https://github.com/wandb/weave` | W&B's AI dev toolkit — tracing, eval, experiments. |
| LangSmith SDK | `https://github.com/langchain-ai/langsmith-sdk` | Tracing SDK (free tier for dev). |
| DeepEval | `https://github.com/confident-ai/deep-eval` | Unit testing — 40+ metrics. |
| RAGAS | `https://github.com/explodinggradients/ragas` | RAG pipeline evaluation. |
| OpenAI Evals | `https://github.com/openai/evals` | Official eval framework (community-maintained). |
| AgentBench | `https://github.com/THUDM/AgentBench` | Benchmark for LLM-as-agent evaluation. |

### Less Known

| Resource | URL | Notes |
|----------|-----|-------|
| Promptfoo | `https://github.com/promptfoo/promptfoo` | Open-source eval & red-teaming. |
| LangFuse | `https://github.com/langfuse/langfuse` | Open-source LLM observability, generous free tier. |
| AgentOps | `https://github.com/AgentOps-AI/agentops` | Agent monitoring, cost tracking, session replay. |
| LangWatch | `https://github.com/langwatch/langwatch` | Open-source LLM monitoring & eval. |
| OpenLIT | `https://github.com/openlit/openlit` | OpenTelemetry-based LLM monitoring. |
| Guardrails AI | `https://github.com/guardrails-ai/guardrails` | Output validation — structured, type-safe guards. |
| Instructor | `https://github.com/jxnl/instructor` | Structured output extraction for any LLM. |
| Outlines | `https://github.com/outlines-dev/outlines` | Constrained structured generation. |

---

## 4. Training & Learning (Free)

| Resource | URL | Notes |
|----------|-----|-------|
| HuggingFace Agents Course | `https://huggingface.co/learn/agents-course` | **Best free course** on building agents with smolagents. |
| DeepLearning.AI (Andrew Ng) | `https://www.deeplearning.ai/courses/` | "Building Systems with ChatGPT", "Multi AI Agent Systems" — free audit. |
| Stanford CS224N | `https://web.stanford.edu/class/cs224n/` | NLP with Deep Learning — free lectures. |
| Berkeley LLM Agents Course | `https://llmagents.berkeley.edu/` | Free university-level agent course (YouTube). |
| OpenAI Agents Quickstart | `https://platform.openai.com/docs/guides/agents` | Official quickstart. |
| Anthropic Agent Docs | `https://docs.anthropic.com/en/docs/build-with-claude/agents` | Comprehensive Claude agent guides. |
| LangChain Academy | `https://python.langchain.com/docs/tutorials/` | Free LangChain/LangGraph tutorials. |
| Fast.ai | `https://www.fast.ai/` | Practical Deep Learning — free. |

### YouTube Channels

- Sam Witteveen — LangGraph, agents, DSPy deep dives
- AI Engineer (LLMUniversity) — Agent frameworks, MCP comparisons
- Dave Ebbelaar / Dyl Bert — Practical agent tutorials
- Nicholas Renotte — Hands-on agent projects
- 1littlecoder — MCP-focused tutorials, local agents

---

## 5. News & Community

| Resource | URL | Notes |
|----------|-----|-------|
| The Batch (Andrew Ng) | `https://www.deeplearning.ai/the-batch/` | Weekly high-signal AI news. |
| Import AI (Jack Clark) | `https://importai.substack.com` | Long-running AI newsletter. |
| Latent Space | `https://latent.space` | Podcast + newsletter on developer AI tools. |
| AI Breakfast | `https://www.aibreakfast.com/` | Daily AI newsletter. |
| TLDR AI | `https://tldr.tech/ai` | Short daily AI roundup. |
| The Neuron | `https://www.theneuron.ai/newsletter` | Daily AI tools newsletter. |

### Communities

- `https://huggingface.co/spaces/agents-course/chat` — HF Agents community
- `https://discord.gg/langchain` — LangChain Discord (#agents, #langgraph)
- `https://reddit.com/r/LocalLLaMA` — Reddit, very active
- `https://reddit.com/r/AIAgents` — Agent-specific subreddit
- `https://discord.gg/anthropic` — Anthropic Discord (MCP, agents)

### Awesome Lists

- `https://github.com/e2b-dev/awesome-ai-agents` — 28.2k★, agent list (a bit stale)
- `https://github.com/punkpeye/awesome-mcp-servers` — MCP curated list
- `https://github.com/Shubhamsaboo/awesome-llm-apps` — LLM app patterns

---

## Quick-Start Path

1. HuggingFace Agents Course → `https://huggingface.co/learn/agents-course`
2. Try smolagents → `https://github.com/huggingface/smolagents`
3. Read MCP docs → `https://modelcontextprotocol.io`
4. Browse MCP Servers → `https://github.com/modelcontextprotocol/servers`
5. Use DeepEval or Phoenix → `https://github.com/confident-ai/deep-eval`
6. Follow The Batch → `https://www.deeplearning.ai/the-batch/`
7. Join r/LocalLLaMA + LangChain Discord
