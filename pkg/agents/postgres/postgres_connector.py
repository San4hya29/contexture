"""
PostgreSQL connector for SODA Contexture.

Provides low-level query functions used by the MCP tools.
Connection settings are loaded from config/postgres_config.yaml.
"""

import os
import yaml
import psycopg2
import psycopg2.extras
from typing import Any, Dict, List, Optional, Tuple


def _load_config() -> List[Dict]:
    """Load postgres_config.yaml from the repo config directory."""
    here = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(here, "..", "..", "..", "config", "postgres_config.yaml")
    config_path = os.path.normpath(config_path)

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"postgres_config.yaml not found at {config_path}")

    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    return cfg.get("postgres_instances", [])


def _get_conn(instance: Dict) -> psycopg2.extensions.connection:
    """
    Open a read-only psycopg2 connection for a given config instance.

    ``default_transaction_read_only=on`` is enforced at the session level so
    that even CTEs containing DML (e.g. ``WITH x AS (DELETE ...) SELECT ...``)
    are rejected by PostgreSQL — not just by the client-side prefix check in
    ``execute_query``.
    """
    return psycopg2.connect(
        host=instance.get("host", "localhost"),
        port=instance.get("port", 5432),
        user=instance.get("user", "postgres"),
        password=instance.get("password", ""),
        dbname=instance.get("dbname", "postgres"),
        sslmode=instance.get("sslmode", "disable"),
        cursor_factory=psycopg2.extras.RealDictCursor,
        options="-c default_transaction_read_only=on",
    )


# ── public helpers ────────────────────────────────────────────────────────────

def get_all_instances() -> List[Dict]:
    return _load_config()


def list_databases(instance: Dict) -> List[Dict]:
    conn = _get_conn(instance)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    d.datname                                              AS name,
                    pg_catalog.pg_get_userbyid(d.datdba)                  AS owner,
                    pg_catalog.pg_encoding_to_char(d.encoding)            AS encoding,
                    d.datcollate                                           AS collation,
                    pg_catalog.pg_size_pretty(pg_catalog.pg_database_size(d.datname)) AS size
                FROM   pg_catalog.pg_database d
                WHERE  d.datistemplate = false
                ORDER  BY d.datname
            """)
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def list_schemas(instance: Dict) -> List[str]:
    conn = _get_conn(instance)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT schema_name
                FROM   information_schema.schemata
                WHERE  schema_name NOT IN ('pg_catalog','information_schema','pg_toast')
                  AND  schema_name NOT LIKE 'pg_temp_%'
                  AND  schema_name NOT LIKE 'pg_toast_temp_%'
                ORDER  BY schema_name
            """)
            return [r["schema_name"] for r in cur.fetchall()]
    finally:
        conn.close()


def list_tables(instance: Dict, schema: str = "public") -> List[Dict]:
    conn = _get_conn(instance)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name, table_type
                FROM   information_schema.tables
                WHERE  table_schema = %s
                ORDER  BY table_name
            """, (schema,))
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def describe_table(instance: Dict, schema: str, table: str) -> Dict[str, Any]:
    conn = _get_conn(instance)
    try:
        with conn.cursor() as cur:
            # Columns
            cur.execute("""
                SELECT
                    column_name,
                    data_type,
                    character_maximum_length AS max_length,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
            """, (schema, table))
            columns = [dict(r) for r in cur.fetchall()]

            # Indexes
            cur.execute("""
                SELECT indexname, indexdef
                FROM   pg_indexes
                WHERE  schemaname = %s AND tablename = %s
                ORDER  BY indexname
            """, (schema, table))
            indexes = [dict(r) for r in cur.fetchall()]

            # Primary key
            cur.execute("""
                SELECT kcu.column_name
                FROM   information_schema.table_constraints tc
                JOIN   information_schema.key_column_usage kcu
                       ON tc.constraint_name = kcu.constraint_name
                       AND tc.table_schema   = kcu.table_schema
                WHERE  tc.constraint_type = 'PRIMARY KEY'
                  AND  tc.table_schema    = %s
                  AND  tc.table_name      = %s
                ORDER  BY kcu.ordinal_position
            """, (schema, table))
            primary_keys = [r["column_name"] for r in cur.fetchall()]

            return {
                "schema": schema,
                "table": table,
                "columns": columns,
                "primary_keys": primary_keys,
                "indexes": indexes,
            }
    finally:
        conn.close()


def execute_query(instance: Dict, sql: str, limit: int = 100) -> Tuple[List[Dict], List[str]]:
    """Run a read-only SELECT query, returning (rows, column_names)."""
    normalized = sql.strip().upper()
    if not (normalized.startswith("SELECT") or normalized.startswith("WITH")):
        raise ValueError("Only SELECT / WITH queries are allowed via execute_query.")

    conn = _get_conn(instance)
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchmany(limit)
            col_names = [desc[0] for desc in cur.description] if cur.description else []
            return [dict(r) for r in rows], col_names
    finally:
        conn.close()


def explain_query(instance: Dict, sql: str) -> List[str]:
    """
    Return EXPLAIN (ANALYZE, BUFFERS) output for a SELECT or WITH query.

    Only SELECT/WITH queries are accepted — EXPLAIN ANALYZE actually executes
    the statement, so we validate the SQL before running it.
    """
    normalized = sql.strip().upper()
    if not (normalized.startswith("SELECT") or normalized.startswith("WITH")):
        raise ValueError("Only SELECT / WITH queries are allowed in explain_query.")

    conn = _get_conn(instance)
    try:
        with conn.cursor() as cur:
            cur.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) {sql}")
            return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()


def get_table_stats(instance: Dict, schema: str, table: str) -> Optional[Dict]:
    """Return pg_stat_user_tables row for a specific table."""
    conn = _get_conn(instance)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    n_live_tup                                                         AS live_rows,
                    n_dead_tup                                                         AS dead_rows,
                    pg_size_pretty(pg_total_relation_size(
                        (quote_ident(schemaname)||'.'||quote_ident(relname))::regclass)) AS total_size,
                    pg_size_pretty(pg_indexes_size(
                        (quote_ident(schemaname)||'.'||quote_ident(relname))::regclass)) AS index_size,
                    COALESCE(last_vacuum::text,  '-')                                  AS last_vacuum,
                    COALESCE(last_analyze::text, '-')                                  AS last_analyze,
                    COALESCE(last_autovacuum::text,  '-')                              AS last_autovacuum,
                    COALESCE(last_autoanalyze::text, '-')                              AS last_autoanalyze
                FROM pg_stat_user_tables
                WHERE schemaname = %s AND relname = %s
            """, (schema, table))
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()


