#!/usr/bin/env python3
import os
import yaml
import redis
import argparse

def load_dataset(file_path: str):
    # Check if absolute path or relative to datasets
    if not os.path.exists(file_path):
        # Check in new_redis-connector/datasets or parent redis-connector/datasets
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        paths_to_try = [
            os.path.join(base_dir, "datasets", file_path),
            os.path.join(os.path.dirname(base_dir), "redis-connector", "datasets", file_path),
            os.path.join(base_dir, file_path)
        ]
        for p in paths_to_try:
            if os.path.exists(p):
                file_path = p
                break

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file not found: {file_path}")

    with open(file_path, "r") as f:
        return yaml.safe_load(f)

def load_config():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "config.yaml")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f) or {}
    return {}

def seed_database(dataset_path: str):
    config = load_config()
    redis_cfg = config.get("redis", {})

    host = os.environ.get("REDIS_HOST", redis_cfg.get("host", "localhost"))
    port = int(os.environ.get("REDIS_PORT", redis_cfg.get("port", 6379)))
    username = os.environ.get("REDIS_USERNAME", redis_cfg.get("username", None)) or None
    password = os.environ.get("REDIS_PASSWORD", redis_cfg.get("password", None)) or None
    db = int(os.environ.get("REDIS_DB", redis_cfg.get("db", 0)))

    print(f"Connecting to Redis at {host}:{port} db={db}...")
    client = redis.Redis(
        host=host,
        port=port,
        username=username,
        password=password,
        db=db,
        decode_responses=True
    )

    data = load_dataset(dataset_path)
    keys = data.get("keys", {})

    print(f"Seeding {len(keys)} keys from '{dataset_path}'...")
    for key, spec in keys.items():
        key_type = spec.get("type", "").lower()
        ttl = spec.get("ttl")

        # Clean key
        client.delete(key)

        if key_type == "string":
            client.set(key, spec.get("value", ""))
        elif key_type == "hash":
            client.hset(key, mapping=spec.get("fields", {}))
        elif key_type == "list":
            items = spec.get("items", [])
            if items:
                client.rpush(key, *items)
        elif key_type == "set":
            members = spec.get("members", [])
            if members:
                client.sadd(key, *members)
        elif key_type == "zset":
            scores = spec.get("scores", {})
            if scores:
                client.zadd(key, scores)
        elif key_type == "stream":
            entries = spec.get("entries", [])
            for entry in entries:
                entry_id = entry.get("id", "*")
                fields = entry.get("fields", {})
                client.xadd(key, fields, id=entry_id)
        else:
            print(f"Warning: Unknown key type '{key_type}' for key '{key}'")
            continue

        if ttl:
            client.expire(key, int(ttl))

        print(f"Successfully seeded {key_type} key: {key}")

    print("Database seeding completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Redis database")
    parser.add_argument("--dataset", required=True, help="Path or filename of dataset yaml")
    args = parser.parse_args()
    seed_database(args.dataset)
