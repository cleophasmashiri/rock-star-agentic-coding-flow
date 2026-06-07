# The leash (runner-agnostic guardrails)

Wire the autonomy guardrails so they hold regardless of the agent/runner — they
must NOT depend on Claude Code hooks. Three layers to set up (full reference in
[`../../after/guardrails/`](../../after/guardrails/)):

1. **Gitea branch protection on `main`** — require PR + green CI + ≥1 approval;
   disallow direct push & self-approval. (This is the human merge gate.)
2. **Server-side `pre-receive` hook** ([`pre-receive`](pre-receive)) — reject
   direct pushes to protected branches + secret-scan the incoming commits.
3. **Sandboxed runner** — each agent in its own worktree/container with scoped,
   short-lived creds (push feature branches + comment; NOT merge/deploy).
