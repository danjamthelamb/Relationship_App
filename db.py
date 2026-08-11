####################
# Database Functions (db.py)
####################
from __future__ import annotations

import random
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Literal

import pandas as pd

Relationship = Literal["Friend", "Family"]

@dataclass(frozen=True)
class User:
    id: int
    auth_provider: str
    auth_subject: str
    email: str
    display_name: str | None

DB_PATH = Path("data") / "texter.sqlite"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    return conn

def _migrate_people_to_multiuser(conn: sqlite3.Connection) -> None:
    """
    Migrates the old single-user people table to the multi-user schema.

    Existing people are assigned to the oldest InTouch user,
    which for our current database is user ID 1.
    """

    # Does the people table already exist?
    people_exists = conn.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table'
          AND name = 'people';
        """
    ).fetchone()

    if not people_exists:
        return

    # Check whether user_id already exists.
    columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(people);").fetchall()
    }

    if "user_id" in columns:
        # Already migrated.
        return

    # Find the original/oldest InTouch user.
    legacy_owner = conn.execute(
        """
        SELECT id
        FROM users
        ORDER BY id
        LIMIT 1;
        """
    ).fetchone()

    if legacy_owner is None:
        raise RuntimeError(
            "Cannot migrate existing people because no InTouch user exists."
        )

    legacy_user_id = legacy_owner["id"]

    # Remove the old global uniqueness rule.
    conn.execute("DROP INDEX IF EXISTS ux_people_rel_name;")

    # In case a previous migration attempt failed halfway through.
    conn.execute("DROP TABLE IF EXISTS people_new;")

    # Create the new multi-user table.
    conn.execute(
        """
        CREATE TABLE people_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            name TEXT NOT NULL,

            relationship TEXT NOT NULL
                CHECK (relationship IN ('Friend', 'Family')),

            drawn INTEGER NOT NULL DEFAULT 0
                CHECK (drawn IN (0, 1)),

            created_at TEXT NOT NULL DEFAULT (datetime('now')),

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );
        """
    )

    # Copy all existing people and assign them to the original user.
    conn.execute(
        """
        INSERT INTO people_new (
            id,
            user_id,
            name,
            relationship,
            drawn,
            created_at
        )
        SELECT
            id,
            ?,
            name,
            relationship,
            drawn,
            created_at
        FROM people;
        """,
        (legacy_user_id,),
    )

    # Replace the old table with the new one.
    conn.execute("DROP TABLE people;")
    conn.execute("ALTER TABLE people_new RENAME TO people;")

    # Names only need to be unique within a user's own relationship list.
    conn.execute(
        """
        CREATE UNIQUE INDEX ux_people_user_rel_name
        ON people(user_id, relationship, name);
        """
    )


def init_db() -> None:
    with _connect() as conn:

        # -------------------------
        # Users
        # -------------------------

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                auth_provider TEXT NOT NULL,
                auth_subject TEXT NOT NULL,
                email TEXT NOT NULL,
                display_name TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                UNIQUE (auth_provider, auth_subject)
            );
            """
        )


        # -------------------------
        # People
        # -------------------------

        people_exists = conn.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'people';
            """
        ).fetchone()

        if people_exists:
            _migrate_people_to_multiuser(conn)

        else:
            conn.execute(
                """
                CREATE TABLE people (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    user_id INTEGER NOT NULL,

                    name TEXT NOT NULL,

                    relationship TEXT NOT NULL
                        CHECK (relationship IN ('Friend', 'Family')),

                    drawn INTEGER NOT NULL DEFAULT 0
                        CHECK (drawn IN (0, 1)),

                    created_at TEXT NOT NULL DEFAULT (datetime('now')),

                    FOREIGN KEY (user_id)
                        REFERENCES users(id)
                        ON DELETE CASCADE
                );
                """
            )


        # Remove old single-user index if it somehow still exists.
        conn.execute(
            "DROP INDEX IF EXISTS ux_people_rel_name;"
        )

        # Multi-user uniqueness rule.
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_people_user_rel_name
            ON people(user_id, relationship, name);
            """
        )


        # -------------------------
        # Meta
        # -------------------------

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            """
        )


def get_people_df(user_id: int) -> pd.DataFrame:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT
                id,
                name,
                relationship,
                drawn
            FROM people
            WHERE user_id = ?
            ORDER BY relationship, name;
            """,
            (user_id,),
        ).fetchall()

    return pd.DataFrame([dict(r) for r in rows])


