import sqlite3
import datetime
import re 
import json
import hashlib


class db_helper:

    @staticmethod
    def get_connection(db: str) -> sqlite3.Connection:
        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("pragma busy_timeout = 5000;")
        return conn



    @staticmethod
    def create_tables(db: str):

        print("DEBUG: creating tables")

        # connect to the db
        conn = db_helper.get_connection(db)
        try:
            with conn: 
                # create a cursor object to execute SQL commands
                cursor = conn.cursor()

                # write and execute SQL (Create and insert)
                print("DEBUG: making the books table")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS book (
                        id                 INTEGER PRIMARY KEY,
                        title              TEXT NOT NULL,
                        author             TEXT NOT NULL DEFAULT 'Unknown',
                        normalized_key     TEXT NOT NULL UNIQUE, -- Lowercase "title|author" to merge Kindle & Kobo entries
                        progress_percent   REAL NOT NULL DEFAULT 0.0 CHECK (progress_percent >= 0.0 AND progress_percent <= 100.0),
                        time_spent_seconds INTEGER NOT NULL DEFAULT 0 CHECK (time_spent_seconds >= 0),
                        status             TEXT NOT NULL DEFAULT 'reading' CHECK (status IN ('reading', 'finished', 'unstarted')),
                        extra_meta         TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(extra_meta)),
                        created_at         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
                        updated_at         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
                    ) STRICT;
                """)

                print("DEBUG: making the clippings table")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS clipping (
                        id             INTEGER PRIMARY KEY,
                        book_id        INTEGER NOT NULL REFERENCES book(id) ON DELETE CASCADE,
                        source         TEXT NOT NULL CHECK (source IN ('kindle', 'kobo', 'manual')),
                        clip_type      TEXT NOT NULL CHECK (clip_type IN ('highlight', 'note', 'bookmark')),
                        content        TEXT NOT NULL DEFAULT '',
                        user_note      TEXT NOT NULL DEFAULT '',
                        content_hash   TEXT NOT NULL UNIQUE, -- SHA-256 fingerprint to prevent duplicate imports
                        source_meta    TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(source_meta)),
                        exported_to_md INTEGER NOT NULL DEFAULT 0 CHECK (exported_to_md IN (0, 1)),
                        highlighted_at TEXT NOT NULL,
                        created_at     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))    
                    ) STRICT;
                """)

                print("DEBUG: creating the reading_event table")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS reading_event (
                        id               INTEGER PRIMARY KEY,
                        book_id          INTEGER REFERENCES book(id) ON DELETE SET NULL,
                        device           TEXT NOT NULL,
                        event_type       TEXT NOT NULL CHECK (event_type IN ('heartbeat', 'sync', 'sleep_alert_fired')),
                        progress_percent REAL CHECK (progress_percent IS NULL OR (progress_percent >= 0.0 AND progress_percent <= 100.0)),
                        recorded_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
                    ) STRICT;
                """)

                # set up the app_state table and populate it if not already
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS app_state(
                        key         TEXT PRIMARY KEY,
                        value       TEXT NOT NULL,
                        updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
                    ) STRICT;
                """)

                print("DEBUG: inputing default settings and putting them inside the app_state table")
                cursor.execute("""
                    -- seed default bedtime settings( ignored if already set)
                    INSERT OR IGNORE INTO app_state (key, value) VALUES
                    ('bedtime_curfew', '21:30'),
                    ('sleep_alert_active', 'false'),
                    ('last_sync_at', '');
                """)

        finally:
            conn.close()

    @staticmethod
    def create_indexes(db: str):

        print("DEBUG: making indexes")

        # connect to the database
        conn = db_helper.get_connection(db)

        try:

            with conn:
                # optimize speeds when indexing the database
                conn.executescript("""
                    -- Speeds up fetching all highlights for a specific book
                    CREATE INDEX IF NOT EXISTS idx_clipping_book_id ON clipping(book_id);

                    -- partial index: only indexes unexported highlights so the markdown worker finds new ones in microseconds
                    CREATE INDEX IF NOT EXISTS idx_clipping_unexported ON clipping(exported_to_md) WHERE exported_to_md = 0;

                    -- speed up the bedtime curfew engine when checking recent heartbeats
                    CREATE INDEX IF NOT EXISTS idx_event_recorded_at ON reading_event(recorded_at DESC);

                    -- Speeds up finding the most recently updated book
                    CREATE INDEX IF NOT EXISTS idx_book_updated_at ON book(updated_at DESC)
                """)

        finally:
            conn.close()

    @staticmethod
    def fetch_bookTitle(db: str):
        print("DEBUG: fetching the book title")

        conn = db_helper.get_connection(db)

        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT title FROM book ORDER BY updated_at DESC LIMIT 1;
                """)

                # fetchone returns a single book item
                row = cursor.fetchone()
                return row["title"] if row else "no books yet"
        finally:
            conn.close()
        
    @staticmethod
    def upsert_book(cursor: sqlite3.Cursor, raw_book_title: str, progress: float = 0.0) -> int:
        """
        Splits 'Title (Author)', inserts or updates the book row,
        and forces updated_at to now so it registers as the most recent book.
        """
        raw_book = raw_book_title.strip()
        author_match = re.search(r"\(([^()]+)\)$", raw_book)

        if author_match:
            author = author_match.group(1).strip()
            title = raw_book[:author_match.start()].strip()
        else:
            title = raw_book
            author = "Unknown"

        norm_key = f"{title.lower()}|{author.lower()}"

        cursor.execute("""
            INSERT INTO book (title, author, normalized_key, progress_percent)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(normalized_key) DO UPDATE SET
                progress_percent = MAX(book.progress_percent, excluded.progress_percent),
                updated_at       = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
            RETURNING id;
        """, (title, author, norm_key, progress))

        return cursor.fetchone()["id"]

    @staticmethod
    def insert_clipping(cursor: sqlite3.Cursor, book_id: int, item: dict, source: str = "kindle") -> bool:
        """
        Inserts a single parsed clipping dictionary into the clipping table.
        Returns True if a new row was inserted, or False if it was a duplicate/skipped.
        """
        clip_type = item["type"].lower()
        if clip_type not in ("highlight", "note", "bookmark"):
            return False

        # Build a deterministic SHA-256 hash so re-imports never create duplicates
        raw_sig = f"{book_id}|{clip_type}|{item['content']}|{item['date']}"
        content_hash = hashlib.sha256(raw_sig.encode("utf-8")).hexdigest()

        source_meta = json.dumps({
            "page": item.get("page"),
            "location": item.get("location"),
        })

        cursor.execute("""
            INSERT OR IGNORE INTO clipping (
                book_id, source, clip_type, content,
                content_hash, source_meta, highlighted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (
            book_id,
            source,
            clip_type,
            item["content"],
            content_hash,
            source_meta,
            item["date"],
        ))

        return cursor.rowcount == 1

    @staticmethod
    def insert_reading_event(
        cursor: sqlite3.Cursor,
        device: str,
        event_type: str,
        book_id: int | None = None,
        progress: float | None = None,
    ) -> None:
        """Logs a sync, heartbeat, or sleep_alert_fired event."""
        cursor.execute("""
            INSERT INTO reading_event (book_id, device, event_type, progress_percent)
            VALUES (?, ?, ?, ?);
        """, (book_id, device, event_type, progress))

    @staticmethod
    def import_kindle_batch(db: str, clippings: list[dict]) -> int:
        """
        Master transaction function: takes the full list from kindle.parse_kindle_clippings(),
        upserts books, inserts all new highlights, logs the sync, and updates app_state.
        """
        conn = db_helper.get_connection(db)
        new_count = 0
        last_book_id = None

        try:
            with conn:
                cursor = conn.cursor()

                for item in clippings:
                    book_id = db_helper.upsert_book(cursor, item["book"])
                    last_book_id = book_id

                    if db_helper.insert_clipping(cursor, book_id, item, source="kindle"):
                        new_count += 1

                # Log the sync event and update last_sync_at
                db_helper.insert_reading_event(cursor, device="kindle", event_type="sync", book_id=last_book_id)

                cursor.execute("""
                    UPDATE app_state
                    SET value      = strftime('%Y-%m-%dT%H:%M:%SZ', 'now'),
                        updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
                    WHERE key = 'last_sync_at';
                """)

            return new_count
        finally:
            conn.close()

    @staticmethod
    def touch_book(db: str, book_id: int):
        # manually updates a book's timestamp to bring it to the top
        conn = db_helper.get_connection(db)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE book
                    SET updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
                    WHERE id = ?;
                """, (book_id,))
        finally:
            conn.close()