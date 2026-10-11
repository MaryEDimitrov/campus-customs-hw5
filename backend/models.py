"""Typed contracts shared by the Campus Customs agent team."""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field

Role = Literal["boss", "inventory", "accounting", "facilities", "customer_service"]


class AgentFinding(BaseModel):
    role: Role
    ticket_id: int
    recommendation: str
    evidence: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    needs_human_approval: bool = False
    proposed_next_step: str


class DelegationRecord(BaseModel):
    from_role: Role
    to_role: Role
    ticket_id: int
    task: str
    result_summary: str


class TeamRunResult(BaseModel):
    run_id: str
    ticket_ids: list[int]
    findings: list[AgentFinding]
    delegations: list[DelegationRecord] = Field(default_factory=list)
    final_plan: str
    human_approval_required: bool

