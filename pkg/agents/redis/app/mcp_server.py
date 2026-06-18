import os
import yaml
import redis
import json
import asyncio
from typing import List, Dict, Any, Optional
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server.stdio import stdio_server

# Redis Agent Configuration
# This agent is strictly READ-ONLY by design. No write, modify, admin, or script tools are exposed.
READ_ONLY_MODE = True

# Load configuration relative to this file
def load_config() -> Dict[str, Any]:
    base_dir = os.path.abspath(__file__)
    for _ in range(5):
        base_dir = os.path.dirname(base_dir)
    config_path = os.path.join(base_dir, "config", "redis_config.yaml")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f) or {}
    return {}

config = load_config()
redis_cfg = config.get("redis", {})

redis_host = os.environ.get("REDIS_HOST", redis_cfg.get("host", "localhost"))
redis_port = int(os.environ.get("REDIS_PORT", redis_cfg.get("port", 6379)))
redis_username = os.environ.get("REDIS_USERNAME", redis_cfg.get("username", None)) or None
redis_password = os.environ.get("REDIS_PASSWORD", redis_cfg.get("password", None)) or None
redis_db = int(os.environ.get("REDIS_DB", redis_cfg.get("db", 0)))

# Initialize Redis client
redis_client = redis.Redis(
    host=redis_host,
    port=redis_port,
    username=redis_username,
    password=redis_password,
    db=redis_db,
    decode_responses=True
)

ALLOWED_READONLY_COMMANDS = {
    "GET",
    "MGET",
    "EXISTS",
    "TYPE",
    "TTL",
    "PTTL",

    "HGET",
    "HMGET",
    "HGETALL",
    "HKEYS",
    "HVALS",
    "HLEN",
    "HEXISTS",

    "LRANGE",
    "LLEN",
    "LINDEX",

    "SMEMBERS",
    "SCARD",
    "SISMEMBER",
    "SINTER",
    "SUNION",
    "SDIFF",

    "ZRANGE",
    "ZREVRANGE",
    "ZRANK",
    "ZREVRANK",
    "ZSCORE",
    "ZCARD",
    "ZRANGEWITHSCORES",

    "SCAN",

    "JSON.GET"
}

def make_json_safe(val: Any) -> Any:
    """Recursively processes nested Redis structures and converts them to JSON-safe objects."""
    if isinstance(val, bytes):
        return val.decode("utf-8", errors="replace")
    elif isinstance(val, set):
        return [make_json_safe(x) for x in val]
    elif isinstance(val, tuple):
        return [make_json_safe(x) for x in val]
    elif isinstance(val, list):
        return [make_json_safe(x) for x in val]
    elif isinstance(val, dict):
        return {make_json_safe(k): make_json_safe(v) for k, v in val.items()}
    return val

