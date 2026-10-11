"""MCP tools for the Campus Customs ticket workflow."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from fastmcp import FastMCP

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "campus_customs_new.db"
mcp = FastMCP("campus-customs")

def _row(query: str, params: tuple = ()) -> dict | None:
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        result = connection.execute(query, params).fetchone()
        return dict(result) if result else None


@mcp.tool
def list_open_tickets() -> list[dict]:
    """List the currently open tickets for the Boss agent's bounded work queue."""
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute("SELECT id, type, requester, subject, sku, size, qty, lease_id, invoice_id, status, notes, created_at FROM tickets WHERE status = 'open' ORDER BY id").fetchall()
    return [dict(row) for row in rows]


@mcp.tool
def get_ticket_context(ticket_id: int) -> dict:
    """Read one ticket and its linked inventory, lease, invoice, vendor, pricing, and cash context."""
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        ticket = connection.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if ticket is None:
            return {"found": False, "ticket_id": ticket_id}
        result = {"found": True, "ticket": dict(ticket)}
        if ticket["sku"] and ticket["size"]:
            row = connection.execute("SELECT * FROM inventory WHERE sku = ? AND size = ?", (ticket["sku"], ticket["size"])).fetchone()
            result["inventory"] = dict(row) if row else None
            row = connection.execute("SELECT * FROM pricing WHERE sku = ?", (ticket["sku"],)).fetchone()
            result["pricing"] = dict(row) if row else None
        if ticket["lease_id"]:
            row = connection.execute("SELECT l.*, d.date_today FROM leases l CROSS JOIN desk d WHERE l.id = ?", (ticket["lease_id"],)).fetchone()
            result["lease"] = dict(row) if row else None
        if ticket["invoice_id"]:
            row = connection.execute("SELECT i.*, v.name AS vendor_name, v.specialty, v.lead_days FROM invoices i JOIN vendors v ON v.id = i.vendor_id WHERE i.id = ?", (ticket["invoice_id"],)).fetchone()
            result["invoice"] = dict(row) if row else None
        result["cash_accounts"] = [dict(row) for row in connection.execute("SELECT * FROM cash_accounts ORDER BY name").fetchall()]
        return result


@mcp.tool
def update_ticket_status(ticket_id: int, status: str, note: str) -> dict:
    """Update a ticket only with an explicit status and audit note; never sends communication."""
    allowed = {"open", "in_progress", "blocked", "resolved"}
    if status not in allowed or not note.strip():
        return {"updated": False, "error": "status must be open, in_progress, blocked, or resolved, and note is required"}
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute("UPDATE tickets SET status = ?, notes = CASE WHEN notes IS NULL OR notes = '' THEN ? ELSE notes || char(10) || ? END WHERE id = ?", (status, note.strip(), note.strip(), ticket_id))
        connection.commit()
        return {"updated": cursor.rowcount == 1, "ticket_id": ticket_id, "status": status, "note_added": note.strip()}


@mcp.tool
def make_human_approved_payment(kind: str, ref_id: int, amount: float, account: str, approved_by: str) -> dict:
    """Make an outgoing payment only when a named human approves it and cash remains non-negative."""
    if amount <= 0 or not approved_by.strip():
        return {"paid": False, "error": "positive amount and explicit human approved_by are required"}
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        cash = connection.execute("SELECT balance FROM cash_accounts WHERE name = ?", (account,)).fetchone()
        if cash is None:
            return {"paid": False, "error": "cash account not found"}
        if cash["balance"] < amount:
            return {"paid": False, "error": "insufficient funds; payment refused", "balance": cash["balance"], "amount": amount}
        payment_id = connection.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM payments").fetchone()[0]
        paid_at = connection.execute("SELECT date_today FROM desk").fetchone()[0]
        connection.execute("UPDATE cash_accounts SET balance = balance - ?, date = ? WHERE name = ?", (amount, paid_at, account))
        connection.execute("INSERT INTO payments (id, kind, ref_id, amount, account, paid_at, approved_by) VALUES (?, ?, ?, ?, ?, ?, ?)", (payment_id, kind, ref_id, amount, account, paid_at, approved_by.strip()))
        connection.commit()
        return {"paid": True, "payment_id": payment_id, "kind": kind, "ref_id": ref_id, "amount": amount, "account": account, "paid_at": paid_at, "approved_by": approved_by.strip(), "remaining_balance": cash["balance"] - amount}

@mcp.tool
def check_customer_order_inventory(sku: str, size: str, requested_qty: int) -> dict:
    """Check exact stock for customer-order ticket 101 without changing inventory."""
    if requested_qty < 1:
        return {"error": "requested_qty must be positive"}
    row = _row("SELECT sku, name, size, qty, location FROM inventory WHERE sku = ? AND size = ?", (sku, size))
    if row is None:
        return {"sku": sku, "size": size, "requested_qty": requested_qty, "found": False, "available": False}
    row.update({"requested_qty": requested_qty, "found": True, "available": row["qty"] >= requested_qty})
    return row

@mcp.tool
def get_rent_obligation_status(lease_id: int) -> dict:
    """Read the lease and shop date needed to resolve rent-notice ticket 102."""
    row = _row("""SELECT l.id AS lease_id, l.space_name, l.landlord, l.monthly_rent,
                        l.next_due, l.notes, d.date_today
                 FROM leases AS l CROSS JOIN desk AS d WHERE l.id = ?""", (lease_id,))
    if row is None:
        return {"lease_id": lease_id, "found": False}
    row["found"] = True
    row["overdue"] = row["next_due"] < row["date_today"]
    return row

@mcp.tool
def evaluate_bulk_price_and_stock(sku: str, size: str, requested_qty: int) -> dict:
    """Read price and exact size stock for bulk-price ticket 103."""
    if requested_qty < 1:
        return {"error": "requested_qty must be positive"}
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        pricing = connection.execute("SELECT sku, unit_cost, list_price FROM pricing WHERE sku = ?", (sku,)).fetchone()
        stock = connection.execute("SELECT sku, name, size, qty, location FROM inventory WHERE sku = ? AND size = ?", (sku, size)).fetchone()
    return {"sku": sku, "size": size, "requested_qty": requested_qty,
            "pricing": dict(pricing) if pricing else None,
            "inventory": dict(stock) if stock else None,
            "enough_stock": bool(stock and stock["qty"] >= requested_qty)}

if __name__ == "__main__":
    mcp.run()
