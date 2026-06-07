#!/usr/bin/env python3
"""Approvals UI — the human surface for the autonomous feature factory.

Humans START a feature and approve the PLAN and TECH-STACK gates here. The MERGE
gate stays in Gitea (branch protection is the enforced gate); this UI just links to it.

FastAPI + plain HTML forms. In-memory store for the reference — swap for Postgres/
Redis in real use. Runs as the `approvals` compose service on :8080. The orchestrator
talks to it over HTTP (pull the next brief; open a gate; poll for the human's decision).
"""
from __future__ import annotations

import itertools
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI(title="Feature Factory — Approvals")
_ids = itertools.count(1)
FEATURES: dict[int, dict] = {}   # id -> {id, brief, status: queued|running}
GATES: dict[int, dict] = {}      # id -> {id, feature, name, payload, status: pending|approved|rejected}

# ---------- API the ORCHESTRATOR calls ----------
@app.get("/features/next")
def next_feature() -> dict:
    """Orchestrator pulls the next queued brief (instead of CC_BRIEF)."""
    for f in FEATURES.values():
        if f["status"] == "queued":
            f["status"] = "running"
            return f
    raise HTTPException(404, "no queued feature")


@app.post("/gates")
def open_gate(feature: int = Form(...), name: str = Form(...), payload: str = Form("")) -> dict:
    """Orchestrator registers a pending human gate; returns its id."""
    gid = next(_ids)
    GATES[gid] = {"id": gid, "feature": feature, "name": name, "payload": payload, "status": "pending"}
    return {"gate": gid}


@app.get("/gates/{gid}")
def gate_status(gid: int) -> dict:
    """Orchestrator polls this until status != 'pending'."""
    if gid not in GATES:
        raise HTTPException(404, "no such gate")
    return GATES[gid]


# ---------- API the UI (human) calls ----------
@app.post("/features")
def submit_feature(brief: str = Form(...)) -> RedirectResponse:
    fid = next(_ids)
    FEATURES[fid] = {"id": fid, "brief": brief, "status": "queued"}
    return RedirectResponse("/", status_code=303)


@app.post("/gates/{gid}/{decision}")
def decide(gid: int, decision: str) -> RedirectResponse:
    if gid not in GATES or decision not in ("approve", "reject"):
        raise HTTPException(400, "bad request")
    GATES[gid]["status"] = "approved" if decision == "approve" else "rejected"
    return RedirectResponse("/", status_code=303)


# ---------- the page ----------
@app.get("/", response_class=HTMLResponse)
def home() -> str:
    pending = [g for g in GATES.values() if g["status"] == "pending"]
    gate_rows = "".join(
        f"<li><b>{g['name']}</b> (feature {g['feature']}) — {g['payload'][:140]} "
        f"<form method=post action=/gates/{g['id']}/approve style=display:inline><button>Approve</button></form> "
        f"<form method=post action=/gates/{g['id']}/reject style=display:inline><button>Reject</button></form></li>"
        for g in pending
    ) or "<li>none</li>"
    feat_rows = "".join(
        f"<li>#{f['id']} [{f['status']}] {f['brief'][:90]}</li>" for f in FEATURES.values()
    ) or "<li>none</li>"
    return f"""<!doctype html><meta charset=utf-8><title>Feature Factory — Approvals</title>
<h1>Feature Factory — Approvals</h1>
<h2>Start a feature</h2>
<form method=post action=/features>
  <textarea name=brief rows=3 cols=72 placeholder="One-paragraph feature brief..."></textarea><br>
  <button>Submit feature</button>
</form>
<h2>Pending gates (plan / tech-stack)</h2>
<ul>{gate_rows}</ul>
<p><i>GATE 3 (merge) is approved in Gitea — Approve + Merge on the PR; branch protection enforces it.</i></p>
<h2>Features</h2>
<ul>{feat_rows}</ul>"""
