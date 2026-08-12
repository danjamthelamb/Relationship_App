####################
# Database Functions (db.py)
####################
from __future__ import annotations

import random
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal

import pandas as pd


Relationship = Literal["Friend", "Family"]


@dataclass(frozen=True)
class User:
    id: int
    auth_provider: str
    auth_subject: str
    email: str
    display_name: str | None


@dataclass
class DrawResult:
    friend: str
    family: str


DB_PATH = Path("data") / "texter.sqlite"


# -------------------------------------------------
# CONNECTION
# -------------------------------------------------

def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # SQLite requires this on each connection
    # for foreign keys to actually be enforced.
    conn.execute("PRAGMA foreign_keys = ON;")

    return conn


# -------------------------------------------------
# MIGRATIONS
# -------------------------------------------------

def _migrate_people_to_multiuser(
    conn: sqlite3.Connection,
) -> None:
    """
    Migrate the original single-user people table
    to the multi-user schema.

    Existing people are assigned to the oldest
    InTouch user.
    """

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

    columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(people);"
        ).fetchall()
    }

    # Already migrated.
    if "user_id" in columns:
        return

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
            "Cannot migrate existing people because "
            "no InTouch user exists."
        )

    legacy_user_id = legacy_owner["id"]

    # Remove old global uniqueness rule.
    conn.execute(
        "DROP INDEX IF EXISTS ux_people_rel_name;"
    )

    # Clean up any failed prior attempt.
    conn.execute(
        "DROP TABLE IF EXISTS people_new;"
    )

    # Create new multi-user structure.
    conn.execute(
        """
        CREATE TABLE people_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            name TEXT NOT NULL,

            relationship TEXT NOT NULL
                CHECK (
                    relationship IN ('Friend', 'Family')
                ),

            drawn INTEGER NOT NULL DEFAULT 0
                CHECK (
                    drawn IN (0, 1)
                ),

            last_drawn_date TEXT,

            created_at TEXT NOT NULL
                DEFAULT (datetime('now')),

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );
        """
    )

    # Preserve last_drawn_date if an older DB
    # somehow already contains it.
    if "last_drawn_date" in columns:

        conn.execute(
            """
            INSERT INTO people_new (
                id,
                user_id,
                name,
                relationship,
                drawn,
                last_drawn_date,
                created_at
            )
            SELECT
                id,
                ?,
                name,
                relationship,
                drawn,
                last_drawn_date,
                created_at
            FROM people;
            """,
            (legacy_user_id,),
        )

    else:

        conn.execute(
            """
            INSERT INTO people_new (
                id,
                user_id,
                name,
                relationship,
                drawn,
                last_drawn_date,
                created_at
            )
            SELECT
                id,
                ?,
                name,
                relationship,
                drawn,
                NULL,
                created_at
            FROM people;
            """,
            (legacy_user_id,),
        )

    # Replace old table.
    conn.execute(
        "DROP TABLE people;"
    )

    conn.execute(
        "ALTER TABLE people_new RENAME TO people;"
    )

    # Names only need to be unique within
    # one user's relationship list.
    conn.execute(
        """
        CREATE UNIQUE INDEX ux_people_user_rel_name
        ON people(
            user_id,
            relationship,
            name
        );
        """
    )


def _migrate_add_last_drawn_date(
    conn: sqlite3.Connection,
) -> None:
    """
    Add last_drawn_date to an existing multi-user
    people table if it does not already exist.
    """

    columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(people);"
        ).fetchall()
    }

    if "last_drawn_date" in columns:
        return

    conn.execute(
        """
        ALTER TABLE people
        ADD COLUMN last_drawn_date TEXT;
        """
    )


