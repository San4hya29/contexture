#!/usr/bin/env python3
"""
Quick connectivity test for the PostgreSQL MCP agent.

Run from this directory:
    cd pkg/agents/postgres
    python test_connection.py

Reads connection settings from config/postgres_config.yaml.
Verifies that:
  1. The config file is found and parses correctly.
  2. Each configured instance accepts a connection.
  3. list_databases() and list_schemas() return data without errors.
"""
import sys
import os

# Ensure imports resolve regardless of working directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from postgres_connector import get_all_instances, _get_conn, list_databases, list_schemas


def _hr():
    print("-" * 50)


def main():
    # ── 1. Config loading ────────────────────────────────
    print("Loading postgres_config.yaml...")
    try:
        instances = get_all_instances()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print(
            "\nMake sure config/postgres_config.yaml exists at the repo root.\n"
            "Copy the template if needed:\n"
            "  cp config/postgres_config.yaml.example config/postgres_config.yaml"
        )
        sys.exit(1)

    if not instances:
        print("ERROR: No instances found in postgres_config.yaml. Add at least one entry under postgres_instances:")
        sys.exit(1)

    print(f"Found {len(instances)} instance(s): {[i.get('name') for i in instances]}\n")

    # ── 2. Per-instance checks ───────────────────────────
    all_ok = True
    for inst in instances:
        name = inst.get("name", "default")
        _hr()
        print(f"Instance : {name}")
        print(f"Host     : {inst.get('host')}:{inst.get('port', 5432)}")
        print(f"Database : {inst.get('dbname')}")
        print(f"User     : {inst.get('user')}")

        # Connection test
        try:
            conn = _get_conn(inst)
            conn.close()
            print("Connection: OK")
        except Exception as exc:
            print(f"Connection: FAILED — {exc}")
            all_ok = False
            continue

        # list_databases
        try:
            dbs = list_databases(inst)
            print(f"Databases ({len(dbs)}):")
            for db in dbs:
                print(f"  - {db['name']}  [{db['encoding']}]  {db['size']}")
        except Exception as exc:
            print(f"list_databases: FAILED — {exc}")
            all_ok = False

        # list_schemas
        try:
            schemas = list_schemas(inst)
            print(f"Schemas   : {', '.join(schemas) if schemas else '(none)'}")
        except Exception as exc:
            print(f"list_schemas: FAILED — {exc}")
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
