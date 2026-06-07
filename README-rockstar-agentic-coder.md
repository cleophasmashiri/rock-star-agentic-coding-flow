# The Rockstar Agentic Coder — an Autonomous Feature Factory 🎯⚡✅

A role-specialised, mostly-autonomous software-delivery flow that runs **entirely locally** on `docker compose` — no cloud, no vendor lock-in. The runnable code is in [`before/`](before/) (skeleton) and [`after/`](after/) (reference); the centrepiece is the orchestrator, [`after/orchestrator/run.py`](after/orchestrator/run.py).

> Adapted from the *Claude Code Rock-Star* playbook's "Autonomous Feature Factory" capstone. Inline `(Ch N)` and "Capstone 1/2" references point to chapters in that playbook — you don't need them to use this repo.

## How to use

1. Read the brief in [`before/README.md`](before/README.md); fill in the skeletons.
2. Stuck? Compare against [`after/`](after/) — the complete reference.
3. `diff -r before after` is the spoiler.

## Run it (fully local)

```bash
export GITEA_TOKEN=... WIKI_TOKEN=... MM_TOKEN=... RUNNER_TOKEN=...      # no cloud key needed
docker compose -f after/docker-compose.platform.yml up -d               # Gitea, Wiki.js, Mattermost, Postgres, Ollama, approvals
docker compose -f after/docker-compose.platform.yml exec ollama ollama pull qwen2.5-coder:14b
# submit a feature in the approvals UI → http://localhost:8080, then start a worker:
OLLAMA_MODEL=qwen2.5-coder:14b docker compose -f after/docker-compose.platform.yml run --rm orchestrator
```

Humans **submit a feature** and **approve the plan/stack gates** in the FastAPI **approvals UI** (`:8080`); the **merge gate** is approved in **Gitea** (branch protection enforces it).

## Walkthrough

Here, **specialised agents run the lifecycle** and the human is a *gate-keeper* who approves at a few decisive moments and otherwise watches. The roles — Product Owner, UI Designer, Back End Developer, UI Developer, QA, **plus an Architect who owns the tech stack** — are each a **custom agent** with its own scoped tools and system prompt, dispatched by an **orchestrator** that reads the dependency graph and drives the work to green with minimal human interaction.

Crucially, the whole platform runs **on your laptop with `docker compose`** — all open-source, **no Jira, no Confluence, no GitHub, no Figma SaaS**. You can run, inspect, and tear down the entire feature factory locally.

> **Minimal human interaction ≠ no human.** Autonomy is bounded by *least privilege* (each agent has only the tools its role needs) and a handful of *hard human gates* (approve the plan, approve the tech-stack ADR, approve the merge) enforced in the platform — Gitea branch protection + a server-side hook + a sandboxed runner (Recipe 0.3), not a single vendor's hook system. An agent that can't merge to `main` or deploy to prod can run wide open in between. Build the leash before you let it run.

> 📦 **What this repo ships.** A **Python orchestrator** ([`after/orchestrator/run.py`](after/orchestrator/run.py)) driving a **pluggable CLI runner** (`goose` / `aider` / `openhands`) over a local **Ollama** model — no cloud, no Anthropic SDK. It is **tool-neutral**: agents live in `agents/*.md`, config in `team/`, the leash in `guardrails/`, and a small **FastAPI `approvals/` UI** (`:8080`) is where a human submits a feature and approves the plan/stack gates (the merge gate stays in Gitea). The recipes below teach the *pattern* and use Claude-Code surfaces (subagents, hooks, the Agent SDK) as the default illustration; where this repo diverges to stay vendor-neutral, it's called out inline.

### Guided by impact, quality, and time — and tracked

A fast swarm that ships the wrong thing, or ships it buggy, hasn't delivered. So the factory is judged on the three axes the whole playbook is built around — and every one is a **logged number, not a vibe**:

| Axis | What it means for a feature | Set at | Tracked by |
|------|------------------------------|--------|------------|
| 🎯 **Impact** | the outcome it should move — a metric + target, not "shipped" | plan (`po-agent`) → **GATE 1** | an `impact` record on the epic: hypothesis + success metric + baseline → **measured after release** |
| ✅ **Quality** | every role's Definition-of-Done gate passed, independently verified | role checklists + the `reviewer-agent` (review + verify) | `[[cc-audit]]` gate pass/fail + bugs filed + rework loops |
| ⚡ **Time** | cycle time against a target the team set | plan (a cycle-time budget) | `[[cc-audit]]` durations + cycle time vs target |

The first two human gates exist *because* of these axes: GATE 1 weighs **impact** (worth building?) and the **time target** (realistic?); GATE 2 weighs **architecture** cost/perf. The `/delivery-scorecard` (Recipe 3.3) rolls all three up per feature, so "did we deliver — on impact, on quality, on time?" is answered with data.

### The local platform (all OSS, all `docker compose`)

| Concern | Typical SaaS | This stack (local OSS) | Runs in Docker |
|---------|-------------------|------------------------|----------------|
| Git + PRs + **CI** | GitHub | **Gitea** + Gitea Actions runner | ✅ |
| Issues / board (epics, tasks) | Jira | **Gitea Issues + Projects** (Kanban) | ✅ |
| Docs / feature spec | Confluence | **Wiki.js** | ✅ |
| Chat / notifications | Teams / Slack | **Mattermost** | ✅ |
| Design | Figma | **Penpot** (optional, heavier) | ✅ |
| App DB | Postgres | **Postgres** | ✅ |
| **LLM runtime** | Claude API (cloud) | **Ollama** serving a local model (e.g. `qwen2.5-coder`, `llama3.1`) | ✅ |
| **Agent runner** | Claude Code | **Claude Code** (best quality) *or* a local-LLM alt — **Aider / goose / OpenHands / Continue** pointed at Ollama | ✅ |
| The orchestrator | (humans) | **Python service** — a pluggable CLI runner over Ollama, *or* the Agent SDK (Ch 34) | ✅ |
| **Human UI** | (Jira/Teams) | **FastAPI `approvals/` app** (`:8080`) — submit a feature + approve the plan/stack gates; merge stays in Gitea | ✅ |

