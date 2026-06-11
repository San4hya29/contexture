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
├── postgres_connector.py  # psycopg2-based query helpers
├── mcp_tools.py           # Tool wrapper functions (callable without the server)
├── tool_registry.py       # TOOLS dict — mirrors mongodb/tool_registry.py
├── agent.py               # Keyword-based NL query router — mirrors mongodb/agent.py
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
server.py  (FastMCP — port 8003)
      │  @app.tool() handlers
      ▼
postgres_connector.py  (psycopg2)
      │  SQL queries
      ▼
PostgreSQL
```

The flow is identical to how the Prometheus MCP server works (port 8001).  
The OCS engine fetches context from `/get_ocs_prompt`, the LLM converts the NL query into a list of tool calls, and the FastMCP client executes them against this server.

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
| `pg_explain_query` | EXPLAIN ANALYZE output for a query |
| `pg_get_table_stats` | Live rows, dead rows, sizes, vacuum/analyze timestamps |
| `pg_get_db_stats` | Cache hit ratio, commits, rollbacks, deadlocks from pg_stat_database |
| `pg_get_slow_queries` | Top slow queries via pg_stat_statements (extension required) |

All tools iterate over every instance in `postgres_config.yaml` and return results keyed by instance name — same pattern as the Prometheus tools returning `*_per_prometheus`.

---

## Configuration

Edit `config/postgres_config.yaml` (created at the project config root):

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

---

## Getting Started

### 1. Install dependencies

```bash
cd pkg/agents/postgres
pip install -r requirements.txt
```

### 2. Configure the connection

```bash
# Edit the config at project root
vi ../../config/postgres_config.yaml
```

### 3. Run the MCP server

**HTTP/SSE transport** (recommended — matches how the Prometheus server runs):

```bash
uvicorn server:app --port 8003
```

**stdio transport** (for direct MCP client use):

```bash
python server.py
```

### 4. Wire it into the Contexture client

In `config/mcp_server_config.yaml`, add the postgres server URL alongside the Prometheus one:

```yaml
mcp_server_url: "http://localhost:8001/mcp"        # Prometheus (existing)
postgres_mcp_url: "http://localhost:8003/mcp"      # PostgreSQL (new)
```

Then update `pkg/mcp/client_dynamic.py` to connect to the postgres server when postgres tools are needed, or run both servers and route tool calls by name prefix (`pg_*`).

---

## Using as a Standalone Tool (Alternative)

If you prefer to run the upstream open-source server directly instead of this wrapper:

```bash
# Install crystaldba/postgres-mcp
pip install postgres-mcp

# Run it (stdio transport, compatible with any MCP client)
postgres-mcp --db-url "postgresql://postgres:password@localhost:5432/mydb"

# Or with uvx (no install needed)
uvx postgres-mcp --db-url "postgresql://postgres:password@localhost:5432/mydb"
```

This provides a subset of the same tools. The `server.py` in this folder adds:
- Multi-instance support (query multiple PostgreSQL servers at once)
- Config-file based connection management (consistent with the rest of Contexture)
- OCS-aligned tool naming and output shape

---

## Adding a New Tool

1. Add a query function to `postgres_connector.py`.
2. Add a wrapper in `mcp_tools.py`.
3. Register it in `tool_registry.py`.
4. Add an `@app.tool()` in `server.py` that iterates `_instances()` and calls the connector.
5. Optionally add a keyword branch in `agent.py` for direct NL routing.