def get_counts(user_id: int) -> dict:
    with _connect() as conn:
        out = {}

        for rel in ("Friend", "Family"):
            total = conn.execute(
                """
                SELECT COUNT(*) AS n
                FROM people
                WHERE user_id = ?
                  AND relationship = ?;
                """,
                (user_id, rel),
            ).fetchone()["n"]

            remaining = conn.execute(
                """
                SELECT COUNT(*) AS n
                FROM people
                WHERE user_id = ?
                  AND relationship = ?
                  AND drawn = 0;
                """,
                (user_id, rel),
            ).fetchone()["n"]

            out[rel] = {
                "total": total,
                "remaining": remaining,
            }

    return out


def _get_meta(
    user_id: int,
    key: str,
) -> str:
    user_key = f"user:{user_id}:{key}"

    with _connect() as conn:
        row = conn.execute(
            """
            SELECT value
            FROM meta
            WHERE key = ?;
            """,
            (user_key,),
        ).fetchone()

    return (row["value"] if row else "") or ""


def _set_meta(
    user_id: int,
    key: str,
    value: str,
) -> None:
    user_key = f"user:{user_id}:{key}"

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO meta (
                key,
                value
            )
            VALUES (?, ?)

            ON CONFLICT(key)
            DO UPDATE SET
                value = excluded.value;
            """,
            (
                user_key,
                value,
            ),
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

def get_or_create_user(
    auth_provider: str,
    auth_subject: str,
    email: str,
    display_name: str | None = None,
) -> User:

    with _connect() as conn:
        row = conn.execute(
            """
            SELECT
                id,
                auth_provider,
                auth_subject,
                email,
                display_name
            FROM users
            WHERE auth_provider = ?
              AND auth_subject = ?;
            """,
            (auth_provider, auth_subject),
        ).fetchone()

        if row is None:
            cursor = conn.execute(
                """
                INSERT INTO users (
                    auth_provider,
                    auth_subject,
                    email,
                    display_name
                )
                VALUES (?, ?, ?, ?);
                """,
                (
                    auth_provider,
                    auth_subject,
                    email,
                    display_name,
                ),
            )

            user_id = cursor.lastrowid

        else:
            user_id = row["id"]

            # Keep profile information current
            conn.execute(
                """
                UPDATE users
                SET email = ?,
                    display_name = ?
                WHERE id = ?;
                """,
                (
                    email,
                    display_name,
                    user_id,
                ),
            )

        row = conn.execute(
            """
            SELECT
                id,
                auth_provider,
                auth_subject,
                email,
                display_name
            FROM users
            WHERE id = ?;
            """,
            (user_id,),
        ).fetchone()

    return User(
        id=row["id"],
        auth_provider=row["auth_provider"],
        auth_subject=row["auth_subject"],
        email=row["email"],
        display_name=row["display_name"],
    )

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


def upsert_people(
    user_id: int,
    df: pd.DataFrame,
) -> None:
    """
    Save edits for one user's people.

    Expected columns:
        id, name, relationship, drawn

    Only records belonging to user_id can be
    inserted, updated, or deleted.
    """

    df = df.copy()

    # Basic cleanup
    df["name"] = df["name"].astype(str).str.strip()
    df = df[df["name"] != ""]

    # Validate relationships
    invalid_relationships = df[
        ~df["relationship"].isin(["Friend", "Family"])
    ]

    if not invalid_relationships.empty:
        raise ValueError(
            "Relationship must be Friend or Family."
        )

    try:
        with _connect() as conn:

            # Get ONLY this user's existing records
            existing_ids = {
                row["id"]
                for row in conn.execute(
                    """
                    SELECT id
                    FROM people
                    WHERE user_id = ?;
                    """,
                    (user_id,),
                ).fetchall()
            }

            # IDs coming back from the editor
            incoming_ids = {
                int(x)
                for x in df["id"].dropna().astype(int).tolist()
            }

            # Delete records removed from this user's dataset
            to_delete = sorted(existing_ids - incoming_ids)

            if to_delete:
                conn.executemany(
                    """
                    DELETE FROM people
                    WHERE id = ?
                      AND user_id = ?;
                    """,
                    [
                        (person_id, user_id)
                        for person_id in to_delete
                    ],
                )

            # Insert/update remaining records
            for _, row in df.iterrows():

                rid = (
                    int(row["id"])
                    if pd.notna(row["id"])
                    else None
                )

                name = str(row["name"]).strip()
                relationship = row["relationship"]

                drawn = (
                    int(row["drawn"])
                    if "drawn" in row
                    and pd.notna(row["drawn"])
                    else 0
                )

                # -------------------------
                # New person
                # -------------------------
                if rid is None or rid == 0:

                    conn.execute(
                        """
                        INSERT INTO people (
                            user_id,
                            name,
                            relationship,
                            drawn
                        )
                        VALUES (?, ?, ?, ?);
                        """,
                        (
                            user_id,
                            name,
                            relationship,
                            drawn,
                        ),
                    )

                # -------------------------
                # Existing person
                # -------------------------
                else:

                    conn.execute(
                        """
                        UPDATE people
                        SET
                            name = ?,
                            relationship = ?,
                            drawn = ?
                        WHERE id = ?
                          AND user_id = ?;
                        """,
                        (
                            name,
                            relationship,
                            drawn,
                            rid,
                            user_id,
                        ),
                    )

    except sqlite3.IntegrityError as e:
        raise ValueError(
            "A person with that name already exists "
            "in that relationship list."
        ) from e


def add_person(
    user_id: int,
    name: str,
    relationship: Relationship,
) -> None:

    name = name.strip()

    if not name:
        raise ValueError("Name cannot be empty.")

    if relationship not in ("Friend", "Family"):
        raise ValueError("Relationship must be Friend or Family.")

    try:
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO people (
                    user_id,
                    name,
                    relationship
                )
                VALUES (?, ?, ?);
                """,
                (
                    user_id,
                    name,
                    relationship,
                ),
            )

    except sqlite3.IntegrityError:
        raise ValueError(
            f"{name} already exists in your {relationship} list."
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

def reset_drawn(
    user_id: int,
    relationship: str | None = None,
) -> None:
    """
    relationship:
        "Friend", "Family", or None for all

    Sets drawn = 0 only for the selected user's records.
    """

    with _connect() as conn:

        if relationship in ("Friend", "Family"):
            conn.execute(
                """
                UPDATE people
                SET drawn = 0
                WHERE user_id = ?
                  AND relationship = ?;
                """,
                (
                    user_id,
                    relationship,
                ),
            )

        else:
            conn.execute(
                """
                UPDATE people
                SET drawn = 0
                WHERE user_id = ?;
                """,
                (user_id,),
            )


def reset_prev(
    user_id: int,
    relationship: str | None = None,
) -> None:

    if relationship == "Friend":
        _set_meta(
            user_id,
            "prev_friend",
            "",
        )

    elif relationship == "Family":
        _set_meta(
            user_id,
            "prev_family",
            "",
        )

    else:
        _set_meta(
            user_id,
            "prev_friend",
            "",
        )

        _set_meta(
            user_id,
            "prev_family",
            "",
        )