Swap any of these for a sibling you prefer (Forgejo for Gitea, OpenProject/Plane for the tracker, Outline/BookStack for the wiki, Rocket.Chat for chat) — the agent contracts don't change.

**On running the LLM locally.** The whole point of this stack is *no cloud dependency*, so the model runs in Docker too: **Ollama** serves an open coding model on `:11434`, and the agents talk to it. Two honest caveats: (1) Claude Code itself targets Claude models (via the API, Bedrock, or Vertex — Ch 33), so a *fully local* swarm swaps the agent runner for an open-source, Ollama-friendly one (**Aider**, **goose**, **OpenHands**, **Continue**) while keeping the same role/least-privilege/gate design; (2) local models are smaller — expect to **lean harder on the gates** (CI, reviewer-agent, QA acceptance) to catch what a 7-13B model misses. A common hybrid: local Ollama for the high-volume implement steps, Claude for the reviewer/QA judgement calls. Point any runner at the local model with `OPENAI_BASE_URL=http://ollama:11434/v1` (Ollama's OpenAI-compatible API) or the runner's native Ollama setting.

### The agent roster (one specialised agent per role)

Each lives as a `<name>.md` definition with a **least-privilege tool list** and a role system prompt — in `.claude/agents/` if Claude Code is the runner (Ch 7), or tool-neutral `agents/` if a local runner reads them (as the companion project does). Most reuse the *workflow* from Capstone 2's skills — now embedded in an agent that runs headless.

| Agent | Role | Tools (least privilege) | May NOT |
|-------|------------------|--------------------------|---------|
| `orchestrator-agent` | Coordinator / dispatcher — *the orchestrator program itself* (`run.py`), not an LLM agent (Recipe 2.1) | Task (dispatch), gitea, mattermost | edit code |
| `po-agent` | Product Owner | wiki (write), gitea issues | touch code, merge |
| `architect-agent` | Architect — **owns the tech stack** | Read, WebSearch, wiki (write ADR), gitea | touch code, merge, pick outside the allowlist |
| `designer-agent` | UI Designer | penpot (read), wiki (write) | touch code |
| `backend-agent` | Back End Developer | Bash, Edit, gitea | deploy prod, merge |
| `ui-agent` | UI Developer | Bash, Edit, gitea | deploy prod, merge |
| `qa-agent` | QA Engineer | Bash (Playwright), gitea | edit app code, merge |
| `reviewer-agent` | Reviewer + checklist verifier (is the code good? did the role's steps happen?) | Read, Bash (read-only), gitea (read + comment) | **Edit**, merge, dispatch |
| `dev-manager-agent` | The **human** Dev Manager's assistant — reports, surfaces decisions, delegated low-risk chores | Read, Bash (read-only), gitea (read + comment), mattermost | approve gates, merge, deploy, reassign contested work |

```mermaid
flowchart TD
    H([Human: one-paragraph brief]) --> ORC[orchestrator · run.py<br/>dispatcher, not an LLM agent]
    ORC -->|decompose| POA[po-agent] -->|issues + dependency DAG| GITEA[(Gitea issues)]
    POA -->|feature doc| WIKI[(Wiki.js)]
    H -. GATE 1: approve plan .-> ORC
    ORC -->|needs a stack?| ARC[architect-agent<br/>cost · perf · landscape · allowlist]
    ARC -->|ADR proposal| WIKI
    H -. GATE 2: approve tech stack ADR .-> ARC
    ORC -->|dispatch READY issues| AG
    subgraph AG [role agents · headless · parallel git worktrees]
      BEA[backend-agent]; UIAG[ui-agent]; DSG[designer-agent]
    end
    AG -->|PRs + cc-audit| GITEA
    GITEA -->|PR| CI{Gitea Actions CI}
    CI -->|green| REV[reviewer-agent<br/>review + role checklist]
    REV -->|PASS| H2[/GATE 3: human approves merge/]
    H2 --> QA[qa-agent] -->|acceptance on merged feature| DONE([Feature ready])
    DONE --> DM[dev-manager-agent<br/>report + 'decisions for you'] -.-> HM([Human Dev Manager])
    ORC <-->|standups · alerts| MM[(Mattermost)]
```

**Recipe format** is the same as Capstones 1–2: 🎯 **Goal** → 🤖 **Claude Code move** → ✅ **Verify** → 💡 **Why**, with a hidden solution per recipe. The `[[cc-audit]]` convention from Capstone 2 carries over unchanged — agents emit it as Gitea issue comments.

---

### Phase 0 — Stand up the local platform

#### Recipe 0.1 — The whole stack in one `docker compose up`

- 🎯 **Goal:** Git+CI, issue board, docs, and chat running locally — the agents' entire world, reproducible and disposable.
- 🤖 **Claude Code move:** A single compose file. Ask Claude to scaffold it, then `docker compose up -d`:
  ```yaml
  # docker-compose.platform.yml — the team's "SaaS", all local OSS.
  services:
    postgres:
      image: postgres:16
      environment: { POSTGRES_PASSWORD: dev }
      volumes: ["pg:/var/lib/postgresql/data"]
    gitea:                       # git + issues + projects(Kanban) + PRs + Actions(CI)
      image: gitea/gitea:1.22
      environment: { GITEA__database__DB_TYPE: postgres, GITEA__database__HOST: postgres:5432,
                     GITEA__actions__ENABLED: "true" }
      ports: ["3000:3000", "2222:22"]
      depends_on: [postgres]
    gitea-runner:                # executes Gitea Actions (the CI gate)
      image: gitea/act_runner:latest
      environment: { GITEA_INSTANCE_URL: http://gitea:3000,
                     GITEA_RUNNER_REGISTRATION_TOKEN: "${RUNNER_TOKEN}" }
      volumes: ["/var/run/docker.sock:/var/run/docker.sock"]
      depends_on: [gitea]
    wiki:                        # docs — Confluence alternative
      image: requarks/wiki:2
      environment: { DB_TYPE: postgres, DB_HOST: postgres, DB_USER: postgres, DB_PASS: dev, DB_NAME: wiki }
      ports: ["3001:3000"]
      depends_on: [postgres]
    mattermost:                  # chat + notifications — Teams/Slack alternative
      image: mattermost/mattermost-team-edition:9
      environment: { MM_SQLSETTINGS_DRIVERNAME: postgres,
                     MM_SQLSETTINGS_DATASOURCE: "postgres://postgres:dev@postgres/mattermost?sslmode=disable" }
      ports: ["8065:8065"]
      depends_on: [postgres]
    ollama:                      # the LOCAL LLM — serves an open coding model in Docker
      image: ollama/ollama:latest
      ports: ["11434:11434"]
      volumes: ["ollama:/root/.ollama"]
      # GPU optional: add `deploy.resources.reservations.devices` for NVIDIA. After up:
      #   docker compose exec ollama ollama pull qwen2.5-coder:14b
      # Agents/runners reach it at http://ollama:11434 (OpenAI-compatible at /v1).
    # Optional (heavier): Penpot for design — add its official compose if the designer-agent is in play.
  volumes: { pg: {}, ollama: {} }
  ```
- ✅ **Verify:** Gitea at `:3000`, Wiki.js at `:3001`, Mattermost at `:8065` all load; the Actions runner shows as registered in Gitea admin; `docker compose down -v` wipes it clean.
- 💡 **Why:** The agents act on *real* systems, not mocks — but real systems you own, can reset, and never bill you. The whole capstone is `up`/`down`-able.

<details>
<summary>💡 Solution — what good looks like</summary>

- One compose file brings up git+CI+issues+docs+chat; CI is **real** (Gitea Actions runner with a Docker socket), so the agents' PRs actually get tested.
- It's **disposable** (`down -v` resets everything), so you can rehearse the autonomous run repeatedly from a clean slate.
- **What you should NOT have done:** point the agents at your company's real GitHub/Jira while you're still learning how autonomous they are. Rehearse on the local stack; promote to real systems only once the gates and least-privilege are proven.

</details>

#### Recipe 0.2 — Wire each tool to an MCP server

- 🎯 **Goal:** Every platform tool is reachable as first-class tools, scoped to the local instance.
- 🤖 **Claude Code move:** When the runner is **Claude Code** (or goose), add MCP servers (Ch 14) — in `.claude/settings.json` for Claude Code — using off-the-shelf servers where they exist and thin ones over the REST API where they don't (Ch 34). *(The companion project's Python orchestrator skips MCP and calls Gitea/Mattermost over **REST/`httpx`** directly — same reach, no Claude-specific config.)*
  ```json
  {
    "mcpServers": {
      "gitea":      { "command": "npx",  "args": ["-y", "gitea-mcp"],          "env": { "GITEA_URL": "http://localhost:3000", "GITEA_TOKEN": "${env:GITEA_TOKEN}" } },
      "wiki":       { "command": "node", "args": ["./mcp/wiki-server.js"],     "env": { "WIKI_URL": "http://localhost:3001", "WIKI_TOKEN": "${env:WIKI_TOKEN}" } },
      "mattermost": { "command": "npx",  "args": ["-y", "mattermost-mcp"],     "env": { "MM_URL": "http://localhost:8065",   "MM_TOKEN": "${env:MM_TOKEN}" } }
    }
  }
  ```
- ✅ **Verify:** `claude doctor` lists `gitea`, `wiki`, `mattermost`; "create a test issue in repo X" and "post to #dev in Mattermost" both work against the local stack.
- 💡 **Why:** Agents coordinate *through these tools* — the issue board is the shared memory, chat is the nudge channel. No MCP, no coordination.

<details>
<summary>💡 Solution — what good looks like</summary>

- Off-the-shelf MCP where it exists; a **thin custom MCP over the REST API** (Ch 34) where it doesn't — a few tools (`create_issue`, `comment`, `create_pr`) is enough, you don't wrap the whole API.
- Tokens are **scoped to the local instance** and injected via env, never committed.
- **What you should NOT have done:** have agents shell out to `curl` against each tool ad hoc. An MCP server is the audited, typed, reusable surface; scattered `curl` calls are unauditable and brittle.

</details>

#### Recipe 0.3 — The leash: runner-agnostic guardrails

- 🎯 **Goal:** Make the *irreversible and outward-facing* actions impossible for an agent to take alone — so everything else can run unattended.
- 🤖 **Claude Code move:** Put the leash in the **platform**, not the agent runtime — so it holds no matter which runner (goose / aider / Claude Code) pushed. Three layers (see [`after/guardrails/`](after/guardrails/)):
  ```
  # 1. Gitea branch protection on `main`: no direct pushes; require PR + green CI + a
  #    reviewer-agent PASS + >=1 approval. This IS the merge gate, enforced server-side.
  # 2. A server-side `pre-receive` git hook: reject direct pushes to main + secret-scan
  #    the incoming commits (gitleaks). Holds even if a runner has no hook system.
  # 3. Run each agent in a sandboxed worktree/container with SCOPED, short-lived creds
  #    (push feature branches + comment; cannot merge or deploy). Least privilege by token.
  ```
  > **If — and only if — your runner is Claude Code**, you can add a `PreToolUse` hook (Ch 13) as a *fourth* layer that blocks `git push`/`merge` to main and secret commits client-side. A non-Claude runner (goose/aider) won't fire that hook — which is exactly why layers 1–3 carry the leash.
- ✅ **Verify:** Any agent — under any runner — that tries to push/merge `main` is rejected by branch protection + the `pre-receive` hook; a normal feature-branch PR is not; the secret scan blocks a staged key.
- 💡 **Why:** "Minimal human interaction" is only responsible if the agent *cannot* do the dangerous thing. A leash that lives in a *specific runner's* hook system silently disappears the moment you swap runners — so it belongs in the git server + the sandbox.

<details>
<summary>💡 Solution — what good looks like</summary>

- The dangerous actions (merge to `main`, prod deploy) are blocked **server-side + by the sandbox** — branch protection, the `pre-receive` hook, and scoped creds — so a prompt-injected or confused agent can't cross the line *regardless of runner*.
- The merge gate opens only via a human approval on the PR; least privilege is enforced by the **token scope**, not a `tools:` line a non-Claude runner ignores.
- **What you should NOT have done:** rely on the agent's *prompt* ("please don't merge to main"), or on a **Claude-Code-only `PreToolUse` hook** as the sole leash. Instructions are advisory and a runner-specific hook is fragile — build the leash in the platform, not the prompt or one vendor's runtime.

</details>

---

### Phase 1 — Define the role agents

#### Recipe 1.1 — One agent per role, least privilege

- 🎯 **Goal:** Each lifecycle role becomes a `<role>-agent.md` — `.claude/agents/` for the Claude Code runner, or tool-neutral `agents/` read by the orchestrator (as the companion project does) — with exactly the tools it needs and a system prompt that *is* its job.
- 🤖 **Claude Code move:** Author the agent files (Ch 7). Most reuse a Capstone 2 skill body as their prompt. The pivotal one, `backend-agent` (it owns the database schema **and** the API, in whatever stack the architect's ADR chose):
  ```markdown
  ---
  name: backend-agent
  description: Implements a back-end issue — database schema then the API, contract-first, in the project's stack — tests it, and opens a PR. Dispatched by the orchestrator; never merges.
  tools: [Read, Edit, Bash, mcp__gitea]
  ---

  You are the back-end developer agent. Input: one Gitea issue (the task) + its OpenAPI spec.
  Use the stack from the approved architecture ADR — do not pick your own.

  1. Read the issue + linked Wiki spec. If it's the DB task, do step 2; the API task, step 3.
  2. DB: write a versioned migration (+ tested rollback); verify against a real DB in a
     container (constraints + seed round-trip). Constraints enforce invariants, not app code.
  3. API: confirm the DB issue is CLOSED, then implement CONTRACT-FIRST (the framework
     regenerates the agreed OpenAPI) against that schema.
  4. TDD: write tests for every spec response, then run the stack's verify/test command.
     - If RED: read the failure, fix, re-run. Repeat up to 5 times.
     - Still RED after 5 → STOP, comment the failure on the issue, do NOT open a PR.
  5. Only when GREEN: open a Gitea PR. Comment the [[cc-audit]] lines (db_migrate/implement,
     unit_tests with count, dev=backend-agent, durations). Move the issue to "In Review".
     DO NOT merge — human gate.
  Halt and comment on the issue at the first unrecoverable red gate.
  ```
- ✅ **Verify:** Invoking `backend-agent` on a sample issue produces a green build + an open PR + cc-audit comments — and the agent has no tool that could merge or deploy.
- 💡 **Why:** A specialised agent with a narrow toolset is predictable and safe to run unattended. The system prompt encodes the role's standards once; every dispatch follows them.

<details>
<summary>💡 Solution — what good looks like</summary>

- The agent's `tools:` list is **exactly its job** — `backend-agent` can edit code and talk to Gitea, but has no deploy or merge tool, so autonomy can't exceed its mandate.
- Its prompt reuses the proven Capstone 2 `/implement-api-task` workflow (contract-first, real-DB integration tests, halt-on-red), so quality doesn't regress just because a machine is driving.
- **What you should NOT have done:** one all-powerful "dev agent" with every tool. Least privilege per role is what makes the swarm auditable and bounds the blast radius of any single agent going wrong.

</details>

#### Recipe 1.2 — The reviewer/verifier agent has no hands

- 🎯 **Goal:** One `reviewer-agent` that both critiques the PR **and** verifies the role checklist — but cannot change code, merge, or dispatch. Separation of duties, enforced by tools.
- 🤖 **Claude Code move:** One **independent peer** that does *both* jobs — review the diff **and** verify the role checklist — with **read + comment only** (no `Edit`, no merge, no dispatch):
  ```markdown
  ---
  name: reviewer-agent
  description: Independently reviews a Gitea PR (correctness, security, contract-fidelity) AND verifies the task's role checklist against evidence. Comments a verdict. Cannot edit, merge, or dispatch.
  tools: [Read, Bash, mcp__gitea]
  ---
  Input: a Gitea PR + the task's role checklist (.claude/team/role-checklists/<role>.md).

  REVIEW — run the /review and /security-review lenses on the diff. Post findings 🔴/🟡/⚪.
  VERIFY — for EACH Definition-of-Done item, find the cited evidence (the issue's [[cc-audit]]
    lines, CI status, the named artifact). Mark ✓ only if it EXISTS and PASSES; ✗ otherwise,
    naming what's missing. Re-derive from evidence — never take the doing agent's word.
  VERDICT — PASS only if NO 🔴 remain AND every required checklist item is ✓. Post the review
    + the checked-off checklist as comments; append [[cc-audit]] gate=review and gate=verify
    (dev=reviewer-agent). On FAIL: request changes, route back to the OWNING agent.
  Never edit files. Never merge.
  ```
- ✅ **Verify:** It can comment and request changes but has no tool that edits, merges, or dispatches; a 🔴 finding **or** a missing checklist item bounces the PR back to the owner; the orchestrator won't reach the merge gate until it PASSes.
- 💡 **Why — independent peer, not self or lead:** the agent that did the work is the **worst** judge of it (self-review = marking your own homework). The **orchestrator** dispatches — making it judge too would concentrate dispatch + judgement and bottleneck the swarm. So **one independent peer** asks *both* "is the code good?" **and** "did the role's required steps actually happen?", and the lead only **enforces** its verdict.

<details>
<summary>💡 Solution — what good looks like</summary>

- Authority is **tool-enforced**: with no `Edit`/merge/dispatch, the agent can only judge — so "PASS" means something, and fixes flow back to the owner. It reuses the `/review` + `/security-review` lenses (Ch 9) **and** checks the checklist from **evidence** (cc-audit/CI/artifacts), never the doer's claim.
- The verdict is **two logged gates** (`review` + `verify`), so `/quality-report` shows each task was independently reviewed *and* verified, by which agent.
- **What you should NOT have done:** give it `Edit` "to fix small things" (you lose the second pair of eyes), let the doing agent self-attest, or fold the check into the orchestrator. Keep *doing*, *judging*, and *enforcing* in different hands — but judging the code and judging the checklist are one job, so one peer owns both.

</details>

#### Recipe 1.3 — Role checklists: best-practice readiness + Definition-of-Done

- 🎯 **Goal:** Make "has the required skills for this role" and "finished this task properly" *concrete* — a committed, best-practice checklist per role, not an assumption baked into a prompt.
- 🤖 **Claude Code move:** A committed, PR-gated checklist per role at `.claude/team/role-checklists/<role>.md` (same governance surface as `devs.yml`). Each has **two layers** — *readiness* (capability, checked once at preflight) and *Definition-of-Done* (checked every task) — and **every item points at evidence**:
  ```markdown
  # .claude/team/role-checklists/backend.md — edit via PR.
  ## Readiness (verified ONCE, at preflight — proves the agent CAN do the role)
  - [ ] tools present: Bash, Edit, mcp__gitea         → orchestrator runs `claude doctor`
  - [ ] skills loaded: implement-api-task, implement-db-task, mutation-drill
  - [ ] golden-fixture eval PASSES: on a known issue → green build (stack's verify command) + a PR,
        AND a seeded mutation (flip `<`→`<=`) turns a test RED  (proves tests catch bugs, not decorate)
  ## Definition of Done (verified EVERY task, against evidence)
  - [ ] unit tests written AND green        → [[cc-audit]] gate=unit_tests + CI green
  - [ ] coverage ≥ 80% on changed lines     → coverage artifact
  - [ ] migration has a tested rollback     → [[cc-audit]] gate=db_migrate
  - [ ] generated OpenAPI == agreed spec    → spec diff is empty
  - [ ] money is integer/NUMERIC, no float  → reviewer-agent note
  - [ ] /review clean (+ /security-review if auth) → [[cc-audit]] gate=review
  ```
  ```markdown
  # .claude/team/role-checklists/ui.md   (qa / design / po get the same shape)
  ## Definition of Done
  - [ ] typed client GENERATED from the spec (not hand-typed) → generated dir present in PR
  - [ ] component unit tests + Playwright e2e green           → gate=unit_tests, gate=e2e_tests
  - [ ] built from Figma Dev-Mode tokens                      → design link + reviewer note
  - [ ] accessibility passes (WCAG AA)                        → axe report artifact
  ```
- ✅ **Verify:** Every item is **evidence-checkable** (maps to a `[[cc-audit]]` gate, a CI status, or a named artifact); the readiness eval gates dispatch — a `backend-agent` that can't turn its own fixture test RED is not trusted with real issues.
- 💡 **Why:** This is how "required skills for a role" stops being a hope. Readiness proves *capability* before you trust the agent unattended; the per-task DoD turns "the agent should write tests" into "no advance unless the `unit_tests` evidence exists." Best practice, written down and versioned.

<details>
<summary>💡 Solution — what good looks like</summary>

- Items are **evidence-checkable**, not aspirational — each names the artifact that proves it. The **readiness** layer (incl. the mutation-drill eval from Capstone 1's challenge 7) proves the agent *can* do the role; the **DoD** layer proves it *did*, per task.
- Checklists are **committed and PR-gated** (like `devs.yml` / `slas.yml`), so changing the bar is a reviewed, auditable decision.
- **What you should NOT have done:** a checklist of vibes ("write good tests", "follow best practice") with no evidence pointer. If an item can't be checked against an artifact, an agent can't be held to it and the verifier can't enforce it.

</details>

#### Recipe 1.4 — The `architect-agent` owns the tech stack (cost · performance · landscape · allowlist)

- 🎯 **Goal:** One agent owns the tech-stack decision — choosing only from an **approved allowlist**, under **cost** and **performance** constraints, informed by the **current landscape** — and records it as an ADR a **human approves**. The implementer agents inherit the stack; they never pick it.
- 🤖 **Claude Code move:** A committed, PR-gated allowlist + budgets (the team's "tech radar"), and an architect agent constrained to it:
  ```yaml
  # .claude/team/allowed-stack.yml — the approved tech radar + budgets. Edit via PR.
  allowed:                                     # ADOPT — free to choose
    backend:   [java-spring, kotlin-ktor, node-nest]
    datastore: [postgres, mysql]
    frontend:  [angular, react]
    cache:     [redis]
  trial:       [go-fiber]                      # allowed only with an explicit noted reason
  hold:        [mongodb, microservices-by-default]   # NOT allowed without a human exception
  constraints:
    cost_ceiling_usd_month: 500                # infra + licensing budget
    perf: { p99_ms: 200, throughput_rps: 500 }
  ```
  ```markdown
  ---
  name: architect-agent
  description: Selects the tech stack from the approved allowlist, balancing cost, performance, and the current landscape; writes an ADR for human approval. Does not write app code or merge.
  tools: [Read, WebSearch, mcp__wiki, mcp__gitea]
  ---
  Input: the feature doc + the non-functional requirements (constraints in allowed-stack.yml).

  1. Read allowed-stack.yml. Candidates MUST come from `allowed` (or `trial` with a reason).
     NEVER propose anything in `hold` without flagging it as an explicit exception for the human.
  2. Research the CURRENT landscape (WebSearch): maturity, community, known issues, how each
     candidate has moved since the allowlist was last reviewed. Cite sources.
  3. Score the shortlist on: fit, COST (vs cost_ceiling), PERFORMANCE (vs p99/throughput),
     team familiarity (devs.yml stacks), operational risk.
  4. Pick ONE. Write an ADR to the Wiki: context, options, decision, cost & perf rationale
     (with numbers), trade-offs, and what would change the decision.
  5. Append [[cc-audit]] gate=architecture and STOP — the choice is a HUMAN GATE (Recipe 2.2).
     Do NOT start implementation.
  ```
- ✅ **Verify:** The architect proposes a stack **only from the allowlist**, with an ADR showing **cost vs ceiling** and **perf vs targets** + cited landscape evidence; a human approves before any implementer runs; a `hold` technology surfaces as an explicit exception, never slipped in.
- 💡 **Why:** Tech stack is the highest-leverage, hardest-to-reverse decision in the build. So it's owned by a *dedicated* agent, *constrained* to a reviewed allowlist, *justified* by cost/perf/landscape, and *signed off* by a human — not improvised per task by whichever implementer got there first.

<details>
<summary>💡 Solution — what good looks like</summary>

- The **allowlist + budgets are committed governance** (PR-gated like `devs.yml`/`slas.yml`), so "allowed tech" is a reviewed decision, not the model's whim; the **ADR** makes the choice auditable and reversible-by-decision; the **human gate** keeps the irreversible call human-owned.
- The architect **reads the live landscape with citations** and **scores against real numbers** (cost ceiling, p99/throughput), so the ADR is an argument, not a preference.
- **What you should NOT have done:** let each implementer agent pick its own stack (you get five frameworks and no coherence), let the architect adopt a `hold` technology unattended, or approve a stack ADR with no cost/perf numbers. The implementers build *within* the approved stack; changing it is a new ADR + a human gate.

</details>

---

### Phase 2 — The orchestrator (minimal human interaction)

#### Recipe 2.1 — The coordinator loop (the orchestrator service)

- 🎯 **Goal:** A long-running orchestrator that reads a brief, decomposes it, and drives the role agents to green — pausing only at the human gates.
- 🤖 **Claude Code move:** The orchestrator is **plain deterministic code** that *dispatches* agents — it walks the dependency DAG and runs each agent headless in its own worktree (Ch 26). The companion project ships it as a **Python `orchestrator/run.py`** with a **pluggable runner** (`runAgent` → a local CLI like goose/aider over Ollama); you could equally write it with the **Agent SDK** (Ch 34) if your runner is Claude. The loop is identical either way (pseudocode below; the project's `run.py` is the Python realization):
  ```ts
  // the orchestrator loop (pseudocode) — needs a human only at the gates.
  // companion project: orchestrator/run.py (Python, pluggable runner over Ollama).
  const dag = await runAgent("po-agent", { brief });            // → Gitea issues + deps + Wiki doc
  await humanGate("approve-plan", dag);                          // GATE 1 (human)

  if (dag.needsStackDecision) {                                  // new project / new tech needed
    const adr = await runAgent("architect-agent", { dag });      // cost · perf · landscape · allowlist → ADR
    await humanGate("approve-stack", adr);                       // GATE 2 (human) — approve the ADR
  }

  while (!dag.allClosed()) {
    const ready = dag.readyIssues();                             // deps closed, unassigned
    await Promise.all(ready.map(issue =>
      runAgentInWorktree(agentFor(issue.role), { issue })));     // implement + test + PR (parallel)

    for (const pr of openPRs()) {
      const rv = await runAgent("reviewer-agent",                // review the diff AND the role checklist
                  { pr, checklist: checklistFor(pr.role) });
      if (ciGreen(pr) && rv.pass) {                              // pass = no 🔴 review + all checklist items ✓
        await humanGate("merge", pr);                            // GATE 3 (human) → CC_GATE_APPROVED
        mergePR(pr);
      }
    }
    if (budget.exceeded()) { notify("cost cap hit — pausing"); break; }   // safety
  }
  await runAgent("qa-agent", { epic: dag.epic });                // acceptance on the merged feature
  ```
- ✅ **Verify:** From one brief, the orchestrator creates the issues, runs the architect + stack gate when a stack decision is needed, dispatches agents in parallel, collects PRs, runs review + CI + the verifier, and stops only at the human gates — visible live in Gitea + Mattermost.
- 💡 **Why:** The DAG is the plan; the orchestrator just executes it. Parallel worktrees mean independent issues (DB vs a UI) progress at once. This is the "minimal human interaction" engine.

<details>
<summary>💡 Solution — what good looks like</summary>

- The orchestrator dispatches strictly by the **dependency DAG** (an agent starts only when its blockers are closed) and runs independent issues **in parallel worktrees**, so wall-clock ≈ the critical path, not the sum.
- It owns no edit tools itself — it only **dispatches and gates** — and it carries a **budget/iteration cap** that pauses the run rather than looping forever.
- **What you should NOT have done:** a free-for-all where every agent starts at once and races on `main`. Worktree isolation + DAG ordering + a cost cap are what keep an autonomous swarm from melting down.

</details>

#### Recipe 2.2 — The human-interaction gates (what you still approve)

- 🎯 **Goal:** Name the *few* points where a human must say yes — and make everything else autonomous.
- 🤖 **Claude Code move:** Encode the gates as `humanGate()` pauses (orchestrator) backed by the 0.3 guardrails (branch protection + the `pre-receive` hook + sandbox). **Where the human acts:** the *plan* and *stack* gates surface in the **`approvals/` UI** (`:8080`) — `humanGate()` opens a gate there (`POST /gates`) and blocks until you click Approve/Reject; the *merge* gate is approved in **Gitea** (Approve + Merge on the PR), which branch protection enforces. The full list:
  | Gate | Fires | Why a human is required |
  |------|-------|--------------------------|
  | **Approve plan** | after `po-agent` decomposes, before any code | scope + the **impact** hypothesis/metric ("is this worth building?") and the **time target** ("realistic?") |
  | **Approve tech stack (ADR)** | after `architect-agent` proposes a stack, before implementation — *only when a stack decision is needed* | architecture is a high-leverage, hard-to-reverse choice; a human signs off the ADR |
  | **Approve merge to `main`** | after CI ✓ + the **reviewer-agent PASS** (review + checklist) for a PR | the one irreversible, integration-affecting step |
  | **Approve prod deploy** | (out of scope here — dev deploy is automatic) | outward-facing; never unattended |
  Everything between — implement, test, open PR, CI, **review + checklist-verify**, dev-deploy, QA — runs with no human. The reviewer-agent is an *automated* gate that precedes the human merge gate: it gates *advancement*, the human gates *approval*.
- ✅ **Verify:** A feature run interrupts the human only at the gates — plan and merge always, plus the stack-ADR approval whenever the architect proposes a new/changed stack; declining a gate cleanly halts that branch without corrupting the board.
- 💡 **Why:** Autonomy is about *moving the human to the highest-leverage decisions*. A few judgment calls per feature — is this the right thing (plan), the right architecture (stack), the right thing to integrate (merge) — instead of fifty mechanical ones.

<details>
<summary>💡 Solution — what good looks like</summary>

- The gates sit on **scope** (plan), **architecture** (the stack ADR), and the **irreversible/outward** steps (merge, prod) — the decisions where human judgement actually adds value — and they're **enforced** by the 0.3 hooks, not just requested.
- Declining a gate halts that work cleanly and leaves the board truthful (the issue stays open with a comment), so a "no" is safe.
- **What you should NOT have done:** gate everything (you've just rebuilt manual work with extra steps) or gate nothing (an agent merges its own unreviewed code to `main`). The art is choosing the few gates that matter.

</details>

---

### Phase 3 — Run a feature end-to-end, then audit it

#### Recipe 3.1 — Kick off a feature with one brief

- 🎯 **Goal:** Ship a real feature through the swarm with a handful of approvals (plan, stack when needed, merge) and no other human input.
- 🤖 **Claude Code move:** Start the orchestrator with a brief; watch it work in Gitea (issues, PRs, CI) and Mattermost (standups):
  ```
  # submit the feature in the approvals UI (http://localhost:8080), then start a worker:
  $ OLLAMA_MODEL=qwen2.5-coder:14b docker compose run --rm orchestrator
  #   (or skip the UI for the brief: -e CC_BRIEF="Add a CSV export of a customer's monthly usage")
  # → po-agent writes the Wiki spec (incl. the impact hypothesis + success metric + a time
  #   target; logs gate=impact) + opens issues (db, api, ui, qa) with deps.
  # → GATE 1 (approvals UI): approve the plan — worth building (impact)? time target realistic?
  # → (if a stack decision is needed) architect-agent proposes a stack ADR; GATE 2 (approvals UI): approve it.
  # → backend-agent (db then api) → ui-agent run (parallel worktrees); each opens a PR; Gitea Actions
  #   runs CI; reviewer-agent reviews the diff AND verifies the role checklist (PASS to advance).
  # → GATE 3 (Gitea PR): approve each merge. qa-agent runs acceptance; then dev-manager-agent posts
  #   the delivery report + a "decisions for you" digest to the human Dev Manager.
  ```
- ✅ **Verify:** The feature branch(es) merged after green CI + review + verifier + your approvals; the Wiki has the spec (and the stack ADR if one was needed); Gitea issues are closed with `[[cc-audit]]` trails; QA acceptance is green.
- 💡 **Why:** This is the payoff — a feature that planned, architected, built, reviewed, tested, and integrated itself, with you making a few judgement calls instead of running the whole team.

<details>
<summary>💡 Solution — what good looks like</summary>

- One brief in; a merged, tested feature out, with the human consulted only at the **plan** and **merge** gates. The board (Gitea) and chat (Mattermost) tell the whole story without you asking.
- The first runs surface prompt/tool gaps in specific agents — fix the agent definition, not the run, so the next feature is smoother.
- **What you should NOT have done:** treat the first autonomous run as production. Rehearse on the throwaway local stack until the gates and agent quality are proven, *then* point it at real systems.

</details>

#### Recipe 3.2 — Observe, audit, and cap the swarm

- 🎯 **Goal:** Know what every agent did, and guarantee the run can't run away.
- 🤖 **Claude Code move:** Reuse Capstone 2's reporting on this stack, plus autonomy-specific limits:
  ```
  # /quality-report (Capstone 2) works unchanged — cc-audit comments now live on Gitea issues.
  > /quality-report <epic/milestone>     # gates done, by which AGENT, which command, durations
  # Autonomy limits (in the orchestrator + guardrails):
  #  - budget cap: stop after N agent-invocations or $X equivalent; notify, don't loop.
  #  - kill switch: a sentinel file / Mattermost command halts dispatch immediately.
  #  - blast radius: agents work only in worktrees; main is branch-protected (0.3).
  ```
- ✅ **Verify:** `/quality-report` attributes every gate to a specific *agent* with durations; tripping the budget cap pauses the run and posts to Mattermost; the kill switch stops dispatch.
- 💡 **Why:** Autonomy without observability is a liability. The same `[[cc-audit]]` trail that proved *who* in Capstone 2 now proves *which agent* — and the caps mean a bad loop costs minutes, not your month's budget.

<details>
<summary>💡 Solution — what good looks like</summary>

- The audit trail is **identical to Capstone 2** — only the `dev` field now names an agent — so `/quality-report` and `/portfolio-report` work unchanged, and a human can see exactly which agent did which gate, how long it took.
- A **budget cap + kill switch + worktree/branch-protection** mean the worst case is a paused run and a few wasted minutes, not an unbounded spend or a corrupted `main`.
- **What you should NOT have done:** run the swarm with no cost ceiling or stop control. An autonomous loop with a bug and no cap is the one failure mode that turns a productivity tool into a bill.

</details>

#### Recipe 3.3 — `/delivery-scorecard`: track impact, quality, and time

- 🎯 **Goal:** Per feature, answer the only question that matters — *did we deliver, on impact, on quality, and on time?* — from logged data, not opinion.
- 🤖 **Claude Code move:** A command that joins the **impact record** (set at plan) with the `[[cc-audit]]` trail (quality gates + durations), and schedules an after-release impact check:
  ```
  > /delivery-scorecard <epic>
  # 🎯 IMPACT   — hypothesis + success metric from the plan's gate=impact record;
  #               baseline → target → ACTUAL (measured after release, not at merge).
  # ✅ QUALITY  — gates passed / required across all tasks; bugs filed; rework loops;
  #               verifier PASS rate.  (all from [[cc-audit]])
  # ⚡ TIME     — cycle time (plan→merge) vs the plan's time target; slowest stage.
  # Verdict per axis: ✓ on-target / ⚠ off-target, with the number. Post to Wiki + Mattermost.

  > /schedule "14 days after release" /delivery-scorecard <epic> --impact-only   # close the impact loop
  ```
  Example:
  ```
  Feature: CSV usage export (epic #142)
  🎯 Impact   ⚠  "cut support tickets about exports 30%"  → baseline 40/wk, target 28, ACTUAL 35 (−12%)  [follow-up in 14d]
  ✅ Quality  ✓  gates 24/24 · 1 bug (fixed) · 1 rework loop · verifier 6/6 PASS
  ⚡ Time      ✓  cycle 2d 9h vs target 3d · slowest stage: backend api (41m)
  ```
- ✅ **Verify:** The scorecard shows all three axes with real numbers; a missed time target or unmet impact metric shows ⚠; the impact figure is the *measured* metric after release, not "merged".
- 💡 **Why:** Autonomy makes shipping cheap, which makes shipping the *wrong* thing cheap too. Tracking impact + quality + time together is what stops a fast swarm from confidently delivering the wrong feature, buggy, "on time".

<details>
<summary>💡 Solution — what good looks like</summary>

- All three axes are **logged numbers**: quality and time fall straight out of the `[[cc-audit]]` trail you already emit; impact comes from the `gate=impact` record the `po-agent` set at plan, **measured after release** via the scheduled follow-up — because impact can't be known at merge.
- The verdict is **per axis**, so "fast but off-target" or "on-target but buggy" can't hide behind a single green checkmark.
- **What you should NOT have done:** track only time/throughput (the easy-to-measure axis) and call it delivery, or declare impact "done" at merge. A feature isn't delivered when it's merged — it's delivered when the metric it promised actually moves.

</details>

### What this exercised

| Phase | Levers pulled |
|-------|---------------|
| 0 | Local OSS platform on `docker compose`; tool access via REST or MCP (14, 34); runner-agnostic leash — branch protection + a `pre-receive` hook + sandbox (24) |
| 1 | Custom subagents, one per role, least-privilege tools (7); reused Capstone 2 skill workflows; an `architect-agent` that owns the tech stack (cost/perf/landscape vs an allowlist → human-approved ADR); best-practice role checklists (readiness + DoD) enforced by an independent `reviewer-agent` (code review **and** checklist verification in one peer); separation of *doing / judging / enforcing* |
| 2 | Orchestrator service — Python + pluggable CLI runner over Ollama, or the Agent SDK (34); dependency-DAG dispatch, parallel worktrees (26), human-gate design (plan/stack via a FastAPI approvals UI, merge in Gitea), verifier-gated advancement |
| 3 | Headless autonomous run (25), `/quality-report` over agent audit trails (14), budget caps + kill switch; the `dev-manager-agent` rolls up the delivery scorecard for the human — 🎯 impact (measured after release), ✅ quality (gates), ⚡ time (cycle time vs target) |

### Make it yours

Stand up the local platform (`docker compose up`), write the eight agent definitions (`po`, `architect`, `designer`, `backend`, `ui`, `qa`, `reviewer`, `dev-manager` — the orchestrator is the *program*, not an agent) with **least-privilege tools**, give the **`architect-agent`** an allowed-stack list + cost/perf budgets so it owns the tech-stack ADR (human-approved), write a **best-practice checklist per role** (readiness + Definition-of-Done), wire the independent **`reviewer-agent`** (code review + checklist verification) to gate advancement, encode your **three human gates** (plan · stack · merge), and — so the swarm is steered, not just fast — set each feature's **impact metric and time target at plan** and roll all three axes up with **`/delivery-scorecard`**. Run one real feature through the swarm. Start with a tiny feature and a tight budget cap; widen the leash only as each agent's readiness eval and checklist record earn trust. The goal isn't to remove yourself — it's to move yourself to the decisions that need judgement and let the specialised, verified agents do the other fifty steps.

> **Specialise every agent. Define the role as a checklist; verify it with an independent peer. Steer by impact, quality, and time — and track all three. Enforce the leash in the harness, not the prompt. Keep the human on the gates that matter.**

---

