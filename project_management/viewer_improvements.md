# Viewer Improvements — Requirements and Ideas

Problem summary
- The right-side viewer is hard to read and scan.
- Markdown is not formatted well enough for fast comprehension.
- Python files render as raw code; hard to navigate.

Goals
- Markdown: render with readable, structured formatting and typographic polish.
- Python: present a simplified, navigable outline of classes, functions, and key symbols with docstrings; allow expanding into code or docstring details; support up/down navigation.

Minimum scope
- Markdown (.md)
  - Headings: clear hierarchy, spacing, and font weight.
  - Lists, code blocks, blockquotes: styled distinctly; monospaced code.
  - Inline formatting: bold/italic/inline code rendered clearly.
  - Link highlighting and basic table alignment.
  - Dark‑mode friendly colors, proper line height and margins.
- Python (.py)
  - Parse an outline of: modules → classes → methods; top‑level functions; constants.
  - Show first line of docstring (summary) inline; expand to full docstring on demand.
  - Keyboard navigation: Up/Down to move, Left/Right to expand/collapse, Enter to open selection in code view.
  - Optional split view: outline on the left, selected symbol’s code on the right with syntax highlighting.

Nice‑to‑have
- Markdown: table of contents pane synced with scroll; footnote rendering; image previews.
- Python: search box filtering symbols; jump to definition within file; copy symbol signature.
- Shared: quick “Copy cell/section” action; adjustable font size; toggle soft wrap.

Implementation approach (high level)
- UI structure
  - Add a viewer mode selector based on file type.
  - For Python, add an Outline panel widget inside the right pane (Treeview) with expand/collapse.
  - For Markdown, continue using Text widget but add tagging for headings, lists, code, quotes, and links; consider a Canvas/HTML hybrid if needed.
- Markdown renderer
  - Create a lightweight Markdown parser/renderer that produces styled segments into the Text widget (no external deps if possible). Recognize: headings (#..######), lists (-, *, 1.), fenced code (```), blockquotes (>), inline `code`, **bold**, _italic_.
  - Apply Text tags with fonts/colors/margins; adjust line spacing for headings and between paragraphs.
- Python outline
  - Use Python’s built‑in `ast` to parse and collect classes, functions, methods, and docstrings.
  - Build a hierarchical model and bind it to a ttk.Treeview.
  - Render docstring summaries; on select, populate the right subpanel with formatted docstring and syntax‑highlighted code snippet.
- Keyboard mappings
  - Up/Down: move selection among outline items or markdown sections.
  - Left/Right: collapse/expand (Python outline), or switch between content/comments.
  - +/- or Cmd+=/Cmd+-: adjust font size.

Risks / considerations
- Tkinter Text is limited for complex layout; excessive tags can slow large files.
- Syntax highlighting in pure Tk may be basic; consider a simple regex‑based highlighter for Python.
- Ensure performance on large .py files (lazy load of code panel, outline first).

Milestones
- M1: Markdown styling pass (headings, lists, code, quotes, links) and font size control.
- M2: Python AST outline with navigation and docstring previews; selection opens code.
- M3: TOC for Markdown + search/filter for Python outline; basic syntax highlighting.

Acceptance criteria
- A sample README.md renders with clear hierarchy, spacing, distinct code blocks.
- A sample Python file shows an outline of classes/methods/functions with docstrings; Up/Down navigates items, Left/Right expands/collapses; Enter opens code.
- No UI freezes when loading medium (~2k lines) Python files.

Notes / Ideas
- Consider caching AST outlines per file path and invalidating on file modification time.
- Allow toggling between “Reader” and “Code” view for Python (doc‑first vs code‑first).
- Add a status bar hint when outline/navigation shortcuts are active.
