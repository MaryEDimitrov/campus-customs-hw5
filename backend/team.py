"""Portkey-backed five-agent team with MCP connectivity and delegation."""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
from contextlib import AsyncExitStack
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.mcp import MCPServerStdio

try:
    from .audit import append_audit_event
    from .models import AgentFinding, DelegationRecord, Role, TeamRunResult
except ImportError:
    from audit import append_audit_event
    from models import AgentFinding, DelegationRecord, Role, TeamRunResult

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = ROOT / "backend" / "prompts"
MODEL_NAME = "gpt-6-luna"
ROLES: tuple[Role, ...] = ("boss", "inventory", "accounting", "facilities", "customer_service")


def make_model() -> OpenAIChatModel:
    load_dotenv(ROOT.parent.parent / ".env")
    api_key = os.environ.get("PORTKEY_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("PORTKEY_API_KEY is required for agent runs")
    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.portkey.ai/v1",
        default_headers={"x-portkey-api-key": api_key, "x-portkey-provider": "openai"},
    )
    return OpenAIChatModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))


def build_agents(model: OpenAIChatModel, servers: dict[Role, MCPServerStdio]) -> dict[Role, Agent]:
    return {
        role: Agent(model, output_type=AgentFinding, system_prompt=(PROMPTS / f"{role}.md").read_text(encoding="utf-8"), toolsets=[servers[role]], model_settings={"openai_reasoning_effort": "none"}, retries=2, name=f"campus_customs_{role}")
        for role in ROLES
    }


async def run_team(ticket_ids: list[int]) -> TeamRunResult:
    """Run bounded specialist loops; MCP tool attachment is added by the MCP adapter."""
    run_id = str(uuid.uuid4())
    append_audit_event(run_id, 0, "boss", "run_start", ticket_ids=ticket_ids, model=MODEL_NAME)
    server_path = ROOT / "mcp_server" / "mcp_server.py"
    async with AsyncExitStack() as stack:
        servers = {}
        for role in ROLES:
            servers[role] = await stack.enter_async_context(MCPServerStdio(sys.executable, [str(server_path)], cwd=str(ROOT), read_timeout=120))
        agents = build_agents(make_model(), servers)
        findings: list[AgentFinding] = []
        delegations: list[DelegationRecord] = []
        step = 1
        delegation_plan: dict[int, tuple[Role, ...]] = {
            101: ("inventory", "customer_service"),
            102: ("facilities", "accounting"),
            103: ("inventory", "accounting", "customer_service"),
        }
        for ticket_id in ticket_ids:
            for role in delegation_plan.get(ticket_id, ("customer_service",)):
                append_audit_event(run_id, step, "boss", "delegation_start", to_role=role, ticket_id=ticket_id)
                result = await agents[role].run(f"Analyze ticket {ticket_id}. Use MCP tools for every shop fact and return a typed finding.")
                finding = result.output
                findings.append(finding)
                tool_names = []
                for message in result.all_messages():
                    for part in getattr(message, "parts", []):
                        if getattr(part, "tool_name", None):
                            tool_names.append(part.tool_name)
                delegations.append(DelegationRecord(from_role="boss", to_role=role, ticket_id=ticket_id, task="Analyze the ticket using MCP facts", result_summary=finding.recommendation[:300]))
                append_audit_event(run_id, step + 1, role, "agent_result", ticket_id=ticket_id, recommendation=finding.recommendation[:300], tool_names=tool_names)
                step += 2
        summary = "; ".join(f"ticket {f.ticket_id} ({f.role}): {f.recommendation[:240]}" for f in findings)
        append_audit_event(run_id, step, "boss", "synthesis_start", finding_count=len(findings))
        boss_result = await agents["boss"].run(f"Synthesize these specialist findings into a safe plan. Do not take action; require human approval for payments. Findings: {summary}")
        final_plan = boss_result.output.recommendation
        append_audit_event(run_id, step + 1, "boss", "synthesis_result", recommendation=final_plan[:500])
        append_audit_event(run_id, step + 2, "boss", "run_end", finding_count=len(findings), human_approval_required=True)
        return TeamRunResult(run_id=run_id, ticket_ids=ticket_ids, findings=findings, delegations=delegations, final_plan=final_plan, human_approval_required=True)

