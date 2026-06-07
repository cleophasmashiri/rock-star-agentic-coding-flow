# Autonomous Feature Factory — skeleton

<!--
  BRIEF
    Build a role-specialised, mostly-autonomous SDLC that runs locally on
    docker compose. A human gives a one-paragraph brief and approves at three
    gates; specialised agents do the rest. The centrepiece is THE ORCHESTRATOR
    (orchestrator/run.py) — a FULLY LOCAL service that walks the dependency DAG
    and dispatches the role agents, pausing only at the gates. Each agent runs
    via a pluggable CLI-delegate runner (goose / aider / openhands) over Ollama —
    no cloud, no proprietary SDK.

  DEFINITION OF DONE
    - `docker compose -f docker-compose.platform.yml up -d` brings up Gitea
      (+Actions runner), Wiki.js, Mattermost, Postgres, and Ollama.
    - The orchestrator loop is implemented: plan → (architect+stack gate) →
      dispatch READY issues in parallel worktrees → reviewer-agent (review +
      checklist verify) → merge gate → QA → delivery scorecard.
    - Each agent has LEAST-PRIVILEGE tools; reviewer-agent has no Edit/merge.
    - PreToolUse hooks + Gitea branch protection make merge-to-main / prod
      deploy impossible for an agent alone (the leash).
    - One real feature runs end to end and interrupts the human only at the
      three gates (plan · stack-ADR · merge).

  TODO (fill these in; compare to ../after/ when stuck)
    [ ] orchestrator/run.py        — the loop, the runner adapters, AND the approvals wiring
                                     (pull the brief from /features/next; open + poll /gates)
    [ ] approvals/app.py           — the human UI (FastAPI): submit form + pending-gates buttons
                                     + the /features and /gates endpoints the orchestrator calls
    [ ] guardrails/                — runner-agnostic leash (pre-receive hook +
                                     Gitea branch protection + sandbox); NO runner-specific hooks
    [ ] agents/*.md                — agent bodies (po, architect, designer, backend, ui, qa,
                                     reviewer, dev-manager)
    [ ] docker-compose.platform.yml— RUNNER_TOKEN, the ollama service, OLLAMA_MODEL
  Set OLLAMA_MODEL (no default) and AGENT_RUNNER (goose|aider|openhands).
  No cloud key required.
  Configs you ADAPT (already filled as examples): devs.yml, allowed-stack.yml,
  slas.yml, role-checklists/.
-->

See [`../README.md`](../README.md) for the full map and prerequisites.
