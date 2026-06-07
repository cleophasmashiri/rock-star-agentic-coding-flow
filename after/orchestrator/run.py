#!/usr/bin/env python3
"""THE ORCHESTRATOR (reference solution).

FULLY LOCAL: every role agent runs on a local Ollama model via a pluggable
CLI-delegate runner (goose / aider / openhands). No cloud, no proprietary SDK.

The orchestrator itself is plain deterministic code — it dispatches agents and
enforces the three human gates. The *agent loop* (tool use against the model) is
provided by whichever local runner you select.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Protocol

import httpx

# --- local LLM + runner config (model is configurable-only — no hard default) ---
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434/v1")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "")
RUNNER = os.environ.get("AGENT_RUNNER", "goose")  # goose | aider | openhands
APPROVALS_URL = os.environ.get("APPROVALS_URL", "http://approvals:8080")  # the human UI (FastAPI)
_feature_id = 0  # set when the brief is pulled from the approvals UI
if not OLLAMA_MODEL:
    raise SystemExit(
        "OLLAMA_MODEL is required (no default). Pull one first, e.g.\n"
        "  docker compose exec ollama ollama pull qwen2.5-coder:14b\n"
        "then set OLLAMA_MODEL=qwen2.5-coder:14b (or llama3.1:8b, etc.)."
    )

AgentResult = dict[str, Any]


# --- pluggable runner -------------------------------------------------------
# Swapping the runner does NOT change the orchestration below.
class AgentRunner(Protocol):
    # Run one role agent's tool-using loop on the local model, in `cwd`.
    def run(self, agent: str, payload: dict, cwd: str) -> AgentResult: ...


def _agent_file(name: str) -> str:
    return f"agents/{name}.md"


def _system_prompt(name: str) -> str:
    return Path(_agent_file(name)).read_text()


def _task_text(payload: dict) -> str:
    return f"## Task\n{json.dumps(payload)}\n\nReturn a JSON result on the last line."


def _parse_result(stdout: str) -> AgentResult:
    for line in reversed(stdout.strip().splitlines()):
        if line.strip().startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                break
    return {"pass": False}


# NOTE: the CLI flags below are ILLUSTRATIVE — check your runner's version docs.
# Each adapter feeds the role system prompt (agents/<agent>.md) + the task
# to a tool-capable local agent pointed at Ollama, then parses its JSON result.
class GooseRunner:  # block's goose — local-first, MCP-capable, Ollama provider
    def run(self, agent: str, payload: dict, cwd: str) -> AgentResult:
        out = subprocess.run(
            ["goose", "run", "--quiet", "--provider", "ollama", "--model", OLLAMA_MODEL,
             "--with-extension", "developer",            # shell/edit tools
             "--system", _system_prompt(agent), "--text", _task_text(payload)],
            cwd=cwd, env={**os.environ, "OLLAMA_HOST": OLLAMA_BASE_URL},
            capture_output=True, text=True, check=True,
        ).stdout
        return _parse_result(out)


class AiderRunner:  # git-native edit→test loop; great for the code agents
    def run(self, agent: str, payload: dict, cwd: str) -> AgentResult:
        out = subprocess.run(
            ["aider", "--model", f"ollama/{OLLAMA_MODEL}", "--no-auto-commit", "--yes",
             "--read", _agent_file(agent),               # role system prompt as read-only context
             "--message", _task_text(payload)],
            cwd=cwd, env={**os.environ, "OLLAMA_API_BASE": OLLAMA_BASE_URL},
            capture_output=True, text=True, check=True,
        ).stdout
        return _parse_result(out)


class OpenHandsRunner:  # heavier sandboxed dev agent — stub
    def run(self, agent: str, payload: dict, cwd: str) -> AgentResult:
        # TODO: invoke OpenHands headless (LLM_BASE_URL=OLLAMA_BASE_URL, LLM_MODEL=OLLAMA_MODEL),
        #       feeding _system_prompt(agent) + _task_text(payload) in `cwd`.
        raise RuntimeError("openhands adapter not wired in this reference — use goose or aider")


RUNNERS: dict[str, AgentRunner] = {"goose": GooseRunner(), "aider": AiderRunner(), "openhands": OpenHandsRunner()}


def select_runner(name: str) -> AgentRunner:
    if name not in RUNNERS:
        raise SystemExit(f"unknown AGENT_RUNNER '{name}' (expected: {' | '.join(RUNNERS)})")
    return RUNNERS[name]


runner = select_runner(RUNNER)


# --- thin wrappers ----------------------------------------------------------
class Budget:  # pause, never loop forever
    def __init__(self, max_runs: int) -> None:
        self.max, self.n = max_runs, 0

    def charge(self) -> None:
        self.n += 1

    def exceeded(self) -> bool:
        return self.n >= self.max


budget = Budget(max_runs=60)


def run_agent(name: str, payload: dict, cwd: str | None = None) -> AgentResult:
    budget.charge()
    return runner.run(name, payload, cwd or os.getcwd())


def run_agent_in_worktree(name: str, payload: dict, branch: str) -> AgentResult:
    return run_agent(name, payload, worktree_for(branch))  # git worktree per branch


def human_gate(name: str, payload: Any) -> None:
    """Open a gate in the approvals UI (FastAPI) and block until a human decides there.
    (GATE 3 'merge' is also enforced in Gitea by branch protection.)"""
    gid = httpx.post(f"{APPROVALS_URL}/gates",
                     data={"feature": _feature_id, "name": name,
                           "payload": json.dumps(payload)[:500]}).json()["gate"]
    notify_mattermost(f"GATE {name}: approve at {APPROVALS_URL}/ (gate {gid})", payload)
    while True:                                              # poll the approvals UI for the decision
        status = httpx.get(f"{APPROVALS_URL}/gates/{gid}").json()["status"]
        if status == "approved":
            return
        if status == "rejected":
            raise SystemExit(f"gate '{name}' was rejected by a human — halting")
        time.sleep(5)


# --- the run (deterministic — unchanged by runner choice) -------------------
def main() -> None:
    brief = os.environ.get("CC_BRIEF") or _pull_brief()   # CLI env var, or pull from the approvals UI

    dag = run_agent("po-agent", {"brief": brief})        # issues + deps + Wiki doc + gate=impact + time target
    human_gate("approve-plan", dag)                      # GATE 1 — worth building? time target realistic?

    if dag.get("needsStackDecision"):
        adr = run_agent("architect-agent", {"dag": dag})  # cost · perf · landscape · allowlist → ADR
        human_gate("approve-stack", adr)                 # GATE 2 — approve the tech-stack ADR

    while not dag_all_closed(dag):
        for issue in dag_ready_issues(dag):              # deps closed, unassigned
            run_agent_in_worktree(agent_for(issue["role"]), {"issue": issue}, f"feat/{issue['key']}")

        for pr in open_prs():
            rv = run_agent("reviewer-agent", {"pr": pr, "checklist": checklist_for(pr["role"])})  # review + verify
            if ci_green(pr) and rv.get("pass"):          # pass = no 🔴 review + all checklist items ✓
                human_gate("merge", pr)                  # GATE 3 — human approves merge → sets CC_GATE_APPROVED
                merge_pr(pr)

        if budget.exceeded():
            notify_mattermost("cost cap hit — pausing", {})
            break

    run_agent("qa-agent", {"epic": dag["epic"]})         # acceptance on the merged feature
    # The dev-manager-agent prepares the report + the "decisions for you" digest for the HUMAN
    # Dev Manager — it recommends/drafts, the human decides. (Reads run_delivery_scorecard data.)
    run_agent("dev-manager-agent", {"epic": dag["epic"]})  # 🎯 impact · ✅ quality · ⚡ time + escalations


# --- helpers (wire to your Gitea/Mattermost MCP or REST) --------------------
def agent_for(role: str) -> str:
    return {"backend": "backend-agent", "ui": "ui-agent", "design": "designer-agent", "qa": "qa-agent"}[role]


def checklist_for(role: str) -> str:
    return Path(f"team/role-checklists/{role}.md").read_text()


def worktree_for(branch: str) -> str:  # git worktree add ../wt/<branch> <branch>
    return f"../wt/{branch}"


def open_prs() -> list[dict]: return []                  # gitea: list open PRs for the epic
def ci_green(pr: dict) -> bool: return pr.get("ci") == "success"
def merge_pr(pr: dict) -> None: ...                      # gitea merge — needs CC_GATE_APPROVED + branch protection
def _pull_brief() -> str:                                # pull the next queued feature from the approvals UI
    global _feature_id
    f = httpx.get(f"{APPROVALS_URL}/features/next").json()
    _feature_id = f["id"]
    return f["brief"]
def notify_mattermost(msg: str, payload: Any) -> None: ...    # optional chat ping (mattermost REST)
def dag_all_closed(dag: dict) -> bool: ...               # gitea: all child issues closed
def dag_ready_issues(dag: dict) -> list[dict]: return []  # deps closed, unassigned
def run_delivery_scorecard(epic: Any) -> dict: ...       # deterministic scorecard data the dev-manager-agent reads (cc-audit join)


if __name__ == "__main__":
    main()

# Least-privilege caveat: a CLI-delegate runner enforces per-agent tool limits
# LESS strictly than a tools: allowlist. The leash here is runner-agnostic — see
# guardrails/: Gitea branch protection + the pre-receive hook + a sandboxed runner
# with scoped creds. It does NOT depend on a runner's client-side hooks.
