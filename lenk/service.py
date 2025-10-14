"""Core application service shared by the web interface."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .database import DatabaseMixin


@dataclass
class SessionState:
    current_directory: Optional[str]
    current_file: Optional[str]
    current_cell: int


class LenkService(DatabaseMixin):
    """Provide application data for the web UI."""

    def __init__(self) -> None:
        self.init_database()
        self.load_settings()
        session = self.get_session_state()
        self.current_root: str = session.current_directory or self.home_directory

    # ------------------------------------------------------------------
    # Session helpers
    # ------------------------------------------------------------------
    def get_session_state(self) -> SessionState:
        directory, file_path, cell = self.load_session_state()
        return SessionState(directory, file_path, cell or 0)

    def update_session_state(
        self,
        current_directory: Optional[str] = None,
        current_file: Optional[str] = None,
        current_cell: Optional[int] = None,
    ) -> SessionState:
        session = self.get_session_state()
        directory = current_directory or session.current_directory or self.current_root
        file_path = current_file or session.current_file
        cell = current_cell if current_cell is not None else session.current_cell
        self.current_root = directory or self.home_directory
        self.cursor.execute(
            '''
            INSERT OR REPLACE INTO session_state (id, current_directory, current_file, current_cell, last_updated)
            VALUES (1, ?, ?, ?, CURRENT_TIMESTAMP)
            ''',
            (self.current_root, file_path, cell),
        )
        self.conn.commit()
        return SessionState(self.current_root, file_path, cell)

    # ------------------------------------------------------------------
    # Filesystem helpers
    # ------------------------------------------------------------------
    @staticmethod
    def normalize_path(path: str) -> str:
        return os.path.abspath(os.path.expanduser(path))

    def list_directory(self, path: Optional[str], markdown_only: bool = False) -> dict:
        directory = self.normalize_path(path or self.current_root or self.home_directory)
        entries: List[dict] = []
        try:
            for item in sorted(os.listdir(directory)):
                if item.startswith('.'):
                    continue
                item_path = os.path.join(directory, item)
                is_dir = os.path.isdir(item_path)
                is_markdown = item.lower().endswith('.md')
                if markdown_only and not (is_dir or is_markdown):
                    continue
                entries.append({
                    'name': item,
                    'path': item_path,
                    'is_dir': is_dir,
                    'is_markdown': is_markdown,
                    'starred': self.is_starred(item_path),
                })
        except (FileNotFoundError, PermissionError):
            entries = []
        self.current_root = directory
        return {
            'path': directory,
            'entries': entries,
            'parent': os.path.dirname(directory) if directory != '/' else None,
        }

    def get_favorites(self) -> List[dict]:
        results = []
        for path in self.get_starred_items():
            if not os.path.exists(path):
                continue
            name = os.path.basename(path)
            results.append({
                'name': name,
                'path': path,
                'is_dir': os.path.isdir(path),
            })
        return results

    # ------------------------------------------------------------------
    # Markdown helpers
    # ------------------------------------------------------------------
    def parse_markdown_cells(self, content: str) -> List[str]:
        lines = content.split('\n')
        current_cell: List[str] = []
        cells: List[str] = []

        for line in lines:
            if line.startswith('#') and current_cell:
                cells.append('\n'.join(current_cell))
                current_cell = [line]
            else:
                current_cell.append(line)

        if current_cell:
            cells.append('\n'.join(current_cell))

        if not cells:
            cells = [content]
        return cells

    def get_file_details(self, path: str) -> dict:
        normalized = self.normalize_path(path)
        try:
            with open(normalized, 'r', encoding='utf-8') as handle:
                content = handle.read()
        except (OSError, UnicodeDecodeError) as exc:
            raise FileNotFoundError(str(exc)) from exc

        cells = self.parse_markdown_cells(content)
        cell_payload = []
        for index, cell_content in enumerate(cells):
            comments = self.get_comments(normalized, cell_content, index)
            cell_payload.append({
                'index': index,
                'heading': self.extract_heading(cell_content),
                'text': cell_content,
                'comment_count': len(comments),
                'fuzzy_count': sum(1 for _, _, conf in comments if conf == 'fuzzy'),
                'comments': [
                    {
                        'text': text,
                        'created_at': created_at,
                        'confidence': confidence,
                    }
                    for text, created_at, confidence in comments
                ],
            })
        return {
            'path': normalized,
            'title': Path(normalized).name,
            'content': content,
            'cells': cell_payload,
            'starred': self.is_starred(normalized),
        }

    def add_comment_for_cell(self, path: str, cell_index: int, comment_text: str) -> List[dict]:
        details = self.get_file_details(path)
        if cell_index < 0 or cell_index >= len(details['cells']):
            raise ValueError('Cell index out of range')
        cell_text = details['cells'][cell_index]['text']
        self.add_comment(path, cell_text, cell_index, comment_text)
        # refresh comments
        updated = self.get_comments(path, cell_text, cell_index)
        return [
            {
                'text': text,
                'created_at': created_at,
                'confidence': confidence,
            }
            for text, created_at, confidence in updated
        ]

    # ------------------------------------------------------------------
    # Favorites helpers
    # ------------------------------------------------------------------
    def toggle_star(self, path: str) -> bool:
        normalized = self.normalize_path(path)
        if self.is_starred(normalized):
            self.remove_star(normalized)
            return False
        self.add_star(normalized)
        return True

    # ------------------------------------------------------------------
    # Settings helpers
    # ------------------------------------------------------------------
    def update_settings(self, *, home_directory: Optional[str] = None, voice_speed: Optional[int] = None) -> None:
        if home_directory:
            normalized = self.normalize_path(home_directory)
            if os.path.isdir(normalized):
                self.home_directory = normalized
                self.save_setting('home_directory', normalized)
                self.current_root = normalized
        if voice_speed is not None:
            self.voice_speed = int(voice_speed)
            self.save_setting('voice_speed', self.voice_speed)