def get_db_stats(instance: Dict) -> Dict[str, Any]:
    """Return pg_stat_database for the connected database."""
    conn = _get_conn(instance)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    datname,
                    numbackends                                          AS active_connections,
                    xact_commit                                          AS commits,
                    xact_rollback                                        AS rollbacks,
                    blks_read                                            AS disk_blocks_read,
                    blks_hit                                             AS buffer_cache_hits,
                    CASE WHEN (blks_hit + blks_read) > 0
                         THEN round(100.0 * blks_hit / (blks_hit + blks_read), 2)
                         ELSE 0 END                                      AS cache_hit_ratio_pct,
                    tup_returned                                         AS rows_returned,
                    tup_fetched                                          AS rows_fetched,
                    tup_inserted                                         AS rows_inserted,
                    tup_updated                                          AS rows_updated,
                    tup_deleted                                          AS rows_deleted,
                    deadlocks
                FROM pg_stat_database
                WHERE datname = current_database()
            """)
            row = cur.fetchone()
            return dict(row) if row else {}
    finally:
        conn.close()


def get_slow_queries(instance: Dict, min_duration_ms: float = 100.0, limit: int = 10) -> List[Dict]:
    """
    Return top slow queries from pg_stat_statements.
    Requires the pg_stat_statements extension to be enabled.

    Handles the column rename introduced in PostgreSQL 13:
      - PostgreSQL ≤12: total_time / mean_time / stddev_time
      - PostgreSQL ≥13: total_exec_time / mean_exec_time / stddev_exec_time
    """
    conn = _get_conn(instance)
    try:
        with conn.cursor() as cur:
            # Check extension exists first
            cur.execute("SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'")
            if not cur.fetchone():
                return [{"error": "pg_stat_statements extension is not enabled on this server."}]

            # Detect PostgreSQL version to handle column name change in pg13
            cur.execute("SELECT current_setting('server_version_num')::int AS ver")
            pg_ver = cur.fetchone()["ver"]

            if pg_ver >= 130000:
                total_col, mean_col, stddev_col = "total_exec_time", "mean_exec_time", "stddev_exec_time"
            else:
                total_col, mean_col, stddev_col = "total_time", "mean_time", "stddev_time"

            cur.execute(f"""
                SELECT
                    left(query, 200)                               AS query_preview,
                    calls,
                    round({total_col}::numeric,  2)                AS total_exec_ms,
                    round({mean_col}::numeric,   2)                AS mean_exec_ms,
                    round({stddev_col}::numeric, 2)                AS stddev_exec_ms,
                    rows
                FROM  pg_stat_statements
                WHERE {mean_col} >= %s
                ORDER BY {mean_col} DESC
                LIMIT %s
            """, (min_duration_ms, limit))
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def check_db_health(instance: Dict) -> Dict[str, Any]:
    """Quick health summary: version, uptime, connections, replication lag."""
    conn = _get_conn(instance)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            version = cur.fetchone()["version"]

            cur.execute("SELECT pg_postmaster_start_time()")
            start_time = cur.fetchone()["pg_postmaster_start_time"]

            cur.execute("""
                SELECT count(*) AS total,
                       sum(CASE WHEN state = 'active' THEN 1 ELSE 0 END)  AS active,
                       sum(CASE WHEN state = 'idle'   THEN 1 ELSE 0 END)  AS idle,
                       max(EXTRACT(EPOCH FROM (now() - query_start)))      AS longest_query_secs
                FROM   pg_stat_activity
                WHERE  pid <> pg_backend_pid()
            """)
            conn_row = dict(cur.fetchone())

            cur.execute("SHOW max_connections")
            max_conn = int(cur.fetchone()["max_connections"])

            # Replication lag (returns None if not a replica)
            cur.execute("""
                SELECT CASE WHEN pg_is_in_recovery()
                            THEN EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp()))
                            ELSE NULL
                       END AS replication_lag_secs
            """)
            repl = cur.fetchone()

            return {
                "version": version,
                "start_time": str(start_time),
                "max_connections": max_conn,
                "connections": conn_row,
                "replication_lag_secs": repl["replication_lag_secs"],
                "is_replica": repl["replication_lag_secs"] is not None,
            }
    finally:
        conn.close()
