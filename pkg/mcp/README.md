# MCP Clients — SODA Contexture

This directory contains the **MCP client layer** for SODA Contexture.  
Clients connect to any FastMCP server exposed by the data-connector agents and drive
natural-language queries through an Ollama LLM.

> **Note:** The Prometheus MCP server has moved to `pkg/agents/prometheus/`.  
> See `pkg/agents/prometheus/README.md` for setup and run instructions.

---

## Files

| File | Purpose |
|---|---|
| `client_dynamic.py` | LLM-based NL→workflow client (Ollama + FastMCP). Primary interactive client. |
| `client_dynamic_ui.py` | Web UI wrapper around `client_dynamic.py`. |
| `client.py` | Static MCP client for direct tool invocation without LLM routing. |

---

## How It Works

```
User (natural language query)
      │
      ▼
client_dynamic.py
      │  1. Fetches OCS context from GET http://localhost:8000/get_ocs_prompt
      │  2. Asks Ollama to convert the NL query to a tool-call workflow (JSON)
      │  3. Executes each tool call against the MCP server
      │  4. Streams a summary back via Ollama
      ▼
FastMCP server (any adaptor — Prometheus, PostgreSQL, ClickHouse, …)
```

---

## Configuration

Edit the relevant files under `config/` at the repo root:

```yaml
# config/mcp_server_config.yaml
mcp_server_url: "http://localhost:8001/mcp"   # Prometheus (pkg/agents/prometheus)

# config/ollama_config.yaml
ollama_url: "http://localhost:11434"
ollama_model: "qwen2.5-coder:14b"
```

---

## Running

### Start the services first

```bash
# 1. OCS engine
go run ./pkg/ocs/

# 2. Prometheus MCP server (from its own directory)
cd pkg/agents/prometheus
python server.py --transport sse --port 8001
```

### Run the interactive client

```bash
cd pkg/mcp
python client_dynamic.py
```

Example queries:
- `What is the current CPU usage for the frontend workload?`
- `Show me the top 5 pods by memory usage`
- `Are there any nodes under disk pressure?`
- `Explain the OCS policy`
