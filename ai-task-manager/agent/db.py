"""SQLite storage for tasks and conversation history."""

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "tasks.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                title    TEXT NOT NULL,
                desc     TEXT,
                priority INTEGER DEFAULT 2,   -- 1=alta 2=media 3=bassa
                status   TEXT DEFAULT 'todo', -- todo | doing | done
                project  TEXT,
                due_date TEXT,
                created  TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                role    TEXT NOT NULL,
                content TEXT NOT NULL   -- JSON serializzato
            )
        """)


def add_task(title: str, desc: str = "", priority: int = 2,
             project: str = "", due_date: str = "") -> dict:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (title, desc, priority, project, due_date) VALUES (?,?,?,?,?)",
            (title, desc, priority, project, due_date),
        )
        return get_task(cur.lastrowid)


def get_task(task_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        return dict(row) if row else None


def list_tasks(status: str = "all", project: str = "") -> list[dict]:
    query = "SELECT * FROM tasks"
    params: list = []
    conditions = []
    if status != "all":
        conditions.append("status=?")
        params.append(status)
    if project:
        conditions.append("project=?")
        params.append(project)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY priority ASC, created ASC"
    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def update_task(task_id: int, **fields) -> dict | None:
    allowed = {"title", "desc", "priority", "status", "project", "due_date"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return get_task(task_id)
    sets = ", ".join(f"{k}=?" for k in updates)
    vals = list(updates.values()) + [task_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE tasks SET {sets} WHERE id=?", vals)
    return get_task(task_id)


def delete_task(task_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        return cur.rowcount > 0


# ── History ──────────────────────────────────────────────────────────────────

def save_message(role: str, content) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO history (role, content) VALUES (?, ?)",
            (role, json.dumps(content, default=str)),
        )


def load_history() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT role, content FROM history ORDER BY id").fetchall()
    return [{"role": r["role"], "content": json.loads(r["content"])} for r in rows]


def clear_history() -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM history")
