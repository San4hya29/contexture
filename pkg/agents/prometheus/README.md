# Prometheus Agent — SODA Contexture

A **FastMCP-based Prometheus data connector** for SODA Contexture.  
It exposes Prometheus metrics as MCP tools so the Contexture engine (backed by a **local Ollama model**) can query, analyse, and build enriched OCS context from Kubernetes observability data.

---

## Folder Structure

```
pkg/agents/prometheus/
├── server.py                  # FastMCP entry point — all @app.tool() definitions
├── prometheus_connector.py    # PrometheusConnect factory and config loading
├── mcp_tools.py               # Tool wrapper functions (callable without the server)
├── tool_registry.py           # TOOLS dict — mirrors postgres/tool_registry.py
├── agent.py                   # Keyword-based NL query router
├── data_pusher.py             # High-cardinality test data generator (Remote Write)
├── config.json                # Sample config for data_pusher.py
├── test_connection.py         # Quick connectivity test — run this first
├── requirements.txt           # Python dependencies
└── README.md

config/
└── prometheus_config.yaml     # Multi-instance connection config (repo root)
```

---

## Architecture

```
Ollama (local LLM)
      │  NL query → workflow JSON
      ▼
pkg/mcp/client_dynamic.py        (full LLM-based routing, any adaptor)
      │  — or —
agent.py                         (keyword-based routing, Prometheus only)
      │  call_tool(name, params)
      ▼
server.py  (FastMCP — default port 8001)
      │  @app.tool() handlers
      ▼
prometheus_connector.py  (PrometheusConnect, multi-instance)
      │  PromQL queries
      ▼
Prometheus
```

The flow is identical to how other SODA Contexture data-connector agents work.  
The OCS engine fetches context from `/get_ocs_prompt`, the LLM converts the NL query into a list of tool calls, and the FastMCP client executes them against this server.

---

## Available MCP Tools

| Tool | Description |
|---|---|
| `explain_ocs_policy` | Parse and explain the OCS config (policy statements, thresholds, workloads) |
| `current_metric_for_pods` | Instant value of any metric for a given list of pods |
| `workload_metrics` | Aggregate a metric by workload (`app` label), with optional time window |
| `top_n_pods_by_metric` | Top N pods by average metric value over a window |
| `pod_network_io` | Network receive/transmit rates (bytes/sec) per pod |
| `pods_exceeding_cpu` | Pods whose CPU rate exceeds a threshold |
| `pods_exceeding_memory` | Pods whose memory usage exceeds a threshold |
| `pod_status_summary` | Count of pods in each lifecycle phase (Running, Pending, Failed, …) |
| `recent_pod_events` | Most recent Kubernetes pod events by reason |
| `node_disk_usage` | Average and peak disk usage (%) per node over a time window |
| `node_memory_usage` | Average and peak memory usage (%) per node over a time window |
| `top_disk_pressure_nodes` | Nodes with disk usage above a threshold |
| `top_memory_pressure_nodes` | Nodes with memory usage above a threshold |
| `describe_cluster_health` | Plain-English cluster health summary from pod phase counts |
| `pod_restart_trend` | Top pods by restart count over a recent window |
| `detect_pod_anomalies` | Z-score anomaly detection across pods for any metric |
| `namespace_resource_summary` | CPU or memory usage broken down by namespace |
| `detect_crashloop_pods` | Pods in or approaching CrashLoopBackOff |
| `correlate_metrics` | Pearson correlation between two metrics across pods |
| `pod_event_timeline` | Snapshot of restarts, network I/O, and CPU for a specific pod |
| `node_condition_summary` | Nodes with non-Ready conditions (MemoryPressure, DiskPressure, …) |

All tools iterate over every instance in `prometheus_config.yaml` and return results keyed by instance name — same pattern as other agents returning `*_per_prometheus`.

---

## Configuration

Edit `config/prometheus_config.yaml` at the project root:

```yaml
prometheus_instances:
  - name: prometheus_1
    base_url: "http://localhost:9090"
    headers: {}
    disable_ssl: false

  # Add more instances as needed (e.g. multi-cluster):
  # - name: prometheus_2
  #   base_url: "http://localhost:9091"
  #   headers: {}
  #   disable_ssl: false
```

Ollama and MCP server URLs are configured in `config/ollama_config.yaml` and `config/mcp_server_config.yaml`.

---

## Getting Started

All commands below are run from the `pkg/agents/prometheus/` directory.

### 1. Install dependencies

```bash
cd pkg/agents/prometheus
pip install -r requirements.txt
```

### 2. Configure Prometheus instances

```bash
vi ../../config/prometheus_config.yaml
```

### 3. Test the connection

Before starting the server, verify config and connectivity:

```bash
python test_connection.py
```

Expected output:

```
Loading prometheus_config.yaml...
Found 1 instance(s): ['prometheus_1']
--------------------------------------------------
Instance : prometheus_1
URL      : http://localhost:9090
SSL      : enabled
Connection: OK
Pod count : 42 (from kube_pod_info)
Node count: 3 (from kube_node_info)
--------------------------------------------------
All instances OK.
```

### 4. Run the MCP server

**stdio transport** (default):

```bash
python server.py
```

**SSE/HTTP transport** (for use with `client_dynamic.py` or any HTTP MCP client):

```bash
python server.py --transport sse --port 8001
```

### 5. Run the NL agent (keyword-based)

For quick queries without Ollama:

```bash
python agent.py
```

Example queries: `cluster health`, `top cpu pods`, `disk pressure`, `crashloop pods`.

### 6. Run the full LLM-based client

For Ollama-powered natural language queries across any adaptor:

```bash
cd pkg/mcp
python client_dynamic.py
```

---

## Setting Up Prometheus on Minikube (Multi-Cluster Example)

```bash
# Start two clusters
minikube start -p minikube1
minikube start -p minikube2

# Deploy Prometheus on each
kubectl --context=minikube1 create namespace monitoring
kubectl --context=minikube1 apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/bundle.yaml

kubectl --context=minikube2 create namespace monitoring
kubectl --context=minikube2 apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/bundle.yaml

# Port-forward locally
kubectl --context=minikube1 -n monitoring port-forward svc/prometheus-operated 9090:9090 &
kubectl --context=minikube2 -n monitoring port-forward svc/prometheus-operated 9091:9090 &
```

Then add both to `config/prometheus_config.yaml`.

---

## Generating Test Data

`data_pusher.py` generates high-cardinality Kubernetes metrics and pushes them via the Prometheus Remote Write API. Useful for testing without a live cluster.

**Prerequisites:** enable remote write receiver in Prometheus:

```
--web.enable-remote-write-receiver
```

And increase the out-of-order time window for historical data:

```yaml
storage:
  tsdb:
    out_of_order_time_window: 15d
```

**Run:**

```bash
# With config file (edit config.json for scale)
python data_pusher.py --config config.json

# Or with inline flags
python data_pusher.py \
    --url http://localhost:9090/api/v1/write \
    --clusters 2 \
    --days 1 \
    --batch-size 100 \
    --scrape-interval 60
```

Default `config.json` pushes a small dataset (2 clusters, 1 day) suitable for quick testing.

---

## Adding a New Tool

1. Add a query function (or inline the query) in `mcp_tools.py`.
2. Register it in `tool_registry.py`.
3. Add an `@app.tool()` in `server.py` that calls `_instances()` + `get_client()`.
4. Optionally add a keyword branch in `agent.py` for direct NL routing.
