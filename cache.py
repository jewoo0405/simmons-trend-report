import sqlite3
import json
import hashlib
import os
from datetime import datetime, timedelta

CACHE_DB = os.path.join(os.path.dirname(__file__), "cache.db")


def _conn():
    c = sqlite3.connect(CACHE_DB)
    c.execute("""CREATE TABLE IF NOT EXISTS cache (
        key TEXT PRIMARY KEY,
        value TEXT,
        expires_at TEXT
    )""")
    c.commit()
    return c


def _key(source, params):
    raw = json.dumps({"source": source, "params": params}, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()


def get(source, params):
    k = _key(source, params)
    c = _conn()
    row = c.execute("SELECT value, expires_at FROM cache WHERE key=?", (k,)).fetchone()
    c.close()
    if not row:
        return None
    if datetime.fromisoformat(row[1]) < datetime.now():
        return None
    return json.loads(row[0])


def set(source, params, value, ttl_hours=24):
    k = _key(source, params)
    expires = (datetime.now() + timedelta(hours=ttl_hours)).isoformat()
    c = _conn()
    c.execute("INSERT OR REPLACE INTO cache (key,value,expires_at) VALUES (?,?,?)",
              (k, json.dumps(value), expires))
    c.commit()
    c.close()
