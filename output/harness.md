# Campus Customs Operations Harness

Working database: `data/campus_customs_new.db`. The seed `data/campus_customs.db` must remain untouched. Backend and MCP code must use the working-copy path from `backend/db_config.py`.

## Tables and agent relevance

| Table | Important fields | Why it matters |
|---|---|---|
| `desk` | `date_today`, `notes` | The shop’s authoritative “today”; all overdue calculations use `date_today`, not the computer clock. |
| `tickets` | `id`, `type`, `requester`, `subject`, `sku`, `size`, `qty`, `lease_id`, `invoice_id`, `status`, `notes`, `created_at` | The work queue; agents resolve open tickets and link orders, rent notices, and pricing requests to the supporting records. |
| `inventory` | `sku`, `name`, `size`, `qty`, `location` | Current stock and shelf location; customer-order decisions must use this table and never create negative quantity. |
| `pricing` | `sku`, `unit_cost`, `list_price` | Cost and list-price truth for pricing requests and margin calculations. |
| `vendors` | `id`, `name`, `specialty`, `lead_days` | Vendor identity, capability, and shipping lead time; lead days are required for delivery estimates. |
| `leases` | `id`, `space_name`, `landlord`, `monthly_rent`, `next_due`, `notes` | Rent obligations and due dates for lease-related tickets. |
| `cash_accounts` | `name`, `balance`, `date` | Available cash; every outgoing payment must be approved and must leave a non-negative balance. |
| `payments` | `id`, `kind`, `ref_id`, `amount`, `account`, `paid_at`, `approved_by` | Immutable-style payment record and approval evidence after a human authorizes payment. |
| `invoices` | `id`, `vendor_id`, `amount`, `due_date`, `status`, `description` | Vendor obligations; an unpaid open invoice blocks new vendor shipments. |

## Relationships

- `tickets.lease_id → leases.id` for rent notices.
- `tickets.invoice_id → invoices.id` for invoice/payment work.
- `tickets.sku + tickets.size → inventory.sku + inventory.size` for product requests.
- `invoices.vendor_id → vendors.id` for vendor identity and lead time.
- `payments.ref_id` is the related business record ID according to `payments.kind`.

## Operating rules

1. Use `desk.date_today` as the shop date for overdue logic.
2. Use `vendors.lead_days` for shipment timing.
3. Do not ship a new product from a vendor with an unpaid/open invoice.
4. Human approval is required before any payment; a tool must refuse unapproved payment requests.
5. Refuse any payment that would make a `cash_accounts.balance` negative.
6. Outgoing cash only is modeled; no revenue is created.
7. Never email customers or contact vendors; drafts remain on the board.
8. Reset from `data/campus_customs.db` before a full ticket-resolution run.

## Initial ticket snapshot

The working copy starts with three open tickets: customer order `101`, rent notice `102`, and price override `103`. It also starts with an open vendor invoice `501` for the Bulldog tee reprint, which is relevant to vendor-shipment decisions.

## Problem 3 — Initial MCP tools

| MCP tool | Tables read | Ticket unlocked | Why this is the right tool |
|---|---|---|---|
| `check_customer_order_inventory(sku, size, requested_qty)` | `inventory` | 101 | Ticket 101 asks for one `CC-TEE-WHITE` in size `S`, so this exact SKU/size lookup determines whether the requested order can be fulfilled without changing stock. |
| `get_rent_obligation_status(lease_id)` | `leases`, `desk` | 102 | Ticket 102 is a rent notice linked to lease `1`, so this join compares the lease’s `next_due` date with authoritative `desk.date_today`. |
| `evaluate_bulk_price_and_stock(sku, size, requested_qty)` | `pricing`, `inventory` | 103 | Ticket 103 requests 20 `CC-HOOD-NAVY` hoodies in size `M`, so the tool returns database prices and exact available quantity before a discount is evaluated. |

All three tools are read-only and return database facts; they do not update tickets, cash, payments, inventory, or prices.

## Complete MCP tool map after Problem 5

| MCP tool | Reads / writes | Agent users | Ticket/workflow purpose |
|---|---|---|---|
| `list_open_tickets` | Reads `tickets` | Boss | Gives Boss the bounded current work queue instead of inventing ticket IDs. |
| `get_ticket_context` | Reads `tickets`, `inventory`, `pricing`, `leases`, `desk`, `invoices`, `vendors`, `cash_accounts` | Boss, Inventory, Accounting, Facilities, Customer Service | Builds the linked evidence packet for one ticket so specialists reason over the same database facts. |
| `check_customer_order_inventory` | Reads `inventory` | Inventory, Customer Service | Checks ticket 101’s exact Bulldog tee SKU/size/quantity before promising fulfillment. |
| `get_rent_obligation_status` | Reads `leases`, `desk` | Facilities, Accounting | Checks ticket 102’s lease due date against the authoritative shop date. |
| `evaluate_bulk_price_and_stock` | Reads `pricing`, `inventory` | Inventory, Accounting, Customer Service | Checks ticket 103’s hoodie cost/list price and size-M quantity before a discount recommendation. |
| `update_ticket_status` | Writes `tickets` | Boss (after evidence), specialists only through delegation | Records a bounded internal state change with a required note; it does not communicate externally. |
| `make_human_approved_payment` | Writes `payments`, updates `cash_accounts`, reads `desk` | Accounting only | Executes an outgoing payment only after a named human approval and a non-negative cash check. |

