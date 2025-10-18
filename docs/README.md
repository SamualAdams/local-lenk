# Lenk Viewer — How to Run

This project is organized in a Django‑like layout. The GUI viewer lives in the `viewer` app and is launched via a top‑level `manage.py`.

## Prerequisites
- Python 3.10+ with Tkinter available (macOS/Linux typically include it)
- macOS optional: `say` command for text‑to‑speech (used for comment narration)

## Setup
```bash
# From the project root
python3 -m venv .venv
. .venv/bin/activate

# Optional but recommended for TLS trust in OpenAI calls
pip install -U pip certifi
```

## Run the app
Choose one of the following from the project root:
```bash
python manage.py          # Preferred (Django-like)
# or
python -m lenk            # Uses package entrypoint
```

## Optional: AI (@chat) in comments
- In the app, open Settings and set your OpenAI API key.
- Then you can add a comment starting with `@chat <your question>` on a markdown cell to get an AI response saved alongside your comments.

## Data persistence
- SQLite DB path: `~/.file_viewer_stars.db`
  - Stores starred items, comments, settings, and last session state.

## Troubleshooting
- If your IDE tries to use a different interpreter, point it to `.venv/bin/python` and set the working directory to the project root.
- If `python -m lenk` fails, ensure you’re in the project root and the virtual environment is activated.

## Project layout (overview)
```
lenk/
├── manage.py                # Project entry (run this)
├── lenk/
│   ├── __init__.py
│   ├── __main__.py          # Supports `python -m lenk`
│   └── apps/
│       └── viewer/
│           ├── app.py       # GUI + main()
│           ├── comments.py  # Narration and clipboard helpers
│           ├── database.py  # SQLite storage
│           └── navigation.py# Tree state persistence
└── docs/
    └── README.md            # This file
```
