# The leash (runner-agnostic guardrails)

The autonomy guardrails do **not** depend on Claude Code — they sit in the
platform and the OS, so they hold no matter which agent/runner (goose / aider /
openhands / Claude) is driving. Three layers:

1. **Gitea branch protection on `main`** — require a PR + green CI + ≥1 approval
   (the reviewer-agent's PASS and/or a human), disallow direct pushes and
   self-approval. This *is* the human merge gate. Set it via the Gitea UI or API:
   ```bash
   curl -X POST -H "Authorization: token $GITEA_TOKEN" \
     "$GITEA_URL/api/v1/repos/<owner>/<repo>/branch_protections" \
     -d '{"branch_name":"main","enable_merge_whitelist":true,"required_approvals":1,
          "block_on_official_review_requests":true,"enable_status_check":true}'
   ```
2. **Server-side `pre-receive` hook** ([`pre-receive`](pre-receive)) — rejects
   direct pushes to protected branches and scans for secrets. Install it on the
   Gitea repo (admin → git hooks, or `repo.git/hooks/pre-receive`).
3. **Sandboxed runner** — each agent runs in its own git worktree/container with
   **scoped, short-lived credentials** (a token that can push feature branches
   and comment, but cannot merge or deploy). Least privilege is enforced by the
   sandbox + the token scope — not by an agent's prompt or a `tools:` line.

The orchestrator's `human_gate("merge", …)` pauses for a human; branch protection
is what makes that gate *unbypassable* by an agent.
