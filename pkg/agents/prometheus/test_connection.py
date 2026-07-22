#!/usr/bin/env python3
"""
Quick connectivity test for the Prometheus MCP agent.

Run from this directory:
    cd pkg/agents/prometheus
    python test_connection.py

Reads connection settings from config/prometheus_config.yaml.
Verifies that:
  1. The config file is found and parses correctly.
  2. Each configured instance accepts a connection.
  3. A basic PromQL query returns data without errors.
"""
import sys
import os

# Ensure local imports resolve regardless of working directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prometheus_connector import get_all_instances, get_client


def _hr():
    print("-" * 50)


def main():
    # ── 1. Config loading ────────────────────────────────
    print("Loading prometheus_config.yaml...")
    try:
        instances = get_all_instances()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if not instances:
        print(
            "ERROR: No instances found in prometheus_config.yaml. "
            "Add at least one entry under prometheus_instances:"
        )
        sys.exit(1)

    print(f"Found {len(instances)} instance(s): {[i.get('name') for i in instances]}\n")

    # ── 2. Per-instance checks ───────────────────────────
    all_ok = True
    for inst in instances:
        name = inst.get("name", "default")
        _hr()
        print(f"Instance : {name}")
        print(f"URL      : {inst.get('base_url')}")
        print(f"SSL      : {'disabled' if inst.get('disable_ssl') else 'enabled'}")

        # Connection + basic query test
        try:
            client = get_client(inst)
            # check_prometheus_connection() returns True if reachable
            ok = client.check_prometheus_connection()
            if ok:
                print("Connection: OK")
            else:
                print("Connection: FAILED — check_prometheus_connection() returned False")
                all_ok = False
                continue
        except Exception as exc:
            print(f"Connection: FAILED — {exc}")
            all_ok = False
            continue

        # Basic query: count pods
        try:
            result = client.custom_query("count(kube_pod_info)")
            pod_count = int(float(result[0]["value"][1])) if result else 0
            print(f"Pod count : {pod_count} (from kube_pod_info)")
        except Exception as exc:
            print(f"Query test: FAILED — {exc}")
            all_ok = False

        # Node count
        try:
            result = client.custom_query("count(kube_node_info)")
            node_count = int(float(result[0]["value"][1])) if result else 0
            print(f"Node count: {node_count} (from kube_node_info)")
        except Exception as exc:
            print(f"Node query: FAILED — {exc}")
            all_ok = False

    # ── 3. Summary ───────────────────────────────────────
    _hr()
    if all_ok:
        print("All instances OK.")
        sys.exit(0)
    else:
        print("One or more instances had errors (see above).")
        sys.exit(1)


if __name__ == "__main__":
    main()
