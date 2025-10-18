# Viewer Improvements — Narrative and Plan

## Context
Today’s viewer makes reading and scanning documents harder than it should be. Markdown lacks typographic structure and visual rhythm, and Python files are rendered as plain code without an index of what matters. The result: it’s slower to find headings in Markdown and slower to navigate classes and functions in Python.

## Vision
Make the right‑side viewer feel like a purpose‑built reader for docs and code. For Markdown, it should read like a clean document with clear hierarchy and pleasant spacing. For Python, it should behave like a mini “symbol explorer” that lets you skim structure, see docstrings, and jump around quickly — all with the keyboard.

## Experience Goals
- Fast scanning: key structure is visually obvious at a glance.
- Keyboard‑first: Up/Down to move, Left/Right to expand or switch context, Enter to open.
- Readable typography: good contrast, spacing, and code rendering in dark mode.
- Zero surprises: large files still load responsively; no UI stalls.

## Reader Modes

### Markdown (.md)
Render Markdown with clear typographic hierarchy and lightweight styling — no heavy HTML engine required.
- Headings: distinct sizes/weights with generous spacing; automatic anchor markers optional.
- Lists and quotes: indentation, bullets, and quote bars that are visually distinct.
- Code blocks: monospaced, shaded background, preserved indentation, optional language label.
- Inline emphasis: bold/italic/inline code styled clearly, with good contrast.
- Tables and links: simple alignment and hover style where possible.
- Dark‑mode friendly: consistent colors, line height, and margins to reduce eye strain.

### Python (.py)
Show an outline of symbols so the file is explorable like a table of contents.
- Structure: modules → classes → methods; plus top‑level functions and constants.
- Docstrings: show the first line as a summary; expand for the full docstring.
- Navigation: Up/Down moves between items; Left/Right collapses/expands; Enter opens selected code.
- Split view (optional): outline on the left, selected symbol’s code on the right with syntax highlighting.

## Interaction Model
- Up/Down: move between sections (Markdown) or symbols (Python).
- Left/Right: switch content vs comments (Markdown) or collapse/expand in outline (Python).
- Cmd+= / Cmd+‑: adjust font size.
- Cmd+C: quickly copy the current section/symbol block (content + metadata) when available.

## Technical Approach

### Markdown rendering
Use the existing Text widget and add a lightweight renderer that translates Markdown into styled segments and tags (no heavy external engine).
- Recognize headings (#..######), lists (-, *, 1.), fenced code (```), blockquotes (>), basic tables, and inline styles.
- Apply tags for fonts, spacing, and colors; tune line spacing before/after headings and paragraphs.
- Preserve fenced code blocks verbatim, with monospaced font and shaded background.

### Python outline
Use Python’s `ast` module to parse classes, methods, functions, and constants.
- Build a hierarchical model and bind it to a `ttk.Treeview` inside the right pane.
- Compute docstring summaries (first line) and show them inline; expand on demand.
- Selecting a symbol populates a detail panel with the docstring and a syntax‑highlighted code snippet.
- Cache parsed outlines per file with invalidation on modification time to keep it snappy.

## Performance & Risks
- Tkinter Text can lag with too many tags on very large files; keep styles minimal and batch inserts.
- Syntax highlighting will be basic at first; use regex‑based rules for Python keywords/strings/comments.
- Outline first, code later: for large Python files, render the outline immediately and lazy‑load code details.

## Milestones
1) Markdown readability pass: headings, lists, code, quotes, links; font‑size control.
2) Python AST outline: navigation and docstring previews; Enter opens code.
3) Enhancements: Markdown TOC, Python outline search/filter, basic syntax highlighting.

## Acceptance Criteria
- A sample README.md renders with obvious hierarchy, spacing, and distinct code blocks.
- A sample Python file displays an outline of classes/methods/functions; Up/Down navigates, Left/Right expands/collapses; Enter opens code, with docstrings visible.
- Opening a ~2k‑line Python file keeps UI responsive; outline renders quickly.

## Open Questions
- Should Markdown support embedded images and footnotes in the first pass?
- Do we want a persistent TOC pane for Markdown, or an on‑demand popup?
- For Python, should we include call signatures in the outline or only on selection?

## Future Ideas
- Toggle between “Reader” (docstring‑first) and “Code” (code‑first) modes for Python.
- Quick command palette (Cmd+P) to jump to headings (Markdown) or symbols (Python).
- Status bar hints that adapt to the current mode and selection.
