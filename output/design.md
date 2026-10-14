# Problem 8 — Dashboard design

I chose a sleek, organized operations-board look: a restrained navy, slate, and warm-gold palette, generous spacing, compact cards, and clear status colors. The hierarchy is intentionally simple: the top shows the shop identity and high-level metrics; the left column is the three-ticket queue; and the main panel focuses on one selected ticket, its run control, live agent activity, findings, and human approval.

The interface is designed to be easy to navigate without feeling cluttered. A supervisor can select one ticket, run the team, watch audit events arrive, review the short agent summaries, and see the checking balance in the same view. The Cash approval card is visually distinct because it changes real state and requires a human decision. Empty states explain what to do next rather than filling the page with placeholder content.

The frontend calls the FastAPI backend at `http://localhost:8000`, allows the Vite origins through backend CORS, and polls `/api/agent-events` while a ticket run is in progress. It uses no API key in the browser; Portkey access remains server-side.

## Review and reflection

During review, I found that the first version automatically marked tickets as resolved after an agent team finished its analysis. That was too strong: the findings sometimes showed that the underlying issue was still pending, such as an unavailable item, an upcoming rent obligation, or a customer request that still needed a decision. We corrected the workflow so an agent resolves a ticket only when its result explicitly says no human approval is required; otherwise it moves the ticket to `in_progress`, records the evidence and blocker, and flags it for human review. This lets agents finish routine work while preserving human control over consequential decisions.

### Implementation saga and reflection

The review exposed several important gaps that were useful to fix. The first dashboard version confused “agent analysis completed” with “ticket resolved,” and the original prompts treated every payment as requiring human approval even though the intended policy allowed funded, in-scope payments to proceed automatically. We aligned the prompts, database approval metadata, and dashboard wording so the authority boundary is explicit.

Testing also uncovered duplicate invoice payments, an invoice that remained open after payment, a concurrent balance-update race, raw tool-name arrays in the activity feed, and an unrelated payment button shown for every ticket. The final safeguards include duplicate-payment checks, serialized transactions, automatic invoice-status updates, explicit approval fields, ticket-specific payment controls, and human-readable audit activity. The main lesson is that reliable agents require coordinated prompts, database constraints, backend enforcement, audit records, and clear UI—not just a capable model.
