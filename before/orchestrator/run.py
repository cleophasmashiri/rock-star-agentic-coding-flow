#!/usr/bin/env python3
"""THE ORCHESTRATOR (skeleton).

FULLY LOCAL: every role agent runs on a local Ollama model via a pluggable
CLI-delegate runner (goose / aider / openhands). No cloud, no Anthropic SDK.

Fill in the TODOs. The full reference is in ../../after/orchestrator/run.py.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Protocol

# --- local LLM + runner config (model is configurable-only — no hard default) ---
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434/v1")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "")
RUNNER = os.environ.get("AGENT_RUNNER", "goose")  # goose | aider | openhands
APPROVALS_URL = os.environ.get("APPROVALS_URL", "http://approvals:8080")  # the human UI (FastAPI)
# TODO: wire the human surface to the approvals UI (see ../../after/orchestrator/run.py):
#   - brief: os.environ.get("CC_BRIEF") or GET {APPROVALS_URL}/features/next
#   - human_gate: POST {APPROVALS_URL}/gates then poll GET /gates/{id} until approved/rejected
# TODO: fail fast if OLLAMA_MODEL is empty, with a helpful message + suggestions
#       (e.g. qwen2.5-coder:14b, llama3.1:8b).

AgentResult = dict[str, Any]


# --- pluggable runner -------------------------------------------------------
class AgentRunner(Protocol):
    # Run one role agent's tool-using loop on the local model, in `cwd`.
    def run(self, agent: str, payload: dict, cwd: str) -> AgentResult: ...


# TODO: implement adapters that shell out (subprocess) to a local, Ollama-capable
#       agent CLI, feeding the role system prompt (agents/<agent>.md) + the
#       task, in `cwd`, pointed at OLLAMA_BASE_URL / OLLAMA_MODEL. See ../../after/.
class GooseRunner:
    def run(self, agent: str, payload: dict, cwd: str) -> AgentResult:
        raise NotImplementedError("TODO: goose adapter")


class AiderRunner:
    def run(self, agent: str, payload: dict, cwd: str) -> AgentResult:
        raise NotImplementedError("TODO: aider adapter")


class OpenHandsRunner:
    def run(self, agent: str, payload: dict, cwd: str) -> AgentResult:
        raise NotImplementedError("TODO: openhands adapter")


RUNNERS: dict[str, AgentRunner] = {"goose": GooseRunner(), "aider": AiderRunner(), "openhands": OpenHandsRunner()}
runner = RUNNERS[RUNNER]


# --- thin wrappers ----------------------------------------------------------
class Budget:
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


# --- the run (TODO: implement the loop — see ../../after/) -------------------
def main() -> None:
    brief = os.environ.get("CC_BRIEF")  # TODO: or pull from {APPROVALS_URL}/features/next  # noqa: F841
    # TODO 1: po-agent decompose → issues + deps + Wiki doc + gate=impact + time target.
    # TODO 2: GATE 1 — approve plan.
    # TODO 3: if a stack decision is needed → architect-agent → GATE 2 (approve ADR).
    # TODO 4: while not dag_all_closed(dag): dispatch READY issues in worktrees;
    #         for each PR run reviewer-agent (review + verify); if CI green AND PASS →
    #         GATE 3 (merge) then merge. Honour the budget cap.
    # TODO 5: qa-agent acceptance, then dispatch the dev-manager-agent to prepare the report +
    #         "decisions for you" digest for the HUMAN Dev Manager (impact · quality · time).
    raise SystemExit("TODO: implement the orchestrator loop")


# --- helpers ----------------------------------------------------------------
def system_prompt_for(name: str) -> str:
    return Path(f"agents/{name}.md").read_text()


def checklist_for(role: str) -> str:
    return Path(f"team/role-checklists/{role}.md").read_text()


# TODO: implement against your Gitea/Mattermost MCP —
# worktree_for, open_prs, ci_green, merge_pr, notify_mattermost, wait_for_approval,
# dag_all_closed, dag_ready_issues, run_delivery_scorecard.

if __name__ == "__main__":
    main()
