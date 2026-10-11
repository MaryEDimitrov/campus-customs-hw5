# Homework 5 — AI Prompt and Work Log

This file records the prompts, decisions, implementation notes, and verification performed while completing Homework 5.

## Assignment setup — 2026-10-11

### User request

Create `AI_prompts.md` at the start of the assignment and keep it updated as work progresses.

### Assistant action

Created this file before beginning Homework 5 implementation. The assignment prompt and grading rubric have not yet been provided.

### Next step

Add the Homework 5 prompt and rubric, then translate the requirements into an implementation and submission checklist.

## Problem sections

Each problem will have its own section using this structure:

## Problem [number] — [title]

### Requirement

<!-- Add the problem statement here. -->

### User prompts and decisions

<!-- Record relevant user requests, clarifications, and decisions here. -->

### Implementation notes

<!-- Record files changed, approach, and important tradeoffs here. -->

### Verification

<!-- Record tests, screenshots, or other evidence that the requirement is met. -->

### Completion status

- [ ] Requirement understood
- [ ] Implementation complete
- [ ] Verification complete
- [ ] Submission artifact reviewed

## Problem 2 — Set up the Campus Customs operations database

### Requirement

Use the supplied `data (6).zip` archive. Extract the original `data/campus_customs.db`, copy it to `data/campus_customs_new.db`, keep the original untouched, and configure the Homework 5 backend/MCP entry points to use the working copy. Study the shop tables, three open tickets, and operating rules before implementing ticket-resolution tools.

### User prompt and rules

The shop database includes `desk`, `tickets`, `inventory`, `pricing`, `vendors`, `leases`, `cash_accounts`, `payments`, and `invoices`. `desk.date_today` is the shop date; vendor lead times come from `vendors`; open unpaid vendor invoices block shipments; payments require human approval; balances may never go negative; only outgoing cash is modeled; and no real customer/vendor communication may occur. Use Portkey for future AI calls.

### Implementation notes

- Extracted `/Users/marydimitrov/Desktop/data (6).zip` into Homework 5.
- Created `data/campus_customs_new.db` as a byte-preserving copy of `data/campus_customs.db`.
- Added `backend/db_config.py` and an HW5-local `.mcp.json` pointing future backend/MCP work at the working copy.
- Started `output/harness.md` with the table map, joins, operating rules, and initial ticket snapshot.
- No ticket was resolved and no payment was made during setup.

### Verification

- Confirmed the archive contains `data/campus_customs.db`.
- Confirmed both database files exist and are 53,248 bytes.
- Confirmed the working copy contains the nine required tables.
- Confirmed three open tickets: IDs 101, 102, and 103.
- Confirmed the initial open vendor invoice is ID 501 and the checking balance is $3,400.
- Confirmed the original seed file was not used for writes.

### Completion status

- [x] New data archive extracted
- [x] Original seed database preserved
- [x] Working database copied
- [x] Backend/MCP working-copy paths established
- [x] Tables and operating rules documented
- [x] Three open tickets identified
- [ ] Ticket-resolution tools implemented

## Problem 3 — Build the MCP server

### Requirement

Build a FastMCP server in `mcp_server/` that reads `data/campus_customs_new.db`. Add three clear tools for tickets 101–103, document each in `output/harness.md`, and add `mcp_server/README.md`. The server does not need to be run in this problem.

### Implementation notes

- Added `mcp_server/mcp_server.py` with three read-only FastMCP tools tied to the three open tickets.
- Added tool-specific table, ticket, and rationale documentation to `output/harness.md`.
- Added `mcp_server/README.md` and `requirements.txt`.
- Updated the HW5-local `.mcp.json` to launch the new server path.
- No ticket update, payment, or server run was performed.

### Verification

- Confirmed each tool uses `data/campus_customs_new.db`.
- Confirmed the tools only execute `SELECT` queries.
- Confirmed the tool descriptions identify ticket 101, 102, or 103 and the specific facts needed.
- Confirmed the server source compiles syntactically without starting it.

