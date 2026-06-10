# MongoDB Agent for Contexture

## Overview

The MongoDB Agent enables natural language interaction with MongoDB databases through the Contexture framework.

Users can ask questions in plain English, and the agent translates those requests into MongoDB operations and returns structured results.

Examples:

- Show customers
- Display products
- How many customers are available?
- List all products

---

## Architecture

User Query
    ↓
MongoDB Agent
    ↓
MCP Tools
    ↓
MongoDB Connector
    ↓
MongoDB Database
    ↓
Response Returned

---

## Components

### agent.py

Main agent responsible for processing user queries and routing requests.

### mongo_connector.py

Handles MongoDB database connectivity and query execution.

### mcp_tools.py

Defines MCP tools used by the agent.

### tool_registry.py

Registers available tools and makes them accessible to the agent.

### test_queries.py

Contains test queries used for validation.

### test_connection.py

Used for MongoDB connection testing.

---

## Features

- Natural language query support
- MongoDB integration
- MCP-based tool execution
- Customer data retrieval
- Product data retrieval
- Customer count retrieval
- Extensible architecture

---

## Example Queries

### Show Customers

Input:

show customers

Output:

[
  {
    "name": "Ravi",
    "city": "Bangalore",
    "age": 22
  }
]

---

### Show Products

Input:

display products

Output:

[
  {
    "product_name": "Laptop",
    "price": 50000
  }
]

---

### Count Customers

Input:

how many customers

Output:

{
  "count": 5
}

---

## Setup

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Start MongoDB

Ensure MongoDB is running locally.

### Run Agent

```bash
python api.py
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

---

## Validation

The following queries were successfully tested:

1. show customers
2. display products
3. how many customers
4. list customers
5. show available products

---

## Folder Structure

pkg/
└── agents/
    └── mongodb/
        ├── README.md
        ├── agent.py
        ├── mongo_connector.py
        ├── mcp_tools.py
        ├── tool_registry.py
        ├── test_queries.py
        └── test_connection.py
