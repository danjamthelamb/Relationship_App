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


# -------------------------------------------------
# DATA CLASSES
# -------------------------------------------------

@dataclass(frozen=True)
class User:
    id: int
    auth_provider: str
    auth_subject: str
    email: str
    display_name: str | None
    use_friends: bool
    use_family: bool


@dataclass
class DrawResult:
    friend: str | None
    family: str | None


# -------------------------------------------------
# DATABASE PATH
# -------------------------------------------------

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

    conn.execute(
        "PRAGMA foreign_keys = ON;"
    )

    return conn


# =================================================
# MIGRATIONS
# =================================================


# -------------------------------------------------
# OLD SINGLE-USER PEOPLE TABLE
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


    # Already multi-user.
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


    # Clean up failed migration attempts.
    conn.execute(
        "DROP TABLE IF EXISTS people_new;"
    )


    conn.execute(
        """
        CREATE TABLE people_new (
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


    # Preserve last_drawn_date if the old table
    # already happened to contain it.
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


    conn.execute(
        "DROP TABLE people;"
    )

    conn.execute(
        """
        ALTER TABLE people_new
        RENAME TO people;
        """
    )


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


# -------------------------------------------------
# LAST DRAWN DATE
# -------------------------------------------------

def _migrate_add_last_drawn_date(
    conn: sqlite3.Connection,
) -> None:
    """
    Add last_drawn_date to an existing people table
    if it does not already exist.
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
# USER GROUP PREFERENCES
# -------------------------------------------------

def _migrate_user_group_preferences(
    conn: sqlite3.Connection,
) -> None:
    """
    Add Friend/Family preference flags to existing
    users tables.

    Existing users default to both enabled.
    """

    columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(users);"
        ).fetchall()
    }


    if "use_friends" not in columns:

        conn.execute(
            """
            ALTER TABLE users
            ADD COLUMN use_friends
                INTEGER NOT NULL DEFAULT 1
                CHECK (use_friends IN (0, 1));
            """
        )


    if "use_family" not in columns:

        conn.execute(
            """
            ALTER TABLE users
            ADD COLUMN use_family
                INTEGER NOT NULL DEFAULT 1
                CHECK (use_family IN (0, 1));
            """
        )


# -------------------------------------------------
# DAILY DRAWS NULLABLE CATEGORIES
# -------------------------------------------------

def _migrate_daily_draws_nullable(
    conn: sqlite3.Connection,
) -> None:
    """
    Older daily_draws tables required both
    friend_name and family_name.

    Friends-only and Family-only users require those
    fields to be nullable.
    """

    table_exists = conn.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table'
          AND name = 'daily_draws';
        """
    ).fetchone()


    if not table_exists:
        return


    table_info = conn.execute(
        "PRAGMA table_info(daily_draws);"
    ).fetchall()


    columns = {
        row["name"]: row
        for row in table_info
    }


    friend_not_null = (
        "friend_name" in columns
        and columns["friend_name"]["notnull"] == 1
    )

    family_not_null = (
        "family_name" in columns
        and columns["family_name"]["notnull"] == 1
    )


    # Already supports NULL.
    if not friend_not_null and not family_not_null:
        return


    conn.execute(
        "DROP TABLE IF EXISTS daily_draws_new;"
    )


    conn.execute(
        """
        CREATE TABLE daily_draws_new (
            user_id INTEGER NOT NULL,

            draw_date TEXT NOT NULL,

            friend_name TEXT,

            family_name TEXT,

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


    conn.execute(
        """
        INSERT INTO daily_draws_new (
            user_id,
            draw_date,
            friend_name,
            family_name
        )

        SELECT
            user_id,
            draw_date,
            friend_name,
            family_name

        FROM daily_draws;
        """
    )


    conn.execute(
        "DROP TABLE daily_draws;"
    )


    conn.execute(
        """
        ALTER TABLE daily_draws_new
        RENAME TO daily_draws;
        """
    )


# =================================================
# DATABASE INITIALIZATION
# =================================================

def init_db() -> None:

    with _connect() as conn:

        # -----------------------------------------
        # USERS
        # -----------------------------------------

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                auth_provider TEXT NOT NULL,

                auth_subject TEXT NOT NULL,

                email TEXT NOT NULL,

                display_name TEXT,

                use_friends INTEGER NOT NULL DEFAULT 1
                    CHECK (
                        use_friends IN (0, 1)
                    ),

                use_family INTEGER NOT NULL DEFAULT 1
                    CHECK (
                        use_family IN (0, 1)
                    ),

                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                UNIQUE (
                    auth_provider,
                    auth_subject
                )
            );
            """
        )


        # Upgrade existing users table.
        _migrate_user_group_preferences(conn)


        # -----------------------------------------
        # PEOPLE
        # -----------------------------------------

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


        _migrate_add_last_drawn_date(conn)


        # Remove old single-user uniqueness rule.
        conn.execute(
            "DROP INDEX IF EXISTS ux_people_rel_name;"
        )


        # User-specific uniqueness rule.
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


        # -----------------------------------------
        # META
        # -----------------------------------------

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            """
        )


        # -----------------------------------------
        # DAILY DRAWS
        # -----------------------------------------

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_draws (
                user_id INTEGER NOT NULL,

                draw_date TEXT NOT NULL,

                friend_name TEXT,

                family_name TEXT,

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


        _migrate_daily_draws_nullable(conn)


# =================================================
# USERS
# =================================================

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
                display_name,
                use_friends,
                use_family

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


            # Keep Google profile information current.
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
                display_name,
                use_friends,
                use_family

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
        use_friends=bool(row["use_friends"]),
        use_family=bool(row["use_family"]),
    )


