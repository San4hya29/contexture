# Redis Agent — SODA Contexture

A Redis AI Copilot for SODA Contexture.

The Redis agent exposes Redis databases as MCP tools, allowing the Contexture engine (backed by a local Ollama model or OpenAI-compatible LLM) to query, analyze, inspect schemas from Redis data.

Built using the official MCP Python SDK and follows the same architecture pattern as the PostgreSQL and Prometheus agents.

## Folder Structure

```
pkg/agents/redis/
├── app/
│   ├── cli.py             # User CLI entry point
│   ├── copilot.py         # Copilot orchestration logic
│   ├── mcp_client.py      # MCP client wrapper
│   └── mcp_server.py      # Redis MCP server
│
├── llm/
│   ├── base.py
│   ├── client.py
│   └── providers/
│       ├── ollama.py
│       └── openai.py
│
├── datasets/
│   └── ecommerce.yaml     # Sample Redis dataset
│
├── seeder/
│   └── seed_data.py       # Dataset seeding utility
│
├── Dockerfile
├── docker-compose.yml
├── docker-compose.external.yml
├── requirements.txt
├── test_connection.py
└── README.md

config/
└── redis_config.yaml      # Redis & LLM configuration
```

## Architecture

```
User CLI
   │
   ▼
app/cli.py
   │
   ▼
Copilot Orchestrator
(app/copilot.py)
   │
   ▼
LLM Provider
(Ollama / OpenAI)
   │
   │ Tool Calls
   ▼
Redis MCP Client
(app/mcp_client.py)
   │
   ▼
Redis MCP Server
(app/mcp_server.py)
   │
   ▼
Redis Database
```


The Copilot receives a natural language question, the LLM determines which MCP tools are required, the MCP client invokes those tools, and the Redis MCP server retrieves the requested information from Redis.

## Configuration

Edit: `config/redis_config.yaml`

Example:

```yaml
redis:
  host: "localhost"
  port: 6379
  username: ""
  password: ""
  db: 0

llm:
  provider: "ollama"
  model: "qwen3:14b"
  api_key: ""
  base_url: "http://localhost:11434/api/chat"
```

### External Redis

To connect to a Redis instance running outside Docker:

```yaml
redis:
  host: "host.docker.internal"
  port: 6379
```

or

```yaml
redis:
  host: "192.168.1.100"
  port: 6379
```

using the Redis server IP address.

## Getting Started

All commands below are run from: `pkg/agents/redis/`

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Redis

Edit:
```bash
vi ../../config/redis_config.yaml
```

Provide Redis connection information and LLM settings.

### 3. Test Connectivity

Before running the Copilot, verify connectivity:

```bash
python test_connection.py
```

Expected output:

```text
Loading redis_config.yaml...

Connecting to Redis...
Connection: OK

Database: 0
Keys Found: 25

Redis Version: 7.x.x

All checks passed.
```

### 4. Seed Sample Data
```bash
python seeder/seed_data.py --dataset ecommerce.yaml
```

### 5. Query the Copilot
```bash
python -m app.cli "What is the highest amount purchased?"
```

Example output:

```text
The highest amount purchased is 1500.0.
```

Another example:

```bash
python -m app.cli "Which products appear in both cart and wishlist?"
```

Example output:

```text
The product appearing in both cart and wishlist is cache:product:101.
```

## Docker Deployment

### Local Redis Environment (Standalone Development Setup)

If you do not have a pre-existing Redis instance and want to run a local Redis server:

```bash
# Spins up local Redis (port 6379) and RedisInsight (port 8001)
docker compose up -d
```

### External Redis Environment (Run Copilot Agent inside Docker)

If you already have an active Redis database (running either on your local host machine, a VM, or a remote server) and want to run only the Redis AI Copilot agent inside a Docker container:

1. Configure your Redis host and LLM details in the shared configuration file `config/redis_config.yaml`.
2. Build and launch the Copilot agent container:

```bash
docker compose -f docker-compose.external.yml up --build
```

*Note: The container will mount the shared `config/redis_config.yaml` configuration automatically to resolve connection details.*

## Testing

### End-to-End Verification
```bash
python test_connection.py
```
## Example Queries
```bash
python -m app.cli "What is email of user 2?"
```
