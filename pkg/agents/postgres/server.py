# server.py — PostgreSQL MCP Server for SODA Contexture
#
# Implements the same FastMCP @app.tool() pattern as pkg/mcp/server.py.
# Connects to PostgreSQL instances defined in config/postgres_config.yaml.
#
# Inspired by open-source PostgreSQL MCP servers:
#   - crystaldba/postgres-mcp  (https://github.com/crystaldba/postgres-mcp)
#   - modelcontextprotocol/servers/src/postgres  (https://github.com/modelcontextprotocol/servers)
#
# Run (always from the pkg/agents/postgres/ directory):
#   python server.py                          # stdio transport (default)
#   python server.py --transport sse          # SSE/HTTP on port 8003
#   python server.py --transport sse --port 9000  # custom port

import os
import yaml
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from postgres_connector import (
    get_all_instances,
    list_databases,
    list_schemas,
    list_tables,
    describe_table,
    execute_query,
    explain_query,
    get_table_stats,
    get_db_stats,
    get_slow_queries,
    check_db_health,
)

app = FastMCP("PostgreSQL MCP Server")

# ── lazy-load instances ───────────────────────────────────────────────────────

def _instances() -> List[Dict]:
    try:
        return get_all_instances()
    except FileNotFoundError as e:
        print(f"[postgres-mcp] WARNING: {e}")
        return []


# ── tools ─────────────────────────────────────────────────────────────────────

@app.tool()
def pg_list_databases() -> Dict[str, Any]:
    """
    List all non-template PostgreSQL databases across configured instances.
    Returns name, owner, encoding, collation, and size for each database.
    Useful for understanding what databases exist and their storage footprint.
    """
    all_results = {}
    for inst in _instances():
        name = inst.get("name", "default")
        try:
            all_results[name] = list_databases(inst)
        except Exception as e:
            all_results[name] = {"error": str(e)}

    return {
        "databases_per_instance": all_results,
        "timestamp": datetime.now().isoformat(),
    }


@app.tool()
def pg_list_schemas() -> Dict[str, Any]:
    """
    List all user-visible schemas in the connected database (excludes system schemas).
    Schemas partition a database into logical namespaces — knowing them is the
    first step to understanding data organisation.
    """
    all_results = {}
    for inst in _instances():
        name = inst.get("name", "default")
        try:
            all_results[name] = list_schemas(inst)
        except Exception as e:
            all_results[name] = {"error": str(e)}

    return {
        "schemas_per_instance": all_results,
        "timestamp": datetime.now().isoformat(),
    }


@app.tool()
def pg_list_tables(schema: str = "public") -> Dict[str, Any]:
    """
    List all tables and views in the given schema.
    Returns table_name and table_type (BASE TABLE or VIEW) for each entry.

    Args:
        schema: Schema name to query (default: 'public').
    """
    all_results = {}
    for inst in _instances():
        name = inst.get("name", "default")
        try:
            all_results[name] = list_tables(inst, schema)
        except Exception as e:
            all_results[name] = {"error": str(e)}

    return {
        "schema": schema,
        "tables_per_instance": all_results,
        "timestamp": datetime.now().isoformat(),
    }


@app.tool()
def pg_describe_table(schema: str, table: str) -> Dict[str, Any]:
    """
    Return the full structure of a table: columns (name, type, nullability, default),
    primary keys, and indexes. Essential for understanding data shape before querying.

    Args:
        schema: Schema name (e.g. 'public').
        table:  Table name.
    """
    all_results = {}
    for inst in _instances():
        name = inst.get("name", "default")
        try:
            all_results[name] = describe_table(inst, schema, table)
        except Exception as e:
            all_results[name] = {"error": str(e)}

    return {
        "description_per_instance": all_results,
        "timestamp": datetime.now().isoformat(),
    }


@app.tool()
def pg_execute_query(sql: str, limit: int = 100) -> Dict[str, Any]:
    """
    Execute a read-only SELECT (or WITH) query and return results as rows.
    Non-SELECT statements are rejected — use pg_execute_statement for writes.

    Args:
        sql:   A SELECT or WITH SQL query.
        limit: Maximum number of rows to return (default: 100).
    """
    all_results = {}
    for inst in _instances():
        name = inst.get("name", "default")
        try:
            rows, cols = execute_query(inst, sql, limit)
            all_results[name] = {
                "columns":   cols,
                "rows":      rows,
                "row_count": len(rows),
            }
        except Exception as e:
            all_results[name] = {"error": str(e)}

    return {
        "query":              sql,
        "results_per_instance": all_results,
        "timestamp":          datetime.now().isoformat(),
    }


