"""
MySQL connector for SODA Contexture.

Provides low-level query functions used by the MCP tools.
Connection settings are loaded from config/mysql_config.yaml.
"""

import os
import yaml
import mysql.connector
from typing import Any, Dict, List, Optional, Tuple


def _load_config() -> List[Dict]:
    """Load mysql_config.yaml from the repo config directory."""
    here = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(here, "..", "..", "..", "config", "mysql_config.yaml")
    config_path = os.path.normpath(config_path)

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"mysql_config.yaml not found at {config_path}")

    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    return cfg.get("mysql_instances", [])


def _get_connection(instance: Dict) -> mysql.connector.MySQLConnection:
    """Open a MySQL connection for a given config instance."""
    host = os.environ.get("MYSQL_HOST") or instance.get("host", "localhost")
    port = int(os.environ.get("MYSQL_PORT") or instance.get("port", 3306))
    user = os.environ.get("MYSQL_USER") or instance.get("username", "root")
    password = os.environ.get("MYSQL_PASSWORD") or instance.get("password", "")
    database = os.environ.get("MYSQL_DATABASE") or instance.get("database", "")

    return mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
    )


# ── public helpers ────────────────────────────────────────────────────────────

def get_all_instances() -> List[Dict]:
    return _load_config()


def list_databases(instance: Dict) -> List[Dict]:
    conn = _get_connection(instance)
    try:
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES")
        rows = cursor.fetchall()
        return [{"name": r[0]} for r in rows]
    finally:
        conn.close()


def list_tables(instance: Dict, database: str = "") -> List[Dict]:
    conn = _get_connection(instance)
    try:
        cursor = conn.cursor()
        db = database or instance.get("database", "")
        cursor.execute(
            "SELECT TABLE_NAME, ENGINE, TABLE_ROWS, "
            "CONCAT(ROUND(DATA_LENGTH / 1024, 2), ' KiB') AS size "
            "FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = %s ORDER BY TABLE_NAME",
            (db,),
        )
        rows = cursor.fetchall()
        return [
            {"name": r[0], "engine": r[1], "total_rows": r[2], "size": r[3]}
            for r in rows
        ]
    finally:
        conn.close()


def describe_table(instance: Dict, database: str, table: str) -> Dict[str, Any]:
    conn = _get_connection(instance)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_KEY, IS_NULLABLE, "
            "COLUMN_DEFAULT, EXTRA "
            "FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s "
            "ORDER BY ORDINAL_POSITION",
            (database, table),
        )
        col_rows = cursor.fetchall()
        columns = [
            {
                "name": r[0],
                "type": r[1],
                "key": r[2],
                "nullable": r[3],
                "default": r[4],
                "extra": r[5],
            }
            for r in col_rows
        ]

        cursor.execute(
            "SELECT TABLE_ROWS, "
            "CONCAT(ROUND(DATA_LENGTH / 1024, 2), ' KiB') AS data_size, "
            "ENGINE "
            "FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s",
            (database, table),
        )
        stats = cursor.fetchall()
        row_count = stats[0][0] if stats else None
        data_size = stats[0][1] if stats else None
        engine = stats[0][2] if stats else None

        return {
            "database": database,
            "table": table,
            "columns": columns,
            "total_rows": row_count,
            "data_size": data_size,
            "engine": engine,
        }
    finally:
        conn.close()


def execute_query(instance: Dict, sql: str, limit: int = 100) -> Tuple[List[Dict], List[str]]:
    """Run a read-only SELECT query, returning (rows, column_names)."""
    normalized = sql.strip().upper()
    if not (normalized.startswith("SELECT") or normalized.startswith("WITH")):
        raise ValueError("Only SELECT / WITH queries are allowed via execute_query.")

    conn = _get_connection(instance)
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        col_names = [desc[0] for desc in cursor.description]
        rows_raw = cursor.fetchmany(limit)
        result = [dict(zip(col_names, row)) for row in rows_raw]
        return result, col_names
    finally:
        conn.close()


