# Autonomous Feature Factory — reference solution

Complete, runnable-as-reference version of the skeleton in [`../before/`](../before/). The brief and Definition-of-Done are in [`../before/README.md`](../before/README.md); this folder is the answer key.

The centrepiece is [`orchestrator/run.py`](orchestrator/run.py) — a **fully local** orchestrator: deterministic control-flow (plan → architect+stack gate → dispatch the DAG in parallel worktrees → `reviewer-agent` (review **and** checklist verify) → merge gate → QA → delivery scorecard) that runs each role agent through a **pluggable CLI-delegate runner** over **Ollama**. No cloud, no proprietary SDK.

## How the agents run (pluggable runner)

`run.py` defines a small `AgentRunner` interface and selects an adapter via `AGENT_RUNNER` (`goose` | `aider` | `openhands`). Each adapter shells out to that local, Ollama-capable agent CLI, feeding the role's system prompt (`agents/<name>.md`) + the task, in the role's worktree, pointed at `OLLAMA_BASE_URL`/`OLLAMA_MODEL`. Swapping the runner does **not** change the orchestration. The model is **configurable-only** — set `OLLAMA_MODEL` (no default).

> **Least-privilege caveat:** a CLI-delegate runner enforces per-agent tool limits *less strictly* than an SDK `tools:` allowlist — so the leash is **runner-agnostic**, in the platform, not the agent. See [`guardrails/`](guardrails/): Gitea **branch protection** + a server-side **`pre-receive`** hook + a **sandboxed runner** with scoped creds. It does **not** rely on a runner's client-side hooks.

## Run it (local)

```bash
export GITEA_TOKEN=... WIKI_TOKEN=... MM_TOKEN=... RUNNER_TOKEN=...        # no cloud key needed
docker compose -f docker-compose.platform.yml up -d                        # Gitea, Wiki.js, Mattermost, Postgres, Ollama, approvals
docker compose -f docker-compose.platform.yml exec ollama ollama pull qwen2.5-coder:14b   # pick + pull a model
# protect `main` in Gitea (PR + green CI + reviewer PASS required), then:
# 1. SUBMIT a feature in the approvals UI →  http://localhost:8080
# 2. start a worker for it:
OLLAMA_MODEL=qwen2.5-coder:14b AGENT_RUNNER=goose \
  docker compose -f docker-compose.platform.yml run --rm orchestrator
```

## How humans drive it (the UI)

- **Submit a feature:** the **approvals UI** (FastAPI) at `http://localhost:8080` — a form that queues the brief; the orchestrator pulls it (`GET /features/next`). *(Or skip the UI: pass `-e CC_BRIEF="…"`.)*
- **Approve GATE 1 (plan) & GATE 2 (tech-stack ADR):** the orchestrator opens a gate in the approvals UI (`POST /gates`) and **blocks** (`human_gate` polls `GET /gates/{id}`); you click **Approve / Reject** on the page.
- **Approve GATE 3 (merge):** in **Gitea** — Approve + Merge on the PR, enforced by branch protection. (The approvals page just reminds you.)

`diff -r ../before ../after` shows everything you had to fill in: the orchestrator loop + runner adapters + the approvals wiring, the `guardrails/` leash, the agent bodies, and the approvals `app.py`.

## Notes

- **Model:** no hard default — set `OLLAMA_MODEL` (suggestions: `qwen2.5-coder:14b` for stronger tool-use, `llama3.1:8b` for lighter hardware). Tool-calling quality varies by model; lean on the gates (CI, `reviewer-agent`, QA) to catch what a small local model misses.
- **Runner:** `AGENT_RUNNER=goose` by default; `aider` (git-native edit/test loop) and `openhands` (stub) are the alternatives — all talk to Ollama.
- This project goes **fully local**; an agent SDK is an equally valid orchestrator runtime. Same role/gate/least-privilege design either way — only the agent-execution layer differs.
- All eight role agents are defined in `agents/` — `po`, `architect`, `designer`, `backend`, `ui`, `qa`, `reviewer`, and `dev-manager` — each least-privilege. The five task-producing roles (`backend`, `ui`, `qa`, `design`, `product`) also have a verifiable checklist (`team/role-checklists/<role>.md`).
- The **`dev-manager-agent`** is the human Dev Manager's assistant: it prepares the delivery report (🎯 impact · ✅ quality · ⚡ time), surfaces a ranked "decisions for you" list, and handles delegated low-risk chores (digests, draft nudges, stale-issue triage) — but **recommends/drafts only**; approving gates, merging, deploying, and contested calls stay with the human. (No DoD checklist — it isn't in the merge path; it serves the manager, not a PR.)
