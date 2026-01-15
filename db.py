from __future__ import annotations

import random
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Literal

import pandas as pd

Relationship = Literal["Friend", "Family"]


DB_PATH = Path("data") / "texter.sqlite"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS people (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                relationship TEXT NOT NULL CHECK (relationship IN ('Friend','Family')),
                drawn INTEGER NOT NULL DEFAULT 0 CHECK (drawn IN (0,1)),
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_people_rel_name
            ON people(relationship, name);
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            """
        )
        # store last pick per relationship (like your prev_d)
        conn.execute("INSERT OR IGNORE INTO meta(key,value) VALUES ('prev_friend','');")
        conn.execute("INSERT OR IGNORE INTO meta(key,value) VALUES ('prev_family','');")


def get_people_df() -> pd.DataFrame:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, name, relationship, drawn FROM people ORDER BY relationship, name;"
        ).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


def get_counts() -> dict:
    with _connect() as conn:
        out = {}
        for rel in ("Friend", "Family"):
            total = conn.execute(
                "SELECT COUNT(*) AS n FROM people WHERE relationship=?;", (rel,)
            ).fetchone()["n"]
            remaining = conn.execute(
                "SELECT COUNT(*) AS n FROM people WHERE relationship=? AND drawn=0;",
                (rel,),
            ).fetchone()["n"]
            out[rel] = {"total": total, "remaining": remaining}
        return out


def _get_meta(key: str) -> str:
    with _connect() as conn:
        row = conn.execute("SELECT value FROM meta WHERE key=?;", (key,)).fetchone()
    return (row["value"] if row else "") or ""


def _set_meta(key: str, value: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO meta(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value;",
            (key, value),
        )


def reset_if_needed(relationship: Relationship) -> None:
    """If all names in this relationship are drawn, reset drawn=0 for that relationship."""
    with _connect() as conn:
        total = conn.execute(
            "SELECT COUNT(*) AS n FROM people WHERE relationship=?;", (relationship,)
        ).fetchone()["n"]
        if total == 0:
            return

        remaining = conn.execute(
            "SELECT COUNT(*) AS n FROM people WHERE relationship=? AND drawn=0;",
            (relationship,),
        ).fetchone()["n"]

        if remaining == 0:
            conn.execute(
                "UPDATE people SET drawn=0 WHERE relationship=?;",
                (relationship,),
            )


def _pick_random_name(relationship: Relationship) -> str:
    """
    Picks a random undrawn name, avoiding the immediate previous name if possible.
    Mirrors your "trapped" loop idea, but in DB form.
    """
    reset_if_needed(relationship)

    prev_key = "prev_friend" if relationship == "Friend" else "prev_family"
    prev_name = _get_meta(prev_key)

    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, name FROM people WHERE relationship=? AND drawn=0;",
            (relationship,),
        ).fetchall()

    if not rows:
        raise ValueError(f"No people found for relationship={relationship}")

    # If we have >1 option, avoid repeating prev
    candidates = [dict(r) for r in rows]
    if prev_name and len(candidates) > 1:
        filtered = [c for c in candidates if c["name"] != prev_name]
        if filtered:
            candidates = filtered

    choice = random.choice(candidates)
    chosen_name = choice["name"]
    chosen_id = choice["id"]

    # Mark drawn + update prev
    with _connect() as conn:
        conn.execute("UPDATE people SET drawn=1 WHERE id=?;", (chosen_id,))
    _set_meta(prev_key, chosen_name)

    return chosen_name


@dataclass
class DrawResult:
    friend: str
    family: str


def draw_friend_and_family() -> DrawResult:
    """
    Draws one Friend and one Family, independently,
    each following the "no repeats until cycle completes" rule.
    """
    friend = _pick_random_name("Friend")
    family = _pick_random_name("Family")
    return DrawResult(friend=friend, family=family)


def upsert_people(df: pd.DataFrame) -> None:
    """
    Save edits from the editor.
    Expected columns: id, name, relationship, drawn
    """
    # basic cleanup
    df = df.copy()
    df["name"] = df["name"].astype(str).str.strip()
    df = df[df["name"] != ""]

    with _connect() as conn:
        existing_ids = set(
            r["id"]
            for r in conn.execute("SELECT id FROM people;").fetchall()
        )
        incoming_ids = set(int(x) for x in df["id"].dropna().astype(int).tolist())

        # Delete rows removed in editor (only those that existed)
        to_delete = sorted(existing_ids - incoming_ids)
        if to_delete:
            conn.executemany("DELETE FROM people WHERE id=?;", [(i,) for i in to_delete])

        # Upsert remaining
        for _, row in df.iterrows():
            rid = int(row["id"]) if pd.notna(row["id"]) else None
            name = str(row["name"]).strip()
            rel = row["relationship"]
            drawn = int(row["drawn"]) if "drawn" in row and pd.notna(row["drawn"]) else 0

            if rid is None or rid == 0:
                # insert
                conn.execute(
                    "INSERT OR IGNORE INTO people(name, relationship, drawn) VALUES(?,?,?);",
                    (name, rel, drawn),
                )
            else:
                # update
                conn.execute(
                    "UPDATE people SET name=?, relationship=?, drawn=? WHERE id=?;",
                    (name, rel, drawn, rid),
                )


def seed_from_your_dicts(friends_d: dict[str, int], family_d: dict[str, int]) -> None:
    """
    Optional helper: migrate from your existing texter_log dicts into SQLite once.
    """
    init_db()
    with _connect() as conn:
        for name, drawn in friends_d.items():
            conn.execute(
                "INSERT OR IGNORE INTO people(name, relationship, drawn) VALUES(?,?,?);",
                (name.strip(), "Friend", int(drawn)),
            )
        for name, drawn in family_d.items():
            conn.execute(
                "INSERT OR IGNORE INTO people(name, relationship, drawn) VALUES(?,?,?);",
                (name.strip(), "Family", int(drawn)),
            )
