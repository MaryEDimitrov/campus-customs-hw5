"""FastAPI dashboard backend for the Campus Customs agent desk."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastmcp import Client
from pydantic import BaseModel, Field

try:
    from .audit import AUDIT_PATH
    from .db_config import DB_PATH, ORIGINAL_DB_PATH
    from .team import run_team
except ImportError:
    from audit import AUDIT_PATH
    from db_config import DB_PATH, ORIGINAL_DB_PATH
    from team import run_team

ROOT = Path(__file__).resolve().parent.parent
MCP_SERVER = ROOT / "mcp_server" / "mcp_server.py"
app = FastAPI(title="Campus Customs Agent Desk")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class PaymentApproval(BaseModel):
    kind: str = Field(min_length=1)
    ref_id: int
    amount: float = Field(gt=0)
    account: str = Field(min_length=1)
    approved_by: str = Field(min_length=1)

class TicketStatusUpdate(BaseModel):
    status: str = Field(pattern="^(open|in_progress|blocked|resolved)$")
    note: str = Field(min_length=1)

async def call_mcp(tool_name: str, arguments: dict) -> dict | list:
    async with Client(str(MCP_SERVER)) as client:
        return (await client.call_tool(tool_name, arguments)).data

@app.get("/api/health")
async def health() -> dict:
    return {"ok": True, "database": str(DB_PATH), "original_database": str(ORIGINAL_DB_PATH)}

@app.get("/api/tickets")
async def tickets() -> list[dict]:
    result = []
    for ticket_id in (101, 102, 103):
        context = await call_mcp("get_ticket_context", {"ticket_id": ticket_id})
        if not context.get("found"):
            raise HTTPException(404, f"Ticket {ticket_id} was not found")
        ticket = context["ticket"]
        invoice = context.get("invoice") or {}
        result.append({"id": ticket["id"], "subject": ticket["subject"], "type": ticket["type"], "status": ticket["status"], "requester": ticket["requester"], "notes": ticket["notes"], "requires_human_approval": bool(ticket.get("requires_human_approval", 0)), "approval_reason": ticket.get("approval_reason"), "payment_status": invoice.get("status")})
    return result

@app.post("/api/tickets/{ticket_id}/run")
async def run_ticket(ticket_id: int) -> dict:
    if ticket_id not in {101, 102, 103}:
        raise HTTPException(404, "Only tickets 101, 102, and 103 are in this assignment")
    context = await call_mcp("get_ticket_context", {"ticket_id": ticket_id})
    if not context.get("found"):
        raise HTTPException(404, f"Ticket {ticket_id} was not found")
    return (await run_team([ticket_id])).model_dump(mode="json")

@app.post("/api/tickets/{ticket_id}/status")
async def update_ticket_status(ticket_id: int, request: TicketStatusUpdate) -> dict:
    if ticket_id not in {101, 102, 103}:
        raise HTTPException(404, "Only tickets 101, 102, and 103 are in this assignment")
    result = await call_mcp("update_ticket_status", {"ticket_id": ticket_id, **request.model_dump()})
    if not result.get("updated"):
        raise HTTPException(400, result.get("error", "Ticket update refused"))
    return result

@app.get("/api/agent-events")
async def agent_events(limit: int = Query(100, ge=1, le=500)) -> list[dict]:
    if not AUDIT_PATH.exists():
        return []
    try:
        events = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(500, "Audit trail is not valid JSON") from exc
    return events[-limit:] if isinstance(events, list) else []

@app.post("/api/payments/approve")
async def approve_payment(request: PaymentApproval) -> dict:
    result = await call_mcp("make_human_approved_payment", request.model_dump())
    if not result.get("paid"):
        raise HTTPException(400, result.get("error", "Payment refused"))
    return result

@app.get("/api/cash/checking")
async def checking_balance() -> dict:
    context = await call_mcp("get_ticket_context", {"ticket_id": 102})
    checking = next((a for a in context.get("cash_accounts", []) if a.get("name") == "checking"), None)
    if checking is None:
        raise HTTPException(404, "Checking account was not found")
    return checking

@app.post("/api/reset")
async def reset_database() -> dict:
    if not ORIGINAL_DB_PATH.exists():
        raise HTTPException(500, "Original database is missing")
    temporary = DB_PATH.with_suffix(".reset.tmp")
    shutil.copy2(ORIGINAL_DB_PATH, temporary)
    temporary.replace(DB_PATH)
    return {"reset": True, "database": str(DB_PATH), "source": str(ORIGINAL_DB_PATH)}