server = Server("redis-mcp-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="discover_schema",
            description="Discover the database key schema by scanning keys and grouping them into pattern groups (e.g. user:* -> hash). Call this tool first before querying unknown datasets to understand the structure of the keyspace.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 1000, "description": "Maximum number of keys to scan to determine schema"}
                }
            }
        ),
        types.Tool(
            name="inspect_key",
            description="Inspect the structural metadata of a key (e.g. fields in a hash, length of a list, cardinality of a set) without fetching the key's full data values. Use this to understand key layout before querying.",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Redis key to inspect"}
                },
                "required": ["key"]
            }
        ),
        types.Tool(
            name="get",
            description="Retrieve the value of a string key in Redis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string"}
                },
                "required": ["key"]
            }
        ),
        types.Tool(
            name="hgetall",
            description="Get all the fields and values in a hash key.",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string"}
                },
                "required": ["key"]
            }
        ),
        types.Tool(
            name="zrange",
            description="Return a range of members in a sorted set (by index). Results are sorted lowest-to-highest score. Set desc=true to sort highest-to-lowest.",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "start": {"type": "integer", "default": 0},
                    "stop": {"type": "integer", "default": -1},
                    "withscores": {"type": "boolean", "default": True},
                    "desc": {"type": "boolean", "default": False}
                },
                "required": ["key"]
            }
        ),
        types.Tool(
            name="xrange",
            description="Return a range of elements in a stream.",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "start": {"type": "string", "default": "-"},
                    "end": {"type": "string", "default": "+"},
                    "count": {"type": "integer"}
                },
                "required": ["key"]
            }
        ),
        types.Tool(
            name="smembers",
            description="Get all the members in a set key in Redis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string"}
                },
                "required": ["key"]
            }
        ),
        types.Tool(
            name="lrange",
            description="Get a range of elements in a list key in Redis. Use start=0 and stop=-1 to get all elements.",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "start": {"type": "integer", "default": 0},
                    "stop": {"type": "integer", "default": -1}
                },
                "required": ["key"]
            }
        ),
        types.Tool(
            name="key_type",
            description="Retrieve the type of a key in Redis (e.g. string, hash, list, set, zset, stream).",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string"}
                },
                "required": ["key"]
            }
        ),
        types.Tool(
            name="execute_readonly_command",
            description="Execute a Redis read-only command with arguments. Use this tool only when no dedicated Redis MCP tool exists for the requested operation. Only safe read-only commands are allowed. Any write, administrative, scripting, pub/sub, configuration, or dangerous command must be rejected.",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Redis command to execute"
                    },
                    "args": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Arguments for the Redis command"
                    }
                },
                "required": ["command"]
            }
        ),
        types.Tool(
            name="scan_keys",
            description="Scan the keyspace for keys matching a pattern. Avoids blocking the Redis server.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "default": "*"},
                    "count": {"type": "integer", "default": 100}
                }
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    if not arguments:
        arguments = {}
    try:
        if name == "discover_schema":
            limit = int(arguments.get("limit", 1000))
            cursor = 0
            all_keys = []
            while True:
                cursor, keys = redis_client.scan(cursor=cursor, count=limit)
                all_keys.extend(keys)
                if cursor == 0 or len(all_keys) >= limit:
                    break
            all_keys = all_keys[:limit]
            
            if all_keys:
                pipe = redis_client.pipeline()
                for k in all_keys:
                    pipe.type(k)
                types_res = pipe.execute()
                
                groups = {}
                for k, ktype in zip(all_keys, types_res):
                    if ":" in k:
                        parts = k.rsplit(":", 1)
                        pattern = parts[0] + ":*"
                    else:
                        pattern = k
                    key_group = (pattern, ktype)
                    if key_group not in groups:
                        groups[key_group] = {"count": 0, "samples": []}
                    groups[key_group]["count"] += 1
                    if len(groups[key_group]["samples"]) < 3:
                        groups[key_group]["samples"].append(k)
                
                patterns = []
                for (pattern, ktype), info in groups.items():
                    patterns.append({
                        "pattern": pattern,
                        "type": ktype,
                        "count": info["count"],
                        "sample_keys": info["samples"]
                    })
            else:
                patterns = []
            res = json.dumps({"patterns": patterns})
        elif name == "inspect_key":
            key = arguments.get("key")
            if not redis_client.exists(key):
                res = json.dumps({"error": f"Key '{key}' does not exist."})
            else:
                ktype = redis_client.type(key)
                ttl = redis_client.ttl(key)
                metadata = {}
                
                is_json = False
                if ktype.lower() in ("rejson-rl", "json"):
                    is_json = True
                else:
                    try:
                        redis_client.execute_command("JSON.TYPE", key)
                        is_json = True
                    except Exception:
                        pass
                
                if is_json:
                    try:
                        ktype = "json"
                        keys = redis_client.execute_command("JSON.OBJKEYS", key)
                        metadata = {
                            "top_level_keys": make_json_safe(keys) if keys else []
                        }
                    except Exception:
                        metadata = {}
                elif ktype == "string":
                    try:
                        metadata = {"length": redis_client.strlen(key)}
                    except Exception:
                        pass
                elif ktype == "hash":
                    try:
                        metadata = {
                            "field_count": redis_client.hlen(key),
                            "fields": list(redis_client.hkeys(key))
                        }
                    except Exception:
                        pass
                elif ktype == "list":
                    try:
                        metadata = {"length": redis_client.llen(key)}
                    except Exception:
                        pass
                elif ktype == "set":
                    try:
                        metadata = {"cardinality": redis_client.scard(key)}
                    except Exception:
                        pass
                elif ktype == "zset":
                    try:
                        metadata = {"cardinality": redis_client.zcard(key)}
                    except Exception:
                        pass
                elif ktype == "stream":
                    try:
                        metadata = {"entry_count": redis_client.xlen(key)}
                    except Exception:
                        pass
                
                res = json.dumps({
                    "key": key,
                    "type": ktype,
                    "ttl": ttl,
                    "metadata": metadata
                })
        elif name == "get":
            key = arguments.get("key")
            val = redis_client.get(key)
            res = json.dumps({"key": key, "value": val})
        elif name == "hgetall":
            key = arguments.get("key")
            val = redis_client.hgetall(key)
            res = json.dumps({"key": key, "value": val})
        elif name == "zrange":
            key = arguments.get("key")
            start = arguments.get("start", 0)
            stop = arguments.get("stop", -1)
            withscores = arguments.get("withscores", True)
            desc = arguments.get("desc", False)
            val = redis_client.zrange(key, start, stop, desc=desc, withscores=withscores)
            res = json.dumps({"key": key, "value": val})
        elif name == "xrange":
            key = arguments.get("key")
            start = arguments.get("start", "-")
            end = arguments.get("end", "+")
            count = arguments.get("count")
            val = redis_client.xrange(key, min=start, max=end, count=count)
            res = json.dumps({"key": key, "value": val})
        elif name == "smembers":
            key = arguments.get("key")
            val = list(redis_client.smembers(key))
            res = json.dumps({"key": key, "value": val})
        elif name == "lrange":
            key = arguments.get("key")
            start = arguments.get("start", 0)
            stop = arguments.get("stop", -1)
            val = redis_client.lrange(key, start, stop)
            res = json.dumps({"key": key, "value": val})
        elif name == "key_type":
            key = arguments.get("key")
            val = redis_client.type(key)
            res = json.dumps({"key": key, "value": val})
        elif name == "execute_readonly_command":
            cmd_raw = arguments.get("command", "")
            cmd = cmd_raw.upper().strip()
            args = arguments.get("args", [])
            
            if cmd not in ALLOWED_READONLY_COMMANDS:
                res = json.dumps({
                    "error": f"Command '{cmd}' is not allowed. Only approved read-only Redis commands may be executed."
                })
            else:
                val_raw = redis_client.execute_command(cmd, *args)
                val = make_json_safe(val_raw)
                res = json.dumps({
                    "command": cmd,
                    "args": args,
                    "result": val
                })
        elif name == "scan_keys":
            pattern = arguments.get("pattern", "*")
            count = arguments.get("count", 100)
            cursor, keys = redis_client.scan(cursor=0, match=pattern, count=count)
            res = json.dumps({"keys": keys, "cursor": cursor})
        else:
            raise ValueError(f"Unknown tool: {name}")
            
        return [types.TextContent(type="text", text=res)]
    except Exception as e:
        return [types.TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="redis-mcp-server",
                server_version="0.1.0",
                capabilities=types.ServerCapabilities(
                    tools=types.ToolsCapability(listChanged=True)
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
