# MySQL MCP Agent

A MySQL data-connector agent for [SODA Contexture](https://github.com/sodafoundation/contexture).  
Exposes MySQL databases, tables, and query execution as MCP tools via [FastMCP](https://github.com/jlowin/fastmcp).

---

## How to Run

The easiest way to run the MySQL agent (including a local database, schema initialization, and the MCP agent itself) is using the provided Docker stack and `run_mysql.bat` launcher from the repository root.

### 1. Start the Stack

From the root of the repository, run:

```bash
.\run_mysql.bat up
```

This will:
- Start a MySQL 8.0 database on port `3306`.
- Automatically seed the database with the `ecommerce` schema.
- Build and start the `contexture-mysql-mcp` FastMCP agent on `http://localhost:8005/sse`.

### 2. Interactive NL Chatbot

An interactive terminal-based Natural Language chatbot is provided in `scripts/mysql/chatbot.py`. It uses Ollama to translate natural language into SQL against the MySQL `ecommerce` schema, and routes it through the MCP Server.

To use it, ensure the stack is running (`.\run_mysql.bat up`), then run:

```bash
py scripts\mysql\chatbot.py
```

**Try asking it:**
- *"List all customers"*
- *"What products did Rahul buy?"*
- *"Total revenue per category"*
- *"Top 3 customers by total spending"*
- *"Which city has the most orders?"*
- *"Average order value per customer"*

### 3. Stop the Stack

```bash
.\run_mysql.bat down
```
