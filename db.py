import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS raw_samples (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id      TEXT NOT NULL,
            source      TEXT NOT NULL,
            keyword     TEXT NOT NULL,
            period      TEXT NOT NULL,
            sample_idx  INTEGER NOT NULL,
            value       REAL,
            collected_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS summaries (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id           TEXT NOT NULL,
            source           TEXT NOT NULL,
            keyword          TEXT NOT NULL,
            period           TEXT NOT NULL,
            median_val       REAL,
            mean_val         REAL,
            std_val          REAL,
            cv               REAL,
            confidence       TEXT,
            outliers_removed INTEGER DEFAULT 0,
            created_at       TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS demographics (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id     TEXT NOT NULL,
            keyword    TEXT NOT NULL,
            period     TEXT NOT NULL,
            gender     TEXT,
            age_group  TEXT,
            value      REAL,
            created_at TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def save_raw_samples(run_id, source, keyword, period, samples, collected_at):
    conn = get_conn()
    conn.executemany(
        "INSERT INTO raw_samples (run_id,source,keyword,period,sample_idx,value,collected_at) VALUES (?,?,?,?,?,?,?)",
        [(run_id, source, keyword, period, i, v, collected_at) for i, v in enumerate(samples)]
    )
    conn.commit()
    conn.close()


def save_summary(run_id, source, keyword, period, stats, created_at):
    conn = get_conn()
    conn.execute(
        """INSERT INTO summaries
           (run_id,source,keyword,period,median_val,mean_val,std_val,cv,confidence,outliers_removed,created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (run_id, source, keyword, period,
         stats["median"], stats["mean"], stats["std"],
         stats["cv"], stats["confidence"], stats["outliers_removed"], created_at)
    )
    conn.commit()
    conn.close()


def save_demographics(run_id, keyword, rows, created_at):
    conn = get_conn()
    conn.executemany(
        "INSERT INTO demographics (run_id,keyword,period,gender,age_group,value,created_at) VALUES (?,?,?,?,?,?,?)",
        [(run_id, keyword, r["period"], r.get("gender"), r.get("age_group"), r["value"], created_at)
         for r in rows]
    )
    conn.commit()
    conn.close()
