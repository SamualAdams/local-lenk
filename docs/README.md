# Lenk – Web and Desktop Viewer

This repo contains two UIs for browsing Markdown files, adding comments, and managing favorites:

- Desktop (Tk): original Python/Tkinter app
- Web (HTML/CSS/JS): new app served by a small Flask backend

Both share the same SQLite database in `~/.file_viewer_stars.db` for favorites, comments, and session state.

---

## Quick Start (Web UI)

Prerequisites:
- Python 3.9+
- pip

Steps:

1. Switch to the web branch
   ```bash
   git checkout html-ui
   ```

2. (Optional) Create a virtual environment
   ```bash
   python -m venv .venv
   # macOS/Linux
   source .venv/bin/activate
   # Windows (PowerShell)
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Run the server
   ```bash
   python -m lenk.web_server
   ```
   - The server starts on `http://127.0.0.1:5000` (override with `LENK_WEB_PORT`).
   - Open that URL in your browser.

5. Use the app
   - Enter a path in the left “Path” field and click Go to browse.
   - Click a markdown file to view it; cells are split by `#` headings.
   - Use the comment form to add comments for the current cell.
   - Click the star ☆ next to the file path to toggle favorites.
   - Copy a cell (content + comments) via the “Copy Cell” button.

Notes:
- Export and settings editing in the web UI are placeholders right now.
- The web UI reuses the same SQLite DB as the desktop app; your favorites and comments are shared.

Troubleshooting:
- If `ModuleNotFoundError: No module named 'flask'`, run `pip install -r requirements.txt`.
- If you see permissions errors for the DB, remove or back up `~/.file_viewer_stars.db` and restart.

---

## Quick Start (Desktop/Tk UI)

1. Make sure Python 3.9+ is available
2. Run the Tk app entry point:
   ```bash
   python file_viewer.py
   ```
3. Shortcuts
   - Arrow keys: navigate cells and open comments
   - Cmd+Shift+Down: read next comment (macOS TTS)
   - Cmd+Shift+Up: read previous comment
   - Cmd+Shift+Left: stop comment reading
   - Cmd+E: export annotated file

Note: macOS “say” is used for TTS in the desktop app.

---

## API (Web UI)

The Flask backend exposes:
- `GET /api/settings` – current settings + session
- `POST /api/settings` – update subset of settings (home directory, voice speed)
- `GET /api/tree?path=/abs/path` – directory listing with `is_dir`, `is_markdown`, `starred`
- `GET /api/favorites` – starred paths
- `POST /api/favorites/toggle { path }` – toggle favorite
- `GET /api/file?path=/abs/file.md` – file + parsed cells + comments
- `POST /api/comments { path, cell_index, comment_text }` – add a comment
- `POST /api/session { current_directory, current_file, current_cell }` – persist session

---

## Project Layout

- `file_viewer.py` – desktop entry point
- `lenk/` – shared Python modules
  - `app.py` – Tk app (desktop)
  - `database.py` – SQLite schema + data access
  - `navigation.py` – desktop tree state persistence
  - `comments.py` – desktop comment/narration helpers
  - `service.py` – service layer for the web API
  - `web_server.py` – Flask app serving `web/` and API
- `web/` – HTML/CSS/JS frontend for the web UI
  - `index.html`, `assets/styles.css`, `assets/main.js`
- `requirements.txt` – Flask dependency

---

## Contributing

- Feature parity gaps (web): export annotated file, full settings UI, TTS/comment playback.
- Please open issues or PRs against the `html-ui` branch for web work.

