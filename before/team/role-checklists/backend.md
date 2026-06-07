# Role checklist — backend. Edit via PR. The reviewer-agent verifies these against evidence.

## Readiness (verified ONCE, at preflight — proves the agent CAN do the role)
- [ ] tools present: Bash, Edit, mcp__gitea            → orchestrator runs a tool preflight
- [ ] skills loaded: implement-api-task, implement-db-task, mutation-drill
- [ ] golden-fixture eval PASSES: on a known issue → green build (the chosen stack's verify
      command) + a PR, AND a seeded mutation (flip `<`→`<=`) turns a test RED
      (proves tests catch bugs, not decorate)

## Definition of Done (verified EVERY task, against evidence)
- [ ] unit tests written AND green        → [[cc-audit]] gate=unit_tests + CI green
- [ ] coverage >= 80% on changed lines    → coverage artifact
- [ ] migration has a tested rollback     → [[cc-audit]] gate=db_migrate
- [ ] generated OpenAPI == agreed spec    → spec diff is empty
- [ ] money is integer/decimal, no float  → reviewer-agent note
- [ ] /review clean (+ /security-review if auth) → [[cc-audit]] gate=review