@app.tool()
def pg_explain_query(sql: str) -> Dict[str, Any]:
    """
    Run EXPLAIN ANALYZE on a SQL query and return the execution plan.
    Use this to understand query performance and identify bottlenecks
    before suggesting index or schema changes.

    Args:
        sql: The SQL query to explain (SELECT recommended).
    """
    all_results = {}
    for inst in _instances():
        name = inst.get("name", "default")
        try:
            all_results[name] = explain_query(inst, sql)
        except Exception as e:
            all_results[name] = {"error": str(e)}

    return {
        "query":             sql,
        "plan_per_instance": all_results,
        "timestamp":         datetime.now().isoformat(),
    }


@app.tool()
def pg_get_table_stats(schema: str, table: str) -> Dict[str, Any]:
    """
    Return runtime statistics for a table from pg_stat_user_tables:
    live rows, dead rows, total size, index size, last vacuum / analyze timestamps.
    Useful for detecting bloat or stale statistics.

    Args:
        schema: Schema name.
        table:  Table name.
    """
    all_results = {}
    for inst in _instances():
        name = inst.get("name", "default")
        try:
            stats = get_table_stats(inst, schema, table)
            all_results[name] = (
                stats if stats
                else {"error": f"Table {schema}.{table} not found in pg_stat_user_tables"}
            )
        except Exception as e:
            all_results[name] = {"error": str(e)}

    return {
        "schema":             schema,
        "table":              table,
        "stats_per_instance": all_results,
        "timestamp":          datetime.now().isoformat(),
    }


@app.tool()
def pg_get_db_stats() -> Dict[str, Any]:
    """
    Return database-level statistics from pg_stat_database:
    active connections, commits, rollbacks, cache hit ratio, rows inserted/updated/deleted,
    and deadlock count. Provides a quick operational snapshot of database health.
    """
    all_results = {}
    for inst in _instances():
        name = inst.get("name", "default")
        try:
            all_results[name] = get_db_stats(inst)
        except Exception as e:
            all_results[name] = {"error": str(e)}

    return {
        "db_stats_per_instance": all_results,
        "timestamp": datetime.now().isoformat(),
    }


@app.tool()
def pg_get_slow_queries(
    min_duration_ms: float = 100.0,
    limit: int = 10,
) -> Dict[str, Any]:
    """
    Return the top slow queries from pg_stat_statements (requires the extension).
    Shows query preview, call count, total/mean/stddev execution time, and rows returned.
    Use this to identify performance hotspots.

    Args:
        min_duration_ms: Minimum mean execution time in milliseconds (default: 100).
        limit:           Maximum number of queries to return (default: 10).
    """
    all_results = {}
    for inst in _instances():
        name = inst.get("name", "default")
        try:
            all_results[name] = get_slow_queries(inst, min_duration_ms, limit)
        except Exception as e:
            all_results[name] = {"error": str(e)}

    return {
        "min_duration_ms":        min_duration_ms,
        "slow_queries_per_instance": all_results,
        "timestamp":              datetime.now().isoformat(),
    }


@app.tool()
def pg_check_db_health() -> Dict[str, Any]:
    """
    Return a health summary for each configured PostgreSQL instance:
    version, server start time, max/active/idle connections, longest running query,
    and replication lag (if this is a replica).
    Use this as the first tool to call when diagnosing database issues.
    """
    all_results = {}
    for inst in _instances():
        name = inst.get("name", "default")
        try:
            all_results[name] = check_db_health(inst)
        except Exception as e:
            all_results[name] = {"error": str(e)}

    return {
        "health_per_instance": all_results,
        "timestamp": datetime.now().isoformat(),
    }


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PostgreSQL MCP Server for SODA Contexture")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="MCP transport type (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8003,
        help="Port for SSE transport (default: 8003)",
    )
    args = parser.parse_args()

    if args.transport == "sse":
        app.run(transport="sse", port=args.port)
    else:
        app.run()
