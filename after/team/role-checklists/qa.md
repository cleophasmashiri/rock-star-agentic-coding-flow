# Role checklist — qa. Edit via PR. The reviewer-agent verifies these against evidence.

## Readiness (verified ONCE, at preflight)
- [ ] tools present: Read, Bash, mcp__gitea
- [ ] skills loaded: implement-test-task (Gherkin + Playwright)
- [ ] golden-fixture eval PASSES: a deliberately-broken build is caught (acceptance goes RED)

## Definition of Done (verified EVERY task, against evidence)
- [ ] every acceptance criterion → exactly one tagged Gherkin scenario  → traceability table
- [ ] acceptance scenarios green on the live dev stack (API + UI)        → [[cc-audit]] gate=acceptance_tests
- [ ] regression suite green                                            → [[cc-audit]] gate=regression
- [ ] each failure filed as a bug with a minimal repro + trace, owned   → [[cc-audit]] gate=bug
- [ ] signoff ONLY with all gates green AND zero open bugs              → [[cc-audit]] gate=signoff
