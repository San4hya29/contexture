#!/usr/bin/env python3
import os
import sys
import yaml
import redis

def main():
    try:
        # 1. Resolve config path (5 levels up from contexture/pkg/agents/redis/test_connection.py)
        base_dir = os.path.abspath(__file__)
        for _ in range(4):
            base_dir = os.path.dirname(base_dir)
        config_path = os.path.join(base_dir, "config", "redis_config.yaml")
        
        print("Loading redis_config.yaml...\n")
        if not os.path.exists(config_path):
            print(f"ERROR: Configuration file not found at {config_path}")
            sys.exit(1)
            
        with open(config_path, "r") as f:
            config = yaml.safe_load(f) or {}
            
        redis_cfg = config.get("redis", {})
        host = os.environ.get("REDIS_HOST", redis_cfg.get("host", "localhost"))
        port = int(os.environ.get("REDIS_PORT", redis_cfg.get("port", 6379)))
        username = os.environ.get("REDIS_USERNAME", redis_cfg.get("username", None)) or None
        password = os.environ.get("REDIS_PASSWORD", redis_cfg.get("password", None)) or None
        db = int(os.environ.get("REDIS_DB", redis_cfg.get("db", 0)))
        
        # 2. Connect & Ping
        print("Connecting to Redis...")
        client = redis.Redis(
            host=host,
            port=port,
            username=username,
            password=password,
            db=db,
            decode_responses=True
        )
        
        client.ping()
        print("Connection: OK\n")
        
        # 3. Database Info
        keys_found = len(client.keys("*"))
        print(f"Database: {db}")
        print(f"Keys Found: {keys_found}\n")
        
        # 4. Redis Server Version
        info = client.info()
        redis_version = info.get("redis_version", "unknown")
        print(f"Redis Version: {redis_version}\n")
        
        print("All checks passed.")
        
    except Exception as e:
        print(f"\nERROR: Connection check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