### Completion status

- [x] FastMCP server created
- [x] Three ticket-specific tools added
- [x] Harness documentation updated
- [x] MCP README added
- [x] Server not run, as requested

## Problem 4 — Add the MCP server to the vibe coder and test each tool

### Requirement

Register the Homework 5 MCP server in the workspace configuration used by the vibe coder and test each of its three tools.

### Implementation notes

- Added `campus-customs-hw5` to the workspace-level `/Users/marydimitrov/AI Foundations/.mcp.json`.
- Installed FastMCP in the HW5 virtual environment.
- Used a FastMCP stdio client to discover and call all three tools.
- No ticket, payment, inventory, or database writes were made.

### Verification

- The vibe-coder configuration points to the HW5 `.venv` and `mcp_server/mcp_server.py` using absolute paths.
- The MCP client discovered exactly three tools.
- Ticket 101 test returned size-S stock `0` and `available: false`.
- Ticket 102 test returned lease 1 due `2026-09-02`, shop date `2026-08-31`, and `overdue: false`.
- Ticket 103 test returned hoodie size-M stock `8`, list price `$58`, unit cost `$22`, and `enough_stock: false`.
- Database hashes were unchanged after testing.

### Completion status

- [x] MCP server added to vibe-coder configuration
- [x] FastMCP dependency installed
- [x] All three tools discovered
- [x] All three tools tested
- [x] No database writes during testing

## Problem 5 — Build the agent team and grow the MCP tools

### Requirement

Build five PydanticAI roles—Boss, Inventory, Accounting, Facilities, and Customer Service—with one detailed prompt per role, typed models, bounded delegation loops, Portkey-backed `gpt-6-luna`, and full MCP connectivity. Add the MCP tools needed for the open-ticket workflow, append agent-loop audit events to `output/audit_trail.json`, and document all agents, tools, tables, and safety controls.

### Implementation notes

- Added role prompts under `backend/prompts/` with explicit shop rules, scope boundaries, approval requirements, no-contact rules, MCP-only evidence, privacy limits, and token/loop limits.
- Added typed contracts in `backend/models.py` for findings, delegation records, and team results.
- Added `backend/audit.py` with append-only audit-event behavior that filters secrets.
- Added `backend/team.py` with Portkey model construction, explicit `gpt-6-luna`, MCP stdio toolsets for every role, specialist delegation, Boss synthesis, and audit events for run/delegation/result/synthesis steps.
- Expanded `mcp_server/mcp_server.py` with `list_open_tickets`, `get_ticket_context`, `update_ticket_status`, and `make_human_approved_payment`.
- Updated `mcp_server/README.md` and `output/harness.md` to cover the full tool and agent maps.

### Prompt rules supplied for customization

Each prompt covers: authoritative MCP-only shop facts; `desk.date_today`; vendor lead times and open-invoice shipment blocks; human payment approval; no negative balances; outbound cash only; no real customer/vendor contact; privacy; exact ticket scope; evidence and blocker reporting; no invented prices, stock, dates, discounts, or revenue; and bounded agent/tool loops.

### Verification

- Installed PydanticAI/OpenAI/MCP dependencies in the HW5 virtual environment.
- Confirmed the new Python files compile syntactically.
- Confirmed the MCP tool source uses the working database path and the new write tools enforce safety checks.
- Agents were not run against Portkey and no ticket/payment database changes were made during setup.

### Completion status

- [x] Five clear agent roles
- [x] One prompt file per agent
- [x] Typed backend models
- [x] MCP-only agent tool connectivity wired
- [x] Additional MCP tools added
- [x] Append-only audit implementation added
- [x] Harness and MCP README updated
- [ ] Live Portkey agent run

### Prompt refinement

Added to `backend/prompts/boss.md`: the Boss must ensure every customer-facing response is polite, professional, clear, respectful, and helpful, including refusals and delays.

### Prompt voice refinement

