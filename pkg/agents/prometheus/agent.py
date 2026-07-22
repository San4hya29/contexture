"""
Natural-language query router for the Prometheus agent.

Maps keyword patterns to tool calls — mirrors the pattern in other
SODA Contexture agents (postgres/agent.py, mongodb/agent.py).

For richer NL→workflow routing backed by Ollama, use
pkg/mcp/client_dynamic.py which talks to the FastMCP server directly.
"""

from tool_registry import TOOLS


def process_query(query: str) -> dict:
    q = query.lower()

    # ── cluster / health overview ────────────────────────────────────────────
    if "cluster health" in q or "overall health" in q or "cluster status" in q:
        return TOOLS["describe_cluster_health"]()

    # ── pod status / phase ───────────────────────────────────────────────────
    if "pod status" in q or "pod phase" in q or "pod summary" in q:
        return TOOLS["pod_status_summary"]()

    # ── crashloop ────────────────────────────────────────────────────────────
    if "crashloop" in q or "crash loop" in q or "crashing" in q:
        return TOOLS["detect_crashloop_pods"]()

    # ── restart trend ────────────────────────────────────────────────────────
    if "restart" in q and "trend" in q:
        return TOOLS["pod_restart_trend"]()
    if "restart" in q:
        return TOOLS["pod_restart_trend"]()

    # ── anomaly detection ────────────────────────────────────────────────────
    if "anomal" in q:
        return TOOLS["detect_pod_anomalies"]()

    # ── CPU pressure ─────────────────────────────────────────────────────────
    if "cpu" in q and ("exceed" in q or "high" in q or "pressure" in q or "threshold" in q):
        return TOOLS["pods_exceeding_cpu"]()
    if "cpu" in q and "top" in q:
        return TOOLS["top_n_pods_by_metric"](metric_name="container_cpu_usage_seconds_total")

    # ── memory pressure ──────────────────────────────────────────────────────
    if "memory" in q and ("exceed" in q or "high" in q or "pressure" in q or "threshold" in q):
        return TOOLS["pods_exceeding_memory"]()
    if "memory" in q and "node" in q:
        return TOOLS["top_memory_pressure_nodes"]()
    if "memory pressure" in q:
        return TOOLS["top_memory_pressure_nodes"]()
    if "memory usage" in q and "node" in q:
        return TOOLS["node_memory_usage"]()
    if "memory" in q and "top" in q:
        return TOOLS["top_n_pods_by_metric"](metric_name="container_memory_usage_bytes")

    # ── disk pressure ─────────────────────────────────────────────────────────
    if "disk" in q and ("pressure" in q or "exceed" in q or "high" in q):
        return TOOLS["top_disk_pressure_nodes"]()
    if "disk" in q:
        return TOOLS["node_disk_usage"]()

    # ── node memory ──────────────────────────────────────────────────────────
    if "node memory" in q or ("node" in q and "memory" in q):
        return TOOLS["node_memory_usage"]()

    # ── node conditions ──────────────────────────────────────────────────────
    if "node condition" in q or "node status" in q or "node health" in q:
        return TOOLS["node_condition_summary"]()

    # ── pod event timeline ───────────────────────────────────────────────────
    if "timeline" in q or "event" in q:
        # Try to extract a pod name from the query
        parts = q.split()
        pod_name = ""
        for i, p in enumerate(parts):
            if p in ("pod", "for") and i + 1 < len(parts):
                pod_name = parts[i + 1]
                break
        if pod_name:
            return TOOLS["pod_event_timeline"](pod_name=pod_name)
        return {"message": "Please specify a pod name, e.g. 'event timeline for pod my-pod-xyz'"}

    # ── workload metrics ─────────────────────────────────────────────────────
    if "workload" in q:
        parts = q.split()
        workload_name = ""
        for i, p in enumerate(parts):
            if p == "workload" and i + 1 < len(parts):
                workload_name = parts[i + 1]
                break
        if workload_name:
            return TOOLS["workload_metrics"](workload_name=workload_name)
        return {"message": "Please specify a workload name, e.g. 'workload metrics for workload frontend'"}

    # ── top pods (generic) ───────────────────────────────────────────────────
    if "top" in q and "pod" in q:
        return TOOLS["top_n_pods_by_metric"]()

    return {
        "message": (
            "No matching tool found. Try asking about: cluster health, pod status, "
            "CPU/memory/disk usage or pressure, restarts, crashloop pods, node conditions, "
            "pod events, or workload metrics."
        )
    }


if __name__ == "__main__":
    while True:
        query = input("\nEnter your query (or 'exit' to quit): ").strip()
        if query.lower() == "exit":
            break
        result = process_query(query)
        import json
        print(json.dumps(result, indent=2, default=str))
