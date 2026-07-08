# MySQL MCP Agent

A MySQL data-connector agent for [SODA Contexture](https://github.com/sodafoundation/contexture).  
Exposes MySQL databases, tables, and query execution as MCP tools via [FastMCP](https://github.com/jlowin/fastmcp),
following the same pattern as the ClickHouse and PostgreSQL agents.

---

## File Structure

```
pkg/agents/mysql/
├── agent.py                  # Natural-language query router
├── mysql_connector.py        # Low-level MySQL connection & queries
├── mcp_tools.py              # Tool wrapper functions (callable without server)
├── server.py                 # FastMCP server exposing all tools
├── test_connection.py        # Quick connectivity test
├── tool_registry.py          # Central TOOLS registry
├── requirements.txt          # Python dependencies
└── README.md                 # This file

config/
└── mysql_config.yaml         # MySQL instance connection settings
```

---

## Setup

### 1. Install dependencies

```bash
cd pkg/agents/mysql
pip install -r requirements.txt
```

### 2. Configure MySQL connection

Edit `config/mysql_config.yaml` at the repo root:

```yaml
mysql_instances:
  - name: local
    host: "localhost"
    port: 3306
    database: "test_db"
    username: "root"
    password: ""
```

### 3. Test the connection

```bash
cd pkg/agents/mysql
python test_connection.py
```

---

## Running the MCP Server

```bash
cd pkg/agents/mysql

# stdio transport (default — for use with MCP clients)
python server.py

# SSE/HTTP transport on port 8005
python server.py --transport sse

# SSE on a custom port
python server.py --transport sse --port 9000
```

---

## Available MCP Tools

| Tool | Description |
|---|---|
| `my_list_databases` | List all databases on the MySQL server |
| `my_list_tables` | List tables in a database with row count and size |
| `my_describe_table` | Show columns, types, keys, and storage info for a table |
| `my_execute_query` | Run a read-only SELECT query |
| `my_get_table_stats` | Storage stats: size, engine, indexes, collation |
| `my_get_db_stats` | Server-level status variables (connections, threads) |
| `my_get_slow_queries` | Top slow queries from `performance_schema` |
| `my_check_db_health` | Version, uptime, connections, running threads |

---

## Docker (local MySQL)

Start a local MySQL instance:

```bash
docker run -d --name contexture-mysql \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=test_db \
  -p 3306:3306 \
  mysql:8.0
```

---

## See Also

- [ClickHouse Agent](../clickhouse/README.md)
- [PostgreSQL Agent](../postgres/README.md)
- [MongoDB Agent](../mongodb/README.md)
- [MySQL Documentation](https://dev.mysql.com/doc/)
