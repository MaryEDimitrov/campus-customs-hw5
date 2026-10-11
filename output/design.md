# Problem 8 — Dashboard design

I chose a sleek, organized operations-board look: a restrained navy, slate, and warm-gold palette, generous spacing, compact cards, and clear status colors. The hierarchy is intentionally simple: the top shows the shop identity and high-level metrics; the left column is the three-ticket queue; and the main panel focuses on one selected ticket, its run control, live agent activity, findings, and human approval.

The interface is designed to be easy to navigate without feeling cluttered. A supervisor can select one ticket, run the team, watch audit events arrive, review the short agent summaries, and see the checking balance in the same view. The Cash approval card is visually distinct because it changes real state and requires a human decision. Empty states explain what to do next rather than filling the page with placeholder content.

The frontend calls the FastAPI backend at `http://localhost:8000`, allows the Vite origins through backend CORS, and polls `/api/agent-events` while a ticket run is in progress. It uses no API key in the browser; Portkey access remains server-side.
