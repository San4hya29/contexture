"""
Natural-language query router for the PostgreSQL agent.

Maps simple keyword patterns to tool calls — mirrors mongodb/agent.py.
For richer NL→workflow routing, the main client_dynamic.py / client_dynamic_ui.py
pipeline is used instead (it talks to the FastMCP server directly via Ollama).
"""

from tool_registry import TOOLS


def process_query(query: str) -> dict:
    q = query.lower()

    if "health" in q or "status" in q:
        return TOOLS["check_db_health"]()

    if "slow" in q or "performance" in q or "latency" in q:
        return TOOLS["get_slow_queries"]()

    if "stat" in q and ("db" in q or "database" in q):
        return TOOLS["get_db_stats"]()

    if ("stat" in q or "size" in q or "row" in q) and ("table" in q):
        # expect "stats for table <schema>.<table>" or similar
        parts = q.split()
        schema, table = "public", ""
        for i, p in enumerate(parts):
            if "." in p:
                schema, table = p.split(".", 1)
            elif p == "table" and i + 1 < len(parts):
                table = parts[i + 1]
        if table:
            return TOOLS["get_table_stats"](schema=schema, table=table)
        return {"message": "Please specify table name, e.g. 'stats for table public.users'"}

    if "describe" in q or "schema of" in q or "columns" in q:
        parts = q.split()
        schema, table = "public", ""
        for p in parts:
            if "." in p:
                schema, table = p.split(".", 1)
        if table:
            return TOOLS["describe_table"](schema=schema, table=table)
        return {"message": "Please specify table, e.g. 'describe public.orders'"}

    if "explain" in q:
        sql = query.strip()
        for kw in ["explain", "Explain", "EXPLAIN"]:
            sql = sql.replace(kw, "").strip()
        return TOOLS["explain_query"](sql=sql) if sql else {"message": "Provide a SQL query to explain."}

    if "select" in q or "query" in q:
        # Pull out the SQL portion after "query:" or "run:" prefix if present
        sql = query
        for prefix in ["query:", "run:", "execute:"]:
            if prefix in q:
                sql = query[q.index(prefix) + len(prefix):].strip()
                break
        return TOOLS["execute_query"](sql=sql)

    if "table" in q:
        schema = "public"
        parts = q.split()
        for i, p in enumerate(parts):
            if p in ("schema", "in") and i + 1 < len(parts):
                schema = parts[i + 1]
        return TOOLS["list_tables"](schema=schema)

    if "schema" in q:
        return TOOLS["list_schemas"]()

    if "database" in q or "db" in q:
        return TOOLS["list_databases"]()

    return {"message": "No matching tool found. Try asking about databases, schemas, tables, health, slow queries, or run a SELECT."}