# -------------------------------------------------
# DATABASE INITIALIZATION
# -------------------------------------------------

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

                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                UNIQUE (
                    auth_provider,
                    auth_subject
                )
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
                        CHECK (
                            relationship IN (
                                'Friend',
                                'Family'
                            )
                        ),

                    drawn INTEGER NOT NULL DEFAULT 0
                        CHECK (
                            drawn IN (0, 1)
                        ),

                    last_drawn_date TEXT,

                    created_at TEXT NOT NULL
                        DEFAULT (datetime('now')),

                    FOREIGN KEY (user_id)
                        REFERENCES users(id)
                        ON DELETE CASCADE
                );
                """
            )


        # Existing multi-user DBs may not have
        # last_drawn_date yet.
        _migrate_add_last_drawn_date(conn)


        # Remove old single-user index if present.
        conn.execute(
            "DROP INDEX IF EXISTS ux_people_rel_name;"
        )


        # Multi-user uniqueness rule.
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                ux_people_user_rel_name

            ON people(
                user_id,
                relationship,
                name
            );
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

        # -------------------------
        # Daily Draws
        # -------------------------

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_draws (
                user_id INTEGER NOT NULL,
                draw_date TEXT NOT NULL,
                friend_name TEXT NOT NULL,
                family_name TEXT NOT NULL,

                PRIMARY KEY (
                    user_id,
                    draw_date
                ),

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            );
            """
        )


