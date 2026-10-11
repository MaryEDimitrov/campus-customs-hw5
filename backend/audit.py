"""Append-only audit events for agent loops."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUDIT_PATH = Path(__file__).resolve().parent.parent / "output" / "audit_trail.json"


def append_audit_event(run_id: str, step: int, role: str, event_type: str, **details: Any) -> None:
    """Append an event without deleting prior runs or exposing secrets."""
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if AUDIT_PATH.exists():
        try:
            existing = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
            if not isinstance(existing, list):
                existing = []
        except json.JSONDecodeError:
            existing = []
    else:
        existing = []
    safe_details = {key: value for key, value in details.items() if key not in {"api_key", "password", "password_hash", "raw_prompt"}}
    existing.append({
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "step": step,
        "role": role,
        "event_type": event_type,
        "details": safe_details,
    })
    AUDIT_PATH.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

