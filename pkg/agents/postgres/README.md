# PostgreSQL Agent — SODA Contexture

A **FastMCP-based PostgreSQL data connector** for SODA Contexture.  
It exposes PostgreSQL databases as MCP tools so the Contexture engine (backed by a **local Ollama model**) can query, analyse, and build enriched OCS context from PostgreSQL data.

Built with the same pattern as `pkg/mcp/server.py` (the Prometheus MCP server).  
Tools follow the design of established open-source PostgreSQL MCP servers:
- [`crystaldba/postgres-mcp`](https://github.com/crystaldba/postgres-mcp)
- [`modelcontextprotocol/servers` — postgres](https://github.com/modelcontextprotocol/servers/tree/main/src/postgres)

---

## Folder Structure

```
pkg/agents/postgres/
├── server.py              # FastMCP entry point — all @app.tool() definitions
├── postgres_connector.py  # psycopg2-based query helpers (read-only connections)
├── mcp_tools.py           # Tool wrapper functions (callable without the server)
├── tool_registry.py       # TOOLS dict — mirrors mongodb/tool_registry.py
├── agent.py               # Keyword-based NL query router — mirrors mongodb/agent.py
├── test_connection.py     # Quick connectivity test — run this first
├── requirements.txt       # Python dependencies
└── README.md

config/
└── postgres_config.yaml   # Connection config (same level as prometheus_config.yaml)
```

---

## Architecture

```
Ollama (local LLM)
      │  NL query → workflow JSON
      ▼
client_dynamic.py / client_dynamic_ui.py
      │  call_tool(name, params)
      ▼
server.py  (FastMCP — default port 8003)
      │  @app.tool() handlers
      ▼
postgres_connector.py  (psycopg2, read-only connections)
      │  SQL queries
      ▼
PostgreSQL
```

The flow is identical to how the Prometheus MCP server works (port 8001).  
The OCS engine fetches context from `/get_ocs_prompt`, the LLM converts the NL query into a list of tool calls, and the FastMCP client executes them against this server.

All connections are opened with `default_transaction_read_only=on` — the server never writes to or modifies any data.

---

## Available MCP Tools

| Tool | Description |
|---|---|
| `pg_check_db_health` | Version, connections, longest query, replication lag — call this first |
| `pg_list_databases` | All databases with owner, encoding, size |
| `pg_list_schemas` | User schemas in the connected database |
| `pg_list_tables` | Tables and views in a given schema |
| `pg_describe_table` | Columns, types, primary keys, indexes |
| `pg_execute_query` | Run a SELECT / WITH query, returns rows |
| `pg_explain_query` | EXPLAIN (ANALYZE, BUFFERS) output for a SELECT query |
| `pg_get_table_stats` | Live rows, dead rows, sizes, vacuum/analyze timestamps |
| `pg_get_db_stats` | Cache hit ratio, commits, rollbacks, deadlocks from pg_stat_database |
| `pg_get_slow_queries` | Top slow queries via pg_stat_statements (extension required — see note below) |

All tools iterate over every instance in `postgres_config.yaml` and return results keyed by instance name — same pattern as the Prometheus tools returning `*_per_prometheus`.

> **Note on `pg_get_slow_queries`:** Requires the `pg_stat_statements` extension.  
> Enable it by adding `pg_stat_statements` to `shared_preload_libraries` in `postgresql.conf` and running `CREATE EXTENSION pg_stat_statements;`. The tool returns an informative error if the extension is absent.  
> Supports PostgreSQL 12 and 13+ (handles the `total_time` → `total_exec_time` column rename automatically).

---

## Configuration

Edit `config/postgres_config.yaml` at the project root:

```yaml
postgres_instances:
  - name: local
    host: "localhost"
    port: 5432
    user: "postgres"
    password: "yourpassword"
    dbname: "postgres"
    sslmode: "disable"

  # Add more instances as needed:
  # - name: analytics
  #   host: "analytics-db.internal"
  #   port: 5432
  #   user: "reader"
  #   password: "..."
  #   dbname: "analytics"
  #   sslmode: "require"
```

All fields follow the same pattern as `config/prometheus_config.yaml`.

---

## Getting Started

All commands below are run from the `pkg/agents/postgres/` directory.

### 1. Install dependencies

```bash
cd pkg/agents/postgres
pip install -r requirements.txt
```

### 2. Configure the connection

```bash
# Edit the config at the project root (two levels up)
vi ../../config/postgres_config.yaml
```

### 3. Test the connection

Before starting the server, verify the config and connection are working:

```bash
python test_connection.py
```

Expected output:

```
Loading postgres_config.yaml...
Found 1 instance(s): ['local']
--------------------------------------------------
Instance : local
Host     : localhost:5432
Database : postgres
User     : postgres
Connection: OK
Databases (3):
  - mydb     [UTF8]  8192 kB
  - postgres [UTF8]  8209 kB
  - template1 [UTF8] 7953 kB
Schemas   : public
--------------------------------------------------
All instances OK.
```

### 4. Run the MCP server

**stdio transport** (default — matches how FastMCP runs in the rest of Contexture):

```bash
python server.py
```

**SSE/HTTP transport** (for use with `client_dynamic.py` over HTTP):

```bash
python server.py --transport sse --port 8003
```

### 5. Wire it into the Contexture client

In `config/mcp_server_config.yaml`, add the postgres server URL alongside the Prometheus one:

```yaml
mcp_server_url: "http://localhost:8001/mcp"        # Prometheus (existing)
postgres_mcp_url: "http://localhost:8003/mcp"      # PostgreSQL (new)
```

Then update `pkg/mcp/client_dynamic.py` to connect to the postgres server when postgres tools are needed, or run both servers and route tool calls by name prefix (`pg_*`).

---

## Using the Upstream Open-Source Server (Alternative)

If you prefer to run `crystaldba/postgres-mcp` directly instead of this wrapper:

```bash
# Install
pip install postgres-mcp

# Run (stdio transport, compatible with any MCP client)
postgres-mcp --db-url "postgresql://postgres:password@localhost:5432/mydb"

# Or with uvx (no install needed)
uvx postgres-mcp --db-url "postgresql://postgres:password@localhost:5432/mydb"
```

The `server.py` in this folder adds on top of that:
- **Multi-instance support** — query multiple PostgreSQL servers in one call
- **Config-file based connections** — consistent with the rest of Contexture
- **OCS-aligned tool naming and output shape**

---

## Adding a New Tool

1. Add a query function to `postgres_connector.py`.
2. Add a wrapper in `mcp_tools.py`.
3. Register it in `tool_registry.py`.
4. Add an `@app.tool()` in `server.py` that iterates `_instances()` and calls the connector.
5. Optionally add a keyword branch in `agent.py` for direct NL routing.
