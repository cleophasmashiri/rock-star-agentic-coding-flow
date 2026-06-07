#!/usr/bin/env python3
"""Approvals UI (skeleton) — the human surface for the feature factory.

Humans START a feature and approve the PLAN and TECH-STACK gates here; the MERGE
gate stays in Gitea. Fill in the TODOs. Full reference: ../../after/approvals/app.py.
"""
from __future__ import annotations

import itertools
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI(title="Feature Factory — Approvals")
_ids = itertools.count(1)
FEATURES: dict[int, dict] = {}   # id -> {id, brief, status}
GATES: dict[int, dict] = {}      # id -> {id, feature, name, payload, status}

# TODO: API the ORCHESTRATOR calls —
#   GET  /features/next        → pop the next queued brief (status → running)
#   POST /gates {feature,name,payload} → register a pending gate, return its id
#   GET  /gates/{id}           → status (orchestrator polls until != pending)
# TODO: API the HUMAN (UI) calls —
#   POST /features {brief}     → enqueue a feature
#   POST /gates/{id}/{approve|reject} → set the gate's decision
# TODO: GET / (HTMLResponse)   → submit form + pending-gates list with Approve/Reject buttons;
#                                note that GATE 3 (merge) is approved in Gitea.


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return "<h1>Feature Factory — Approvals</h1><p>TODO: build the UI (see ../../after/).</p>"