def set_user_groups(
    user_id: int,
    use_friends: bool,
    use_family: bool,
) -> None:
    """
    Set which relationship groups participate
    in this user's InTouch experience.

    At least one must remain enabled.
    """

    if not use_friends and not use_family:

        raise ValueError(
            "Choose at least Friends or Family."
        )


    with _connect() as conn:

        conn.execute(
            """
            UPDATE users

            SET
                use_friends = ?,
                use_family = ?

            WHERE id = ?;
            """,
            (
                int(use_friends),
                int(use_family),
                user_id,
            ),
        )


# -------------------------------------------------
# INTERNAL USER PREFERENCE LOOKUP
# -------------------------------------------------

def _get_user_groups(
    user_id: int,
) -> tuple[bool, bool]:

    with _connect() as conn:

        row = conn.execute(
            """
            SELECT
                use_friends,
                use_family

            FROM users

            WHERE id = ?;
            """,
            (user_id,),
        ).fetchone()


    if row is None:

        raise ValueError(
            "InTouch user not found."
        )


    return (
        bool(row["use_friends"]),
        bool(row["use_family"]),
    )


# =================================================
# PEOPLE
# =================================================

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

    last_drawn_date is deliberately maintained
    by the drawing system instead of the editor.
    """

    df = df.copy()


    # -----------------------------------------
    # CLEANUP
    # -----------------------------------------

    df["name"] = (
        df["name"]
        .astype(str)
        .str.strip()
    )


    df = df[
        df["name"] != ""
    ]


    # -----------------------------------------
    # VALIDATION
    # -----------------------------------------

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


            incoming_ids = {
                int(value)

                for value in (
                    df["id"]
                    .dropna()
                    .astype(int)
                    .tolist()
                )
            }


            # ---------------------------------
            # DELETE
            # ---------------------------------

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


            # ---------------------------------
            # INSERT / UPDATE
            # ---------------------------------

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


                # -----------------------------
                # INSERT
                # -----------------------------

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


                # -----------------------------
                # UPDATE
                # -----------------------------

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


# =================================================
# META
# =================================================

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


# =================================================
# DRAWING
# =================================================

def reset_if_needed(
    user_id: int,
    relationship: Relationship,
) -> None:
    """
    If every person in one relationship group has
    already been drawn, begin a new cycle for that
    group only.

    last_drawn_date is preserved.
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
    selected relationship group.

    Avoid immediately repeating the previous person
    when possible.

    Record today's date as last_drawn_date.
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
    Create today's appropriate selection based on
    which groups this user has enabled.

    Examples:

        Friends + Family:
            friend = "Daniel"
            family = "Mom"

        Friends only:
            friend = "Daniel"
            family = None

        Family only:
            friend = None
            family = "Mom"
    """

    use_friends, use_family = (
        _get_user_groups(user_id)
    )


    friend = None
    family = None


    if use_friends:

        friend = _pick_random_name(
            user_id,
            "Friend",
        )


    if use_family:

        family = _pick_random_name(
            user_id,
            "Family",
        )


    return DrawResult(
        friend=friend,
        family=family,
    )


# -------------------------------------------------
# DAILY DRAW
# -------------------------------------------------

def get_or_create_today_draw(
    user_id: int,
) -> DrawResult:
    """
    Return today's saved connections.

    Behavior depends on the user's enabled groups.

    If an existing selected person was deleted,
    replace only that missing selection.

    Disabled groups are stored as NULL.
    """

    today = date.today().isoformat()


    use_friends, use_family = (
        _get_user_groups(user_id)
    )


    # -----------------------------------------
    # FIND TODAY'S SAVED DRAW
    # -----------------------------------------

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


    # -----------------------------------------
    # NO DRAW EXISTS TODAY
    # -----------------------------------------

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


    # -----------------------------------------
    # EXISTING DRAW
    # -----------------------------------------

    friend_name = (
        row["friend_name"]
        if use_friends
        else None
    )


    family_name = (
        row["family_name"]
        if use_family
        else None
    )


    # -----------------------------------------
    # FRIEND
    # -----------------------------------------

    friend_exists = False


    if use_friends and friend_name:

        with _connect() as conn:

            friend_exists = (
                conn.execute(
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
                ).fetchone()
                is not None
            )


    if use_friends:

        if not friend_exists:

            friend_name = _pick_random_name(
                user_id,
                "Friend",
            )

        else:

            with _connect() as conn:

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


    # -----------------------------------------
    # FAMILY
    # -----------------------------------------

    family_exists = False


    if use_family and family_name:

        with _connect() as conn:

            family_exists = (
                conn.execute(
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
                ).fetchone()
                is not None
            )


    if use_family:

        if not family_exists:

            family_name = _pick_random_name(
                user_id,
                "Family",
            )

        else:

            with _connect() as conn:

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


    # -----------------------------------------
    # SAVE REPAIRED / UPDATED DAILY DRAW
    # -----------------------------------------

    with _connect() as conn:

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


# =================================================
# RESET DRAW STATE
# =================================================

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