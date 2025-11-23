# app/core/storage.py

# Управление SQLite

import sqlite3
from pathlib import Path
from typing import Iterable, Dict, Any

# Путь к файлу БД
DB_PATH = Path(__file__).resolve().parents[2] / "demo_data" / "demo.db"


def get_connection() -> sqlite3.Connection:
    # Получает соединение с БД, создает директорию с ней
    
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema() -> None:
    # Создает таблицы БД
    
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS repos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            path TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS confluence_spaces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            space_key TEXT NOT NULL,
            name TEXT NOT NULL,
            base_url TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS demo_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            question TEXT NOT NULL,
            expected_outline TEXT,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        );
        """
    )

    conn.commit()
    conn.close()


def clear_all() -> None:
    # Очищает данные из БД путем удаления записей из всех таблиц
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM demo_queries;")
    cur.execute("DELETE FROM confluence_spaces;")
    cur.execute("DELETE FROM repos;")
    cur.execute("DELETE FROM projects;")
    conn.commit()
    conn.close()


def insert_many(sql: str, rows: Iterable[Dict[str, Any]]) -> None:
    if not rows:
        return
    conn = get_connection()
    cur = conn.cursor()
    columns = list(rows[0].keys())
    placeholders = ", ".join([f":{c}" for c in columns])
    sql_full = f"{sql} ({', '.join(columns)}) VALUES ({placeholders})"
    cur.executemany(sql_full, rows)
    conn.commit()
    conn.close()