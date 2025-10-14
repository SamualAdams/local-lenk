"""Database mixin for Lenk file viewer."""

import os
import sqlite3
from typing import List, Optional, Tuple


class DatabaseMixin:
    """Encapsulates all database-related helpers for the file viewer."""

    conn: sqlite3.Connection
    cursor: sqlite3.Cursor

    def init_database(self) -> None:
        """Initialize SQLite database for starred items, comments, and settings."""
        db_path = os.path.expanduser("~/.file_viewer_stars.db")
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS starred (
                path TEXT PRIMARY KEY,
                starred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                heading_text TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                cell_index INTEGER,
                comment_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                match_confidence TEXT DEFAULT 'exact'
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                current_directory TEXT,
                current_file TEXT,
                current_cell INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def load_settings(self) -> None:
        """Load top-level settings from the database."""
        self.cursor.execute('SELECT key, value FROM settings')
        settings = dict(self.cursor.fetchall())

        self.home_directory = settings.get('home_directory', os.path.expanduser("~"))
        self.voice_speed = int(settings.get('voice_speed', '200'))
        self.openai_api_key = settings.get('openai_api_key', '')

        self.current_root = self.home_directory

    def save_setting(self, key: str, value: str) -> None:
        """Persist a single setting key/value pair."""
        self.cursor.execute(
            'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
            (key, str(value))
        )
        self.conn.commit()

    def get_setting(self, key: str) -> Optional[str]:
        """Fetch a setting value by key."""
        self.cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        row = self.cursor.fetchone()
        return row[0] if row else None

    def save_session_state(self) -> None:
        """Persist the current browsing session state."""
        self.cursor.execute('''
            INSERT OR REPLACE INTO session_state (id, current_directory, current_file, current_cell, last_updated)
            VALUES (1, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (self.current_root, self.current_file, self.current_cell))
        self.conn.commit()

    def load_session_state(self) -> Tuple[Optional[str], Optional[str], int]:
        """Retrieve the previously persisted session state."""
        self.cursor.execute('SELECT current_directory, current_file, current_cell FROM session_state WHERE id = 1')
        result = self.cursor.fetchone()
        return result if result else (None, None, 0)

    # Starred items -----------------------------------------------------
    def is_starred(self, path: str) -> bool:
        self.cursor.execute('SELECT 1 FROM starred WHERE path = ?', (path,))
        return self.cursor.fetchone() is not None

    def add_star(self, path: str) -> None:
        try:
            self.cursor.execute('INSERT INTO starred (path) VALUES (?)', (path,))
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass

    def remove_star(self, path: str) -> None:
        self.cursor.execute('DELETE FROM starred WHERE path = ?', (path,))
        self.conn.commit()

    def get_starred_items(self) -> List[str]:
        self.cursor.execute('SELECT path FROM starred ORDER BY starred_at DESC')
        return [row[0] for row in self.cursor.fetchall()]

    # Comments ----------------------------------------------------------
    def get_cell_hash(self, content: str) -> str:
        import hashlib

        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def extract_heading(self, cell_content: str) -> str:
        lines = cell_content.strip().split('\n')
        for line in lines:
            if line.startswith('#'):
                return line.strip()
        return "[No Heading]"

    def get_comments(self, file_path: str, cell_content: str, cell_index: int) -> List[Tuple[str, str, str]]:
        heading = self.extract_heading(cell_content)
        content_hash = self.get_cell_hash(cell_content)

        self.cursor.execute(
            '''SELECT id, comment_text, created_at, match_confidence
               FROM comments
               WHERE file_path = ? AND heading_text = ? AND content_hash = ?
               ORDER BY created_at''',
            (file_path, heading, content_hash)
        )
        exact_matches = self.cursor.fetchall()

        if exact_matches:
            for comment_id, *_ in exact_matches:
                self.cursor.execute(
                    'UPDATE comments SET last_matched_at = CURRENT_TIMESTAMP, match_confidence = ? WHERE id = ?',
                    ('exact', comment_id)
                )
            self.conn.commit()
            return [(text, created, conf) for _, text, created, conf in exact_matches]

        self.cursor.execute(
            '''SELECT id, comment_text, created_at, match_confidence
               FROM comments
               WHERE file_path = ? AND heading_text = ?
               ORDER BY created_at''',
            (file_path, heading)
        )
        heading_matches = self.cursor.fetchall()

        if heading_matches:
            for comment_id, *_ in heading_matches:
                self.cursor.execute(
                    'UPDATE comments SET last_matched_at = CURRENT_TIMESTAMP, match_confidence = ? WHERE id = ?',
                    ('fuzzy', comment_id)
                )
            self.conn.commit()
            return [(text, created, 'fuzzy') for _, text, created, _ in heading_matches]

        return []

    def add_comment(self, file_path: str, cell_content: str, cell_index: int, comment_text: str) -> bool:
        heading = self.extract_heading(cell_content)
        content_hash = self.get_cell_hash(cell_content)

        try:
            self.cursor.execute(
                '''INSERT INTO comments
                   (file_path, heading_text, content_hash, cell_index, comment_text, match_confidence)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (file_path, heading, content_hash, cell_index, comment_text, 'exact')
            )
            self.conn.commit()
            return True
        except Exception as exc:  # pylint: disable=broad-except
            print(f"DEBUG: Error inserting comment: {exc}")
            return False