Revised all five role prompts to use a consistent voice: a 27-year-old Yale MBA student supervising Campus Customs—polished, practical, warm, respectful, and direct—while keeping each agent’s scope and safety rules distinct.

## Problem 6 — Plan the three tickets

### Requirement

Before wiring backend writes, plan the expected work for tickets 101, 102, and 103. Include the first Boss delegation, the reason for that choice, the complete streamlined delegation sequence, and the expected MCP tools. Leave room for actual results after the agents run. Include blank or “coming later” Cash and Reflection tabs.

### Implementation notes

- Created `output/desk_tickets.html` with tabs for tickets 101, 102, 103, Cash, and Reflection.
- Added first-person supervisor explanations for who the Boss should call first and why.
- Added ticket-specific expected MCP calls, including conditional status and payment writes.
- Kept the plans efficient: ticket 101 is Inventory → Customer Service; ticket 102 is Facilities → Accounting only if payment is relevant; ticket 103 is Inventory → Accounting → Customer Service, with Facilities only if a replenishment blocker appears.
- Left an empty Actual Agent Results section on every ticket tab for the post-run comparison.
- No agents were run and no database records were changed while creating the plan.

### Completion status

- [x] Three ticket tabs created
- [x] First delegation and reason documented for each ticket
- [x] Streamlined delegation sequences documented
- [x] Expected MCP tools documented for each run
- [x] Cash and Reflection tabs reserved
- [x] Actual-results sections reserved

## Problem 7 — Backend routes

### Requirement

Add FastAPI routes for the React dashboard: return tickets 101–103 and status, run the agent team for one ticket, return recent agent events, execute a human-approved payment/purchase, return the checking balance, and reset the working database from the untouched original.

### Implementation notes

- Added `backend/main.py` with ticket/status, agent-run, event, payment-approval, checking-balance, reset, and health routes.
- Dashboard reads and payment execution call the MCP server rather than adding a second database tools layer.
- The reset route copies `data/campus_customs.db` over `data/campus_customs_new.db` through a temporary file.
- Payment requests require a named human approver and are rejected by MCP when funds are insufficient.
- No server was started and no agents, payments, ticket writes, or resets were run during implementation.

### Verification

- Confirmed the backend source compiles.
- Confirmed routes use FastAPI/Pydantic models.
- Confirmed route code uses the working database through MCP and keeps the original as reset source.

### Completion status

- [x] Ticket/status route
- [x] Agent-run route
- [x] Recent-events route
- [x] Human-approved payment route
- [x] Checking-balance route
- [x] Reset route

## Problem 8 — Run the full board and record resolved tickets

### Requirement

Reset `data/campus_customs_new.db` from the untouched seed, run tickets 101, 102, and 103 to resolution, preserve the Expected sections from Problem 6, and record actual agent work, tool use, cash movement, resolved-ticket evidence, board snapshots, and audit events.

### Implementation notes

- Reset the working database before the full run; the seed database remains untouched.
- Ran the streamlined plans: 101 Inventory → Customer Service; 102 Facilities → Accounting; 103 Inventory → Accounting → Customer Service.
- No payment or purchase was approved or executed. No external customer or vendor communication was sent; customer-facing content stayed as drafts.
- Updated `output/desk_tickets.html` with Actual sections and a cash reconciliation tab, created `output/resolved_tickets.json`, and created `output/resolved_board.html`.
- Appended the real run events to `output/audit_trail.json` without removing earlier test evidence.

### Verification

- Tickets 101, 102, and 103 are `resolved` in the working database.
- Starting checking balance after reset: `$3,400.00`.
- Cash changes: ticket 101 `$0.00`; ticket 102 `$0.00`; ticket 103 `$0.00`.
- Ending checking balance: `$3,400.00`, matching `cash_accounts`.
- No human approvals were recorded and the `payments` table remains empty.
- Run IDs are recorded in `output/resolved_tickets.json`; audit evidence is append-only in `output/audit_trail.json`.

### Completion status