## Agent team and prompt rules

| Agent | Scope | Must do | Must not do |
|---|---|---|---|
| Boss | Queue ownership, delegation, synthesis | Delegate by ticket, require MCP evidence, stop for approval | Invent facts, pay, contact people, or close work without evidence |
| Inventory | SKU/size/quantity/location and vendor shipment blockers | Verify exact stock and vendor invoice state | Guess stock, create negative inventory, promise delivery |
| Accounting | Invoices, rent amounts, cash, payments | Check due/status/balance and require named human approval | Pay without approval, create revenue, allow negative cash |
| Facilities | Lease and shop operations | Use `desk.date_today` and prepare internal drafts | Use computer time, contact landlord/vendor, authorize payment |
| Customer Service | Safe customer-facing drafts | Communicate only verified facts and label drafts | Send messages, promise discounts/refunds, invent shipping |

Safety controls: all shop facts flow through MCP; prompts prohibit a second database layer; payment tools require `approved_by`, positive amounts, and sufficient funds; no incoming cash is modeled; real communications are drafts only; agent loops are bounded by requested tickets, one specialist delegation per role/ticket, tool retries, and a finite run; audit events omit API keys, passwords, raw prompts, and other secrets.

## Problem 6 — Ticket planning artifact

The expected delegation plans and MCP call sequence are in [`desk_tickets.html`](desk_tickets.html). The plan is intentionally streamlined so the live run can be compared against a specific expected sequence rather than a vague instruction to call every specialist.

## Problem 7 — Backend route map

- `GET /api/tickets` — Returns tickets 101–103 and their current statuses through MCP context reads.
- `POST /api/tickets/{ticket_id}/run` — Runs the agent team for one assignment ticket; agents prepare findings but do not approve payments.
- `POST /api/tickets/{ticket_id}/status` — Records an evidence-backed ticket status/note, including the dashboard’s post-run resolution update.
- `GET /api/agent-events` — Returns recent append-only agent events for refreshing the dashboard without exposing secrets.
- `POST /api/payments/approve` — Executes an outgoing payment only with named human approval and MCP cash-safety checks.
- `GET /api/cash/checking` — Returns the current checking-account balance through MCP.
- `POST /api/reset` — Restores `data/campus_customs_new.db` from the untouched original seed database.

## Problem 4 — Vibe-coder MCP connection and tests

The workspace-level `.mcp.json` now registers `campus-customs-hw5` with the absolute HW5 virtualenv and `mcp_server/mcp_server.py` path. A FastMCP stdio client successfully discovered all three tools and called each one against `data/campus_customs_new.db`.

| Tool test | Result |
|---|---|
| Ticket 101: `CC-TEE-WHITE`, size `S`, quantity `1` | Found inventory row; quantity is `0`; `available` is `false`. |
| Ticket 102: lease `1` | Found Chapel Street shop lease; due `2026-09-02`, shop date `2026-08-31`, so `overdue` is `false`. |
| Ticket 103: `CC-HOOD-NAVY`, size `M`, quantity `20` | Found pricing and inventory; list price `$58`, unit cost `$22`, stock `8`; `enough_stock` is `false`. |

The database SHA-256 hashes remained identical before and after testing, confirming that the MCP calls did not write to either database.

## Problem 8 — Full-run evidence

The working database was reset from the untouched seed before the full run. The three successful runs used the streamlined plans below; earlier failed or exploratory audit events remain in the append-only audit file.

| Ticket | Actual delegation | Tools used | Final status | Run ID |
|---|---|---|---|---|
| 101 | Inventory → Customer Service | `get_ticket_context`, `check_customer_order_inventory` | `resolved` | `d591c77d-2694-4a76-8921-2611271013ac` |
| 102 | Facilities → Accounting | `get_ticket_context`, `get_rent_obligation_status` | `resolved` | `e760198c-1be4-41c9-b799-6dc4a89dcd7d` |
| 103 | Inventory → Accounting → Customer Service | `get_ticket_context`, `evaluate_bulk_price_and_stock` | `resolved` | `7f53ff2c-56d2-4a86-a847-2b9cebc8eb46` |

`output/desk_tickets.html` keeps each Problem 6 Expected plan beside the corresponding Actual results. `output/resolved_tickets.json` contains each agent contribution, tools, outcome, approval list, and financial change. `output/audit_trail.json` contains the append-only event history.

### Cash reconciliation

