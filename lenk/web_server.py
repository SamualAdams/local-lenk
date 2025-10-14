"""Flask server powering the HTML UI."""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from .service import LenkService

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"

app = Flask(__name__, static_folder=str(WEB_DIR), static_url_path="")
service = LenkService()


@app.get("/")
def index():
    return send_from_directory(WEB_DIR, "index.html")


@app.get("/api/settings")
def get_settings():
    session = service.get_session_state()
    return jsonify(
        {
            "home_directory": service.home_directory,
            "voice_speed": service.voice_speed,
            "current_directory": service.current_root,
            "session": {
                "current_directory": session.current_directory,
                "current_file": session.current_file,
                "current_cell": session.current_cell,
            },
        }
    )


@app.post("/api/settings")
def update_settings():
    data = request.get_json(force=True) or {}
    home_directory = data.get("home_directory")
    voice_speed = data.get("voice_speed")
    service.update_settings(home_directory=home_directory, voice_speed=voice_speed)
    return get_settings()


@app.get("/api/tree")
def list_directory():
    path = request.args.get("path")
    markdown_only = request.args.get("markdown_only") == "true"
    result = service.list_directory(path, markdown_only=markdown_only)
    return jsonify(result)


@app.get("/api/favorites")
def favorites():
    return jsonify(service.get_favorites())


@app.post("/api/favorites/toggle")
def toggle_favorite():
    data = request.get_json(force=True) or {}
    path = data.get("path")
    if not path:
        return jsonify({"error": "Missing path"}), 400
    starred = service.toggle_star(path)
    return jsonify({"starred": starred})


@app.get("/api/file")
def get_file():
    path = request.args.get("path")
    if not path:
        return jsonify({"error": "Missing path"}), 400
    try:
        details = service.get_file_details(path)
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 404
    return jsonify(details)


@app.post("/api/comments")
def add_comment():
    data = request.get_json(force=True) or {}
    path = data.get("path")
    cell_index = data.get("cell_index")
    comment_text = (data.get("comment_text") or "").strip()
    if not path or cell_index is None or not comment_text:
        return jsonify({"error": "path, cell_index, and comment_text are required"}), 400
    try:
        comments = service.add_comment_for_cell(path, int(cell_index), comment_text)
    except (FileNotFoundError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"comments": comments})


@app.post("/api/session")
def update_session():
    data = request.get_json(force=True) or {}
    session = service.update_session_state(
        current_directory=data.get("current_directory"),
        current_file=data.get("current_file"),
        current_cell=data.get("current_cell"),
    )
    return jsonify(
        {
            "current_directory": session.current_directory,
            "current_file": session.current_file,
            "current_cell": session.current_cell,
        }
    )


@app.get("/api/ping")
def ping():
    return jsonify({"status": "ok"})


@app.post("/api/ai/chat")
def ai_chat():
    data = request.get_json(force=True) or {}
    path = data.get("path")
    cell_index = data.get("cell_index")
    question = (data.get("question") or "").strip()
    if not path or cell_index is None or not question:
        return jsonify({"error": "path, cell_index, and question are required"}), 400
    try:
        result = service.ask_ai_and_save(question, path, int(cell_index))
        return jsonify(result)
    except (FileNotFoundError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400


def main() -> None:
    port = int(os.environ.get("LENK_WEB_PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=True)


if __name__ == "__main__":
    main()