def get_table_stats(instance: Dict, database: str, table: str) -> Optional[Dict]:
    """Return information_schema stats for a specific table."""
    conn = _get_connection(instance)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                TABLE_ROWS,
                DATA_LENGTH,
                CONCAT(ROUND(DATA_LENGTH / 1024, 2), ' KiB')   AS data_size,
                CONCAT(ROUND(INDEX_LENGTH / 1024, 2), ' KiB')  AS index_size,
                ENGINE,
                TABLE_COLLATION,
                AUTO_INCREMENT,
                CREATE_TIME,
                UPDATE_TIME
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            """,
            (database, table),
        )
        rows = cursor.fetchall()
        if not rows:
            return None
        r = rows[0]
        return {
            "total_rows": r[0],
            "data_bytes": r[1],
            "data_size": r[2],
            "index_size": r[3],
            "engine": r[4],
            "collation": r[5],
            "auto_increment": r[6],
            "create_time": str(r[7]) if r[7] else None,
            "update_time": str(r[8]) if r[8] else None,
        }
    finally:
        conn.close()


def get_db_stats(instance: Dict) -> Dict[str, Any]:
    """Return database-level stats from information_schema + global status."""
    conn = _get_connection(instance)
    try:
        cursor = conn.cursor()
        # databases
        cursor.execute("SHOW DATABASES")
        db_rows = cursor.fetchall()

        # key global status variables
        cursor.execute(
            "SHOW GLOBAL STATUS WHERE Variable_name IN "
            "('Threads_connected', 'Threads_running', 'Questions', "
            "'Uptime', 'Connections', 'Aborted_connects')"
        )
        status_rows = cursor.fetchall()

        return {
            "databases": [{"name": r[0]} for r in db_rows],
            "status": {r[0]: r[1] for r in status_rows},
        }
    finally:
        conn.close()


def get_slow_queries(
    instance: Dict, min_duration_sec: float = 1.0, limit: int = 10
) -> List[Dict]:
    """Return slow queries from performance_schema (if available)."""
    conn = _get_connection(instance)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                LEFT(DIGEST_TEXT, 200)                         AS query_preview,
                COUNT_STAR                                     AS calls,
                ROUND(AVG_TIMER_WAIT / 1000000000, 2)         AS avg_duration_ms,
                ROUND(MAX_TIMER_WAIT / 1000000000, 2)         AS max_duration_ms,
                SUM_ROWS_EXAMINED                              AS total_rows_examined,
                SUM_ROWS_SENT                                  AS total_rows_sent
            FROM performance_schema.events_statements_summary_by_digest
            WHERE AVG_TIMER_WAIT / 1000000000 >= %s
            ORDER BY avg_duration_ms DESC
            LIMIT %s
            """,
            (min_duration_sec * 1000, limit),
        )
        rows = cursor.fetchall()
        return [
            {
                "query_preview": r[0],
                "calls": r[1],
                "avg_duration_ms": float(r[2]) if r[2] else 0,
                "max_duration_ms": float(r[3]) if r[3] else 0,
                "total_rows_examined": r[4],
                "total_rows_sent": r[5],
            }
            for r in rows
        ]
    except Exception:
        # performance_schema may be disabled
        return [{"note": "performance_schema not available or disabled"}]
    finally:
        conn.close()


def check_db_health(instance: Dict) -> Dict[str, Any]:
    """Quick health summary: version, uptime, connections, running threads."""
    conn = _get_connection(instance)
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]

        cursor.execute("SHOW GLOBAL STATUS WHERE Variable_name = 'Uptime'")
        uptime_row = cursor.fetchone()
        uptime_secs = int(uptime_row[1]) if uptime_row else None

        cursor.execute("SHOW GLOBAL STATUS WHERE Variable_name = 'Threads_connected'")
        conn_row = cursor.fetchone()
        connections = int(conn_row[1]) if conn_row else None

        cursor.execute("SHOW GLOBAL STATUS WHERE Variable_name = 'Threads_running'")
        running_row = cursor.fetchone()
        running_threads = int(running_row[1]) if running_row else 0

        return {
            "version": version,
            "uptime_seconds": uptime_secs,
            "connections": connections,
            "running_threads": running_threads,
        }
    finally:
        conn.close()