| Item | Change |
|---|---:|
| Starting checking balance after reset | $3,400.00 |
| Ticket 101 — no payment or purchase | $0.00 |
| Ticket 102 — rent upcoming, no approved payment | $0.00 |
| Ticket 103 — no purchase or discount payment | $0.00 |
| Ending checking balance (`cash_accounts`) | $3,400.00 |

No human approvals occurred, the `payments` table is empty, and no balance-changing route was called. The cash equation is `$3,400.00 + $0.00 - $0.00 = $3,400.00`.

## Problem 8 — Submission artifact map

- `output/desk_tickets.html` — comparison board with Expected, Actual, Cash, and Reflection tabs.
- `output/resolved_board.html` — double-clickable resolved board evidence for tickets 101–103.
- `output/resolved_tickets.json` — machine-readable outcomes, contributions, tools, approvals, and cash changes.
- `output/audit_trail.json` — append-only agent-loop events, including the three successful run IDs.

## Problem 10 — Reflection draft

### 1. How each agent performed

- **Ticket 101 — Inventory:** Good: checked the exact SKU, size, and quantity and caught zero stock plus the replenishment blocker. Limitation: it could report the shortage but could not create stock, resolve the unpaid-invoice blocker, or contact the vendor.
- **Ticket 101 — Customer Service:** Good: created a polite, professional draft from verified facts without promising a restock date. Limitation: it could not fix the inventory shortage.
- **Ticket 102 — Facilities:** Good: used `desk.date_today` and correctly classified the $2,400 rent as upcoming, not overdue. Limitation: it could not make the payment, authorize cash movement, or communicate with the landlord; it also depended on Accounting for the financial decision.
- **Ticket 102 — Accounting:** Good: checked the obligation and balance and respected human approval. Limitation: it did not pay because no approval existed, which was the correct safety result.
- **Ticket 103 — Inventory:** Good: identified 8 available versus 20 requested, clearly showing a 12-unit shortage. Limitation: it could not solve the shortage itself.
- **Ticket 103 — Accounting:** Good: verified the $22 unit cost and $58 list price without inventing a discount. Limitation: no purchase could proceed without authorization.
- **Ticket 103 — Customer Service:** Good: prepared a clear shortage draft using verified quantity and pricing facts. Limitation: it could not promise an alternative or delivery date.

### 2. Actual compared with the Expected plan

- **101:** Matched the expected Inventory → Customer Service sequence and expected tools; no extra specialist was sent.
- **102:** Matched Facilities → Accounting; Accounting reviewed payment implications and correctly stopped without human approval.
- **103:** Matched Inventory → Accounting → Customer Service; Facilities was not needed because no facilities or replenishment investigation was required.
- **Overall:** The actual run followed the streamlined plan, resolved all three tickets, and changed no cash.
- **Process lesson:** The first attempts were not fully streamlined and included incorrect/exploratory runs. Those events remain in the append-only audit trail. I corrected the orchestration, reset the working database, and then ran the final clean sequence with only the relevant specialists on each ticket. This shows why the Expected plan, reset step, and audit trail matter.
- **What worked well:** The corrected streamlined design was a strong part of the final run. It reduced unnecessary handoffs and token use while still giving each ticket the right expertise: Inventory and Customer Service for 101, Facilities and Accounting for 102, and Inventory, Accounting, and Customer Service for 103.

### 3. What would be simpler as one agent with tools?

- One agent could read each ticket, call only the relevant MCP tool, summarize the evidence, and update status with fewer handoffs and lower token use.
- That would be simpler for straightforward tickets such as 101 and 102.
- The specialist team is safer for separation of duties: Accounting checks money, Customer Service owns tone, and Boss controls delegation. A one-agent design would still need strict tool permissions, bounded loops, and human approval because it could otherwise miss a safety check or make an overconfident promise.

### 4. Three new problems the team could solve

- **Inventory shortages:** Inventory checks stock, and Customer Service communicates verified alternatives to the customer.
- **Facilities issues:** Facilities investigates the problem, and Customer Service communicates any impact on customers.
- **Payment questions:** Accounting investigates the charge, and Customer Service helps address the customer’s concern.

Possible future extensions: Returns and Refunds (Returns Specialist and eligibility/refund tools); Supplier Performance Problems (Procurement Specialist and delivery/vendor-draft tools); Product Defects (Quality Assurance Specialist and complaint-pattern, inventory-flagging, and safety-escalation tools).

### Three possible new problems Campus Customs might face

- **Product defects:** Customers may report damaged or unsafe merchandise. A Quality Assurance Specialist could identify complaint patterns, flag affected inventory, and escalate safety concerns.
- **Returns and refunds:** Customers may want to return an item or receive a refund. A Returns Specialist could check eligibility, while Accounting handles only authorized refunds.
- **Customer order changes:** A customer may request a new size, pickup time, or delivery detail after ordering. Customer Service could draft the response while Inventory verifies whether the change is possible.
