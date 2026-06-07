# agentic-coding-flow

A standalone, **fully-local** *autonomous feature factory* — role-specialised agents run the software lifecycle and a human is the gate-keeper. Runs entirely on `docker compose` (Gitea, Wiki.js, Mattermost, Postgres, **Ollama**, a FastAPI approvals UI, and the orchestrator). No cloud, no vendor lock-in.

📖 **Start here:** [README-rockstar-agentic-coder.md](README-rockstar-agentic-coder.md) — the full guide + walkthrough.

- Code: [`before/`](before/) (skeleton) · [`after/`](after/) (reference)
- Centrepiece: the orchestrator — [`after/orchestrator/run.py`](after/orchestrator/run.py)
- Human UI: the FastAPI **approvals** app at `http://localhost:8080`
