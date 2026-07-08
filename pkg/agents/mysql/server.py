# server.py — MySQL MCP Server for SODA Contexture
#
# Implements the same FastMCP @app.tool() pattern as pkg/agents/clickhouse/server.py.
# Connects to MySQL instances defined in config/mysql_config.yaml.
#
# Run (always from the pkg/agents/mysql/ directory):
#   python server.py                         # stdio transport (default)
#   python server.py --transport sse         # SSE/HTTP on port 8005
#   python server.py --transport sse --port 9000  # custom port

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from mysql_connector import (
    get_all_instances,
    list_databases,
    list_tables,
    describe_table,
    execute_query,
    get_table_stats,
    get_db_stats,
    get_slow_queries,
    check_db_health,
)

app = FastMCP("MySQL MCP Server")

# ── lazy-load instances ───────────────────────────────────────────────────────

def _instances() -> List[Dict]:
    try:
        return get_all_instances()
    except FileNotFoundError as e:
        print(f"[mysql-mcp] WARNING: {e}")
        return []


# ── tools ─────────────────────────────────────────────────────────────────────

@app.tool()
def my_list_databases() -> Dict[str, Any]:
    """
    List all databases on the MySQL server across configured instances.
    Returns name for each database.
    Useful for understanding what databases exist before querying.
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
def my_list_tables(database: str = "") -> Dict[str, Any]:
    """
    List all tables in the given MySQL database.
    Returns table name, engine, total rows, and data size.

    Args:
        database: Database name to query (uses config default if empty).
    """
    all_results = {}
    for inst in _instances():
        name = inst.get("name", "default")
        try:
            all_results[name] = list_tables(inst, database)
        except Exception as e:
            all_results[name] = {"error": str(e)}

    return {
        "database": database,
        "tables_per_instance": all_results,
        "timestamp": datetime.now().isoformat(),
    }


@app.tool()
def my_describe_table(database: str, table: str) -> Dict[str, Any]:
    """
    Return the full structure of a MySQL table: columns (name, type, key, nullable,
    default, extra), total row count, data size, and engine.
    Essential for understanding data shape before querying.

    Args:
        database: Database name (e.g. 'test_db').
        table:    Table name.
    """
    all_results = {}
    for inst in _instances():
        name = inst.get("name", "default")
        try:
            all_results[name] = describe_table(inst, database, table)
        except Exception as e:
            all_results[name] = {"error": str(e)}

    return {
        "description_per_instance": all_results,
        "timestamp": datetime.now().isoformat(),
    }


@app.tool()
def my_execute_query(sql: str, limit: int = 100) -> Dict[str, Any]:
    """
    Execute a read-only SELECT (or WITH) query against MySQL and return results.
    Non-SELECT statements are rejected.

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
        "query":                  sql,
        "results_per_instance":   all_results,
        "timestamp":              datetime.now().isoformat(),
    }


@app.tool()
def my_get_table_stats(database: str, table: str) -> Dict[str, Any]:
    """
    Return storage statistics for a MySQL table from information_schema:
    total rows, data size, index size, engine, collation, auto_increment,
    create/update times.

    Args:
        database: Database name.
        table:    Table name.
    """
    all_results = {}
    for inst in _instances():
        name = inst.get("name", "default")
        try:
            stats = get_table_stats(inst, database, table)
            all_results[name] = (
                stats if stats
                else {"error": f"Table {database}.{table} not found in information_schema"}
            )
        except Exception as e:
            all_results[name] = {"error": str(e)}

    return {
        "database":           database,
        "table":              table,
        "stats_per_instance": all_results,
        "timestamp":          datetime.now().isoformat(),
    }


@app.tool()
def my_get_db_stats() -> Dict[str, Any]:
    """
    Return database-level statistics: list of databases,
    and key global status variables (connections, threads, uptime, questions).
    Provides a quick operational snapshot of the MySQL server.
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
def my_get_slow_queries(
    min_duration_sec: float = 1.0,
    limit: int = 10,
) -> Dict[str, Any]:
    """
    Return the top slow queries from performance_schema.
    Shows query digest, call count, avg/max duration, rows examined and sent.
    Use this to identify performance hotspots.

    Args:
        min_duration_sec: Minimum average execution time in seconds (default: 1.0).
        limit:            Maximum number of queries to return (default: 10).
    """
    all_results = {}
    for inst in _instances():
        name = inst.get("name", "default")
        try:
            all_results[name] = get_slow_queries(inst, min_duration_sec, limit)
        except Exception as e:
            all_results[name] = {"error": str(e)}

    return {
        "min_duration_sec":          min_duration_sec,
        "slow_queries_per_instance": all_results,
        "timestamp":                 datetime.now().isoformat(),
    }


@app.tool()
def my_check_db_health() -> Dict[str, Any]:
    """
    Return a health summary for each configured MySQL instance:
    version, uptime in seconds, connected threads, and running threads.
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

    parser = argparse.ArgumentParser(description="MySQL MCP Server for SODA Contexture")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="MCP transport type (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8005,
        help="Port for SSE transport (default: 8005)",
    )
    args = parser.parse_args()

    if args.transport == "sse":
        app.run(transport="sse", port=args.port)
    else:
        app.run()
