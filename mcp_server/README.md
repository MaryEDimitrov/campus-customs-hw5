# Campus Customs MCP server

This FastMCP server gives Homework 5 agents narrow, database-backed tools for the current ticket queue. It reads `../data/campus_customs_new.db`, the working copy; the original `../data/campus_customs.db` is never opened for writes.

The initial read-only tools are:

1. `check_customer_order_inventory` reads `inventory` for ticket 101’s Bulldog tee and requested size.
2. `get_rent_obligation_status` reads `leases` and `desk` for ticket 102’s rent due date and shop date.
3. `evaluate_bulk_price_and_stock` reads `pricing` and `inventory` for ticket 103’s bulk hoodie price and size-M stock.

The team-workflow tools added later are:

4. `list_open_tickets` reads the `tickets` work queue.
5. `get_ticket_context` reads a ticket and its linked shop records.
6. `update_ticket_status` writes a ticket status and required note, but never communicates externally.
7. `make_human_approved_payment` writes a payment only with a named human approver, sufficient cash, and a non-negative resulting balance.

All tools use the MCP server’s `../data/campus_customs_new.db` path. No agent may bypass MCP with a second database tool layer.