- [x] Working database reset before full run
- [x] All three tickets resolved
- [x] Expected and Actual board sections preserved
- [x] Cash reconciliation recorded
- [x] Resolved-ticket JSON and board evidence created
- [x] Audit trail appended

## Problem 10 — Reflection draft

### Requirement

Prepare bullet-point notes for the reflection: evaluate each agent on each ticket, compare Actual with Expected, explain the one-agent alternative, and identify three new problems the team could solve.

### Notes

- Inventory was strong at exact stock evidence but should be rated 8/10 because it could not create stock, resolve the unpaid-invoice blocker, or contact the vendor. Customer Service was strongest at polite, professional drafts. Facilities correctly handled date-based rent logic but should be rated 8/10 because it could not make payments, authorize cash movement, or communicate with the landlord and depended on Accounting for the financial decision. Accounting correctly protected cash and approval controls, and Boss kept the final run streamlined. The main limitation for every role was that agents could prepare evidence or drafts but could not invent stock, contact people, or make unapproved payments.
- Actual matched Expected on all three tickets: 101 used Inventory → Customer Service, 102 used Facilities → Accounting, and 103 used Inventory → Accounting → Customer Service. No unnecessary fourth specialist was sent.
- One agent with tools would use fewer handoffs and tokens for simple cases, but the specialist design provides better separation of duties and safety around money, customer tone, and delegation.
- The three possible new Campus Customs problems for the reflection are product defects, returns and refunds, and customer order changes.
- The first attempts did not fully follow the streamlined plan and included incorrect/exploratory runs. Those events were preserved in the append-only audit trail. I corrected the orchestration, reset the working database, and then completed the final run with only the relevant specialists on each ticket. This was an important lesson about planning, resetting, and auditing agent work.
- A positive result was the corrected streamlined design: it reduced unnecessary handoffs and token use while still giving each ticket the right expertise. Ticket 101 used Inventory and Customer Service, 102 used Facilities and Accounting, and 103 used Inventory, Accounting, and Customer Service.
- The full bullet draft is in the Reflection tab of `output/desk_tickets.html` and in the Problem 10 section of `output/harness.md`.

### Completion status

- [x] Reflection bullets drafted
- [x] Expected-versus-Actual comparison included
- [x] One-agent alternative evaluated
- [x] Three new team problems included
- [x] Live backend smoke test

## Problem 8 — Agent Dashboard

### Requirement

Build a React + Vite + TypeScript dashboard in `frontend/` that calls the Problem 7 routes, lists and selects the three tickets, runs a selected team, shows agent events and summaries, marks a completed ticket resolved, supports human payment approval, displays checking balance, and uses an organized, uncluttered design. Allow the Vite origin through backend CORS and document the design choices.

### Implementation notes

- Added a React/Vite/TypeScript frontend with ticket queue, selected-ticket run control, live audit-event polling, agent findings, payment approval, checking balance, and refresh controls.
- Added `backend` CORS for `localhost:5173` and `127.0.0.1:5173`.
- Added a backend ticket-status route so the dashboard can record resolution after a completed run.
- Wrote the visual rationale in `output/design.md`.
- No API key is sent to the browser.

### Verification

- Frontend source and configuration added under `frontend/`.
- Backend source compiles after the CORS and status-route additions.
- Frontend was not started yet in this step.

### Completion status

- [x] Ticket list and selection
- [x] Team-run control
- [x] Live agent-event display
- [x] Agent summary display
- [x] Resolution update route
- [x] Human payment control
- [x] Checking balance display
- [x] Vite-origin CORS
- [x] Design document
- [x] Start Vite and perform browser smoke test

### Problem 8 verification update

- Installed frontend dependencies.
- Fixed missing React/Vite TypeScript declarations.
- `npm run build` passes.
- Vite is running at `http://localhost:5173/` and the served HTML was verified.

## MCP smoke-test evidence

Saved the three successful MCP client calls, including each vibe-coder prompt, tool name, arguments, and exact tool output, in `output/mcp_smoke.json`. The outputs were read from `data/campus_customs_new.db`; no database writes occurred.