# -------------------------------------------------
# USERS
# -------------------------------------------------

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
            (
                auth_provider,
                auth_subject,
            ),
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

            # Keep Google profile info current.
            conn.execute(
                """
                UPDATE users

                SET
                    email = ?,
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


# -------------------------------------------------
# PEOPLE
# -------------------------------------------------

def get_people_df(
    user_id: int,
) -> pd.DataFrame:

    with _connect() as conn:

        rows = conn.execute(
            """
            SELECT
                id,
                name,
                relationship,
                drawn,
                last_drawn_date

            FROM people

            WHERE user_id = ?

            ORDER BY
                relationship,
                name;
            """,
            (user_id,),
        ).fetchall()


    return pd.DataFrame(
        [dict(row) for row in rows]
    )


def get_counts(
    user_id: int,
) -> dict:

    with _connect() as conn:

        out = {}

        for relationship in (
            "Friend",
            "Family",
        ):

            total = conn.execute(
                """
                SELECT COUNT(*) AS n

                FROM people

                WHERE user_id = ?
                  AND relationship = ?;
                """,
                (
                    user_id,
                    relationship,
                ),
            ).fetchone()["n"]


            remaining = conn.execute(
                """
                SELECT COUNT(*) AS n

                FROM people

                WHERE user_id = ?
                  AND relationship = ?
                  AND drawn = 0;
                """,
                (
                    user_id,
                    relationship,
                ),
            ).fetchone()["n"]


            out[relationship] = {
                "total": total,
                "remaining": remaining,
            }


    return out


def add_person(
    user_id: int,
    name: str,
    relationship: Relationship,
) -> None:

    name = name.strip()

    if not name:
        raise ValueError(
            "Name cannot be empty."
        )

    if relationship not in (
        "Friend",
        "Family",
    ):
        raise ValueError(
            "Relationship must be Friend or Family."
        )


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


    except sqlite3.IntegrityError as e:

        raise ValueError(
            f"{name} already exists in your "
            f"{relationship} list."
        ) from e


def upsert_people(
    user_id: int,
    df: pd.DataFrame,
) -> None:
    """
    Save edits for one user's people.

    Expected columns:
        id
        name
        relationship
        drawn

    last_drawn_date is intentionally NOT updated
    here. It is maintained only by the draw logic.
    """

    df = df.copy()


    # -------------------------
    # Cleanup
    # -------------------------

    df["name"] = (
        df["name"]
        .astype(str)
        .str.strip()
    )

    df = df[
        df["name"] != ""
    ]


    # -------------------------
    # Validation
    # -------------------------

    invalid_relationships = df[
        ~df["relationship"].isin(
            [
                "Friend",
                "Family",
            ]
        )
    ]

    if not invalid_relationships.empty:

        raise ValueError(
            "Relationship must be Friend or Family."
        )


    try:

        with _connect() as conn:

            # Existing records belonging ONLY
            # to this user.
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


            # IDs present in the submitted draft.
            incoming_ids = {
                int(value)

                for value in (
                    df["id"]
                    .dropna()
                    .astype(int)
                    .tolist()
                )
            }


            # -------------------------
            # Deletes
            # -------------------------

            to_delete = sorted(
                existing_ids - incoming_ids
            )

            if to_delete:

                conn.executemany(
                    """
                    DELETE FROM people

                    WHERE id = ?
                      AND user_id = ?;
                    """,
                    [
                        (
                            person_id,
                            user_id,
                        )

                        for person_id
                        in to_delete
                    ],
                )


            # -------------------------
            # Inserts / Updates
            # -------------------------

            for _, row in df.iterrows():

                rid = (
                    int(row["id"])
                    if pd.notna(row["id"])
                    else None
                )

                name = str(
                    row["name"]
                ).strip()

                relationship = row[
                    "relationship"
                ]

                drawn = (
                    int(row["drawn"])

                    if (
                        "drawn" in row
                        and pd.notna(
                            row["drawn"]
                        )
                    )

                    else 0
                )


                # -------------------------
                # Insert
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
                # Update
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


# -------------------------------------------------
# META
# -------------------------------------------------

def _get_meta(
    user_id: int,
    key: str,
) -> str:

    user_key = (
        f"user:{user_id}:{key}"
    )


    with _connect() as conn:

        row = conn.execute(
            """
            SELECT value

            FROM meta

            WHERE key = ?;
            """,
            (user_key,),
        ).fetchone()


    return (
        (row["value"] if row else "")
        or ""
    )


def _set_meta(
    user_id: int,
    key: str,
    value: str,
) -> None:

    user_key = (
        f"user:{user_id}:{key}"
    )


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


# -------------------------------------------------
# DRAWING
# -------------------------------------------------

def reset_if_needed(
    user_id: int,
    relationship: Relationship,
) -> None:
    """
    If every person in one of this user's
    relationship lists has been drawn,
    reset drawn = 0 for that list.

    last_drawn_date is intentionally preserved.
    """

    with _connect() as conn:

        total = conn.execute(
            """
            SELECT COUNT(*) AS n

            FROM people

            WHERE user_id = ?
              AND relationship = ?;
            """,
            (
                user_id,
                relationship,
            ),
        ).fetchone()["n"]


        if total == 0:
            return


        remaining = conn.execute(
            """
            SELECT COUNT(*) AS n

            FROM people

            WHERE user_id = ?
              AND relationship = ?
              AND drawn = 0;
            """,
            (
                user_id,
                relationship,
            ),
        ).fetchone()["n"]


        if remaining == 0:

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


def _pick_random_name(
    user_id: int,
    relationship: Relationship,
) -> str:
    """
    Pick a random undrawn person from this user's
    relationship list.

    Avoid immediately repeating the previous person
    when possible.

    Records today's local calendar date as
    last_drawn_date.
    """

    reset_if_needed(
        user_id,
        relationship,
    )


    prev_key = (
        "prev_friend"
        if relationship == "Friend"
        else "prev_family"
    )


    prev_name = _get_meta(
        user_id,
        prev_key,
    )


    with _connect() as conn:

        rows = conn.execute(
            """
            SELECT
                id,
                name

            FROM people

            WHERE user_id = ?
              AND relationship = ?
              AND drawn = 0;
            """,
            (
                user_id,
                relationship,
            ),
        ).fetchall()


    if not rows:

        raise ValueError(
            f"No people found for "
            f"relationship={relationship}"
        )


    candidates = [
        dict(row)
        for row in rows
    ]


    # Avoid repeating the previous person
    # if another candidate is available.
    if (
        prev_name
        and len(candidates) > 1
    ):

        filtered = [
            candidate

            for candidate in candidates

            if (
                candidate["name"]
                != prev_name
            )
        ]

        if filtered:
            candidates = filtered


    choice = random.choice(
        candidates
    )

    chosen_id = choice["id"]
    chosen_name = choice["name"]


    # Local date only: YYYY-MM-DD
    today = date.today().isoformat()


    with _connect() as conn:

        conn.execute(
            """
            UPDATE people

            SET
                drawn = 1,
                last_drawn_date = ?

            WHERE id = ?
              AND user_id = ?;
            """,
            (
                today,
                chosen_id,
                user_id,
            ),
        )


    _set_meta(
        user_id,
        prev_key,
        chosen_name,
    )


    return chosen_name


def draw_friend_and_family(
    user_id: int,
) -> DrawResult:
    """
    Draw one Friend and one Family member
    for this user.
    """

    friend = _pick_random_name(
        user_id,
        "Friend",
    )

    family = _pick_random_name(
        user_id,
        "Family",
    )


    return DrawResult(
        friend=friend,
        family=family,
    )

def get_or_create_today_draw(
    user_id: int,
) -> DrawResult:
    """
    Return today's draw for this user.

    If today's saved Friend or Family member has since
    been deleted, replace only the missing selection.

    If no draw exists today, create and save one.
    """

    today = date.today().isoformat()

    # -------------------------------------------------
    # CHECK FOR EXISTING DAILY DRAW
    # -------------------------------------------------

    with _connect() as conn:
        row = conn.execute(
            """
            SELECT
                friend_name,
                family_name
            FROM daily_draws
            WHERE user_id = ?
              AND draw_date = ?;
            """,
            (
                user_id,
                today,
            ),
        ).fetchone()


    # -------------------------------------------------
    # NO DRAW EXISTS TODAY
    # -------------------------------------------------

    if row is None:

        result = draw_friend_and_family(
            user_id
        )

        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO daily_draws (
                    user_id,
                    draw_date,
                    friend_name,
                    family_name
                )
                VALUES (?, ?, ?, ?);
                """,
                (
                    user_id,
                    today,
                    result.friend,
                    result.family,
                ),
            )

        return result


    # -------------------------------------------------
    # EXISTING DRAW
    # -------------------------------------------------

    friend_name = row["friend_name"]
    family_name = row["family_name"]


    # Check whether today's selected people
    # still exist in this user's lists.
    with _connect() as conn:

        friend_exists = conn.execute(
            """
            SELECT 1
            FROM people
            WHERE user_id = ?
              AND relationship = 'Friend'
              AND name = ?;
            """,
            (
                user_id,
                friend_name,
            ),
        ).fetchone() is not None


        family_exists = conn.execute(
            """
            SELECT 1
            FROM people
            WHERE user_id = ?
              AND relationship = 'Family'
              AND name = ?;
            """,
            (
                user_id,
                family_name,
            ),
        ).fetchone() is not None


    # -------------------------------------------------
    # REPLACE DELETED FRIEND
    # -------------------------------------------------

    if not friend_exists:

        friend_name = _pick_random_name(
            user_id,
            "Friend",
        )


    # -------------------------------------------------
    # REPLACE DELETED FAMILY MEMBER
    # -------------------------------------------------

    if not family_exists:

        family_name = _pick_random_name(
            user_id,
            "Family",
        )


    # -------------------------------------------------
    # KEEP EXISTING VALID PICKS IN SYNC
    # -------------------------------------------------

    with _connect() as conn:

        if friend_exists:
            conn.execute(
                """
                UPDATE people
                SET
                    drawn = 1,
                    last_drawn_date = ?
                WHERE user_id = ?
                  AND relationship = 'Friend'
                  AND name = ?;
                """,
                (
                    today,
                    user_id,
                    friend_name,
                ),
            )


        if family_exists:
            conn.execute(
                """
                UPDATE people
                SET
                    drawn = 1,
                    last_drawn_date = ?
                WHERE user_id = ?
                  AND relationship = 'Family'
                  AND name = ?;
                """,
                (
                    today,
                    user_id,
                    family_name,
                ),
            )


        # Save any repaired selections back into
        # today's daily_draws record.
        conn.execute(
            """
            UPDATE daily_draws
            SET
                friend_name = ?,
                family_name = ?
            WHERE user_id = ?
              AND draw_date = ?;
            """,
            (
                friend_name,
                family_name,
                user_id,
                today,
            ),
        )


    return DrawResult(
        friend=friend_name,
        family=family_name,
    )


    # -------------------------------------------------
    # NO DRAW EXISTS YET TODAY
    # -------------------------------------------------

    result = draw_friend_and_family(
        user_id
    )


    # -------------------------------------------------
    # SAVE TODAY'S DRAW
    # -------------------------------------------------

    with _connect() as conn:

        conn.execute(
            """
            INSERT INTO daily_draws (
                user_id,
                draw_date,
                friend_name,
                family_name
            )

            VALUES (?, ?, ?, ?);
            """,
            (
                user_id,
                today,
                result.friend,
                result.family,
            ),
        )


    return result


# -------------------------------------------------
# RESETS
# -------------------------------------------------

def reset_drawn(
    user_id: int,
    relationship: str | None = None,
) -> None:
    """
    Reset drawn = 0 for Friend, Family,
    or all of one user's people.

    last_drawn_date is intentionally preserved.
    """

    with _connect() as conn:

        if relationship in (
            "Friend",
            "Family",
        ):

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