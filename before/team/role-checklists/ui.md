# Role checklist — ui. Edit via PR. The reviewer-agent verifies these against evidence.

## Readiness (verified ONCE, at preflight — proves the agent CAN do the role)
- [ ] tools present: Read, Edit, Bash, mcp__gitea        → orchestrator runs a tool preflight
- [ ] skills loaded: implement-ui-task, e2e-tests
- [ ] golden-fixture eval PASSES: on a known issue → typed client generated + a green build +
      a Playwright e2e that goes RED when the API contract is broken

## Definition of Done (verified EVERY task, against evidence)
- [ ] typed client GENERATED from the spec (not hand-typed)  → generated dir present in the PR
- [ ] component unit tests green                              → [[cc-audit]] gate=unit_tests + CI green
- [ ] Playwright e2e green against the live dev API           → [[cc-audit]] gate=e2e_tests + report
- [ ] built from the design tokens (not a screenshot)        → design Dev-Mode link + reviewer note
- [ ] accessibility passes (WCAG AA)                          → axe report artifact
- [ ] /review clean                                           → [[cc-audit]] gate=review
