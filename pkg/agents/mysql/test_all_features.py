#!/usr/bin/env python3
"""
Comprehensive Feature Test Suite for MySQL MCP Agent.

Validates all 8 MCP tools against the local MySQL instance.
Requires `contexture_mysql_test` database to be populated with sample data.
"""

import sys
import os
import json

# Ensure imports resolve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_tools import (
    list_databases_tool,
    list_tables_tool,
    describe_table_tool,
    execute_query_tool,
    get_table_stats_tool,
    get_db_stats_tool,
    get_slow_queries_tool,
    check_db_health_tool,
)

def print_section(title: str):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_result(name: str, passed: bool, details: str = ""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {name}")
    if details:
        print(f"       -> {details}")

def run_tests():
    total_tests = 0
    passed_tests = 0

    def assert_test(name: str, condition: bool, details: str = ""):
        nonlocal total_tests, passed_tests
        total_tests += 1
        if condition:
            passed_tests += 1
        print_result(name, condition, details)
        return condition

    print_section("1. Database Discovery Tools")
    
    # Test list_databases
    res_db = list_databases_tool()
    assert_test("my_list_databases returns local instance", "local" in res_db)
    
    local_dbs = res_db.get("local", [])
    db_names = [db["name"] for db in local_dbs] if isinstance(local_dbs, list) else []
    assert_test("my_list_databases finds contexture_mysql_test", "contexture_mysql_test" in db_names, f"Found {len(db_names)} databases")

    # Test list_tables
    res_tbl = list_tables_tool("contexture_mysql_test")
    assert_test("my_list_tables returns local instance", "local" in res_tbl)
    
    local_tbls = res_tbl.get("local", [])
    tbl_names = [t["name"] for t in local_tbls] if isinstance(local_tbls, list) else []
    assert_test("my_list_tables finds customers table", "customers" in tbl_names)
    assert_test("my_list_tables finds products table", "products" in tbl_names)
    assert_test("my_list_tables finds orders table", "orders" in tbl_names)

    print_section("2. Schema Tools")
    
    # Test describe_table
    res_desc = describe_table_tool("contexture_mysql_test", "customers")
    local_desc = res_desc.get("local", {})
    assert_test("my_describe_table returns columns", "columns" in local_desc and len(local_desc["columns"]) > 0)
    
    cols = local_desc.get("columns", [])
    col_names = [c["name"] for c in cols]
    assert_test("my_describe_table includes specific columns", "customer_id" in col_names and "email" in col_names, f"Columns: {col_names}")

    print_section("3. Query Execution Tool")
    
    # Test execute_query (Valid SELECT)
    res_q1 = execute_query_tool("SELECT * FROM customers LIMIT 2")
    local_q1 = res_q1.get("local", {})
    assert_test("my_execute_query (SELECT) returns rows", "rows" in local_q1 and len(local_q1["rows"]) == 2)
    assert_test("my_execute_query (SELECT) returns correct row count", local_q1.get("row_count") == 2)
    assert_test("my_execute_query (SELECT) returns columns metadata", "columns" in local_q1 and len(local_q1["columns"]) > 0)

    # Test execute_query (Invalid statement type)
    res_q2 = execute_query_tool("UPDATE customers SET name = 'Test' WHERE customer_id = 1")
    local_q2 = res_q2.get("local", {})
    assert_test("my_execute_query blocks UPDATE", "error" in local_q2 and "Only SELECT / WITH" in local_q2["error"])

    res_q3 = execute_query_tool("DROP TABLE customers")
    local_q3 = res_q3.get("local", {})
    assert_test("my_execute_query blocks DROP", "error" in local_q3 and "Only SELECT / WITH" in local_q3["error"])

    print_section("4. Statistics & Health Tools")
    
    # Test get_table_stats
    res_tstat = get_table_stats_tool("contexture_mysql_test", "orders")
    local_tstat = res_tstat.get("local", {})
    assert_test("my_get_table_stats returns stats", "total_rows" in local_tstat and "data_size" in local_tstat)
    assert_test("my_get_table_stats engine is InnoDB", local_tstat.get("engine") == "InnoDB")

    # Test get_db_stats
    res_dbstat = get_db_stats_tool()
    local_dbstat = res_dbstat.get("local", {})
    assert_test("my_get_db_stats returns databases list", "databases" in local_dbstat)
    assert_test("my_get_db_stats returns global status", "status" in local_dbstat and "Uptime" in local_dbstat["status"])

    # Test get_slow_queries
    res_slow = get_slow_queries_tool()
    local_slow = res_slow.get("local", [])
    assert_test("my_get_slow_queries executes without error", isinstance(local_slow, list) or ("error" not in local_slow))

    # Test check_db_health
    res_health = check_db_health_tool()
    local_health = res_health.get("local", {})
    assert_test("my_check_db_health returns version", "version" in local_health)
    assert_test("my_check_db_health returns uptime", "uptime_seconds" in local_health)
    assert_test("my_check_db_health returns connections", "connections" in local_health)

    print_section("Summary")
    print(f"Total Tests:  {total_tests}")
    print(f"Passed:       {passed_tests}")
    print(f"Failed:       {total_tests - passed_tests}")
    
    if total_tests == passed_tests:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("\n💥 SOME TESTS FAILED!")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())
