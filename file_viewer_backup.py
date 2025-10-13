#!/usr/bin/env python3
"""
Simple File Viewer - A minimal dark-themed file browser for viewing markdown files
"""
import os
import sqlite3
import tkinter as tk
from tkinter import ttk
from pathlib import Path


class FileViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("File Viewer")
        self.root.geometry("1200x800")

        # Dark theme colors
        self.bg_color = "#1e1e1e"
        self.fg_color = "#d4d4d4"
        self.select_color = "#264f78"
        self.border_color = "#3e3e3e"
        self.button_color = "#ffffff"
        self.button_text_color = "#000000"
        self.button_active_color = "#e0e0e0"

        # Markdown filter state
        self.markdown_only = tk.BooleanVar(value=False)

        # Initialize database
        self.init_database()

        # Configure root
        self.root.configure(bg=self.bg_color)

        # Create main container
        main_container = tk.PanedWindow(
            root,
            orient=tk.HORIZONTAL,
            bg=self.bg_color,
            sashwidth=5,
            sashrelief=tk.FLAT
        )
        main_container.pack(fill=tk.BOTH, expand=True)

        # Left pane - File tree with toolbar
        left_frame = tk.Frame(main_container, bg=self.bg_color)
        main_container.add(left_frame, width=300)

        # Toolbar at top of left pane
        toolbar = tk.Frame(left_frame, bg=self.bg_color, pady=5)
        toolbar.pack(fill=tk.X, padx=5)

        # Path entry for navigation
        path_frame = tk.Frame(toolbar, bg=self.bg_color)
        path_frame.pack(fill=tk.X, pady=(0, 5))

        tk.Label(path_frame, text="Path:", bg=self.bg_color, fg=self.fg_color, font=('Consolas', 10)).pack(side=tk.LEFT, padx=(0, 5))

        self.path_entry = tk.Entry(
            path_frame,
            bg=self.border_color,
            fg=self.fg_color,
            insertbackground=self.fg_color,
            font=('Consolas', 10),
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=self.border_color,
            highlightcolor=self.select_color
        )
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.path_entry.insert(0, os.path.expanduser("~"))
        self.path_entry.bind('<Return>', self.navigate_to_path)

        nav_button = tk.Button(
            path_frame,
            text="Go",
            bg=self.button_color,
            fg=self.button_text_color,
            activebackground=self.button_active_color,
            activeforeground=self.button_text_color,
            font=('Consolas', 10, 'bold'),
            relief=tk.RAISED,
            padx=15,
            pady=2,
            cursor='hand2',
            borderwidth=1,
            highlightthickness=0,
            command=lambda: self.navigate_to_path(None)
        )
        nav_button.pack(side=tk.LEFT)

        # Markdown filter toggle
        filter_frame = tk.Frame(toolbar, bg=self.bg_color)
        filter_frame.pack(fill=tk.X)

        self.md_button = tk.Button(
            filter_frame,
            text="Markdown Only",
            bg="#cccccc",
            fg="#000000",
            activebackground="#aaaaaa",
            activeforeground="#000000",
            font=('Consolas', 10),
            relief=tk.RAISED,
            padx=15,
            pady=5,
            cursor='hand2',
            borderwidth=1,
            highlightthickness=0,
            command=self.toggle_markdown_filter
        )
        self.md_button.pack(side=tk.LEFT, padx=(0, 10))

        # Show starred button
        self.starred_button = tk.Button(
            filter_frame,
            text="⭐ Starred",
            bg="#cccccc",
            fg="#000000",
            activebackground="#aaaaaa",
            activeforeground="#000000",
            font=('Consolas', 10),
            relief=tk.RAISED,
            padx=15,
            pady=5,
            cursor='hand2',
            borderwidth=1,
            highlightthickness=0,
            command=self.show_starred
        )
        self.starred_button.pack(side=tk.LEFT)

        # Tree view with scrollbar
        tree_scroll = tk.Scrollbar(left_frame, bg=self.bg_color)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(
            left_frame,
            yscrollcommand=tree_scroll.set,
            selectmode='browse'
        )
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.tree.yview)

        # Style the treeview
        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "Treeview",
            background=self.bg_color,
            foreground=self.fg_color,
            fieldbackground=self.bg_color,
            borderwidth=0
        )
        style.map('Treeview',
                  background=[('selected', self.select_color)],
                  foreground=[('selected', self.fg_color)])
        style.configure("Treeview.Heading",
                       background=self.border_color,
                       foreground=self.fg_color,
                       borderwidth=0)

        # Store current root path
        self.current_root = os.path.expanduser("~")

        # Right pane - File content viewer
        right_frame = tk.Frame(main_container, bg=self.bg_color)
        main_container.add(right_frame)

        # File path label
        self.path_label = tk.Label(
            right_frame,
            text="Select a file to view",
            bg=self.border_color,
            fg=self.fg_color,
            font=('Consolas', 10),
            anchor='w',
            padx=10,
            pady=5
        )
        self.path_label.pack(fill=tk.X)

        # Text widget with scrollbar for file content
        text_frame = tk.Frame(right_frame, bg=self.bg_color)
        text_frame.pack(fill=tk.BOTH, expand=True)

        text_scroll = tk.Scrollbar(text_frame, bg=self.bg_color)
        text_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_widget = tk.Text(
            text_frame,
            bg=self.bg_color,
            fg=self.fg_color,
            insertbackground=self.fg_color,
            selectbackground=self.select_color,
            font=('Consolas', 11),
            wrap=tk.WORD,
            padx=10,
            pady=10,
            yscrollcommand=text_scroll.set
        )
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text_scroll.config(command=self.text_widget.yview)

        # Bind tree selection event
        self.tree.bind('<<TreeviewSelect>>', self.on_file_select)
        self.tree.bind('<Button-2>', self.toggle_star)  # Right-click
        self.tree.bind('<Button-3>', self.toggle_star)  # Right-click (alternative)
        self.tree.bind('<Control-Button-1>', self.toggle_star)  # Ctrl+Click

        # Track view mode
        self.viewing_starred = False

        # Cell navigation for markdown
        self.cells = []  # List of cell content (text)
        self.current_cell = 0
        self.current_file = None
        self.viewing_comments = False

        # Bind arrow keys globally
        self.root.bind('<Up>', self.on_arrow_key)
        self.root.bind('<Down>', self.on_arrow_key)
        self.root.bind('<Left>', self.on_arrow_key)
        self.root.bind('<Right>', self.on_arrow_key)

        # Populate tree with current directory
        self.populate_tree()

    def init_database(self):
        """Initialize SQLite database for starred items and comments"""
        db_path = os.path.expanduser("~/.file_viewer_stars.db")
        self.conn = sqlite3.connect(db_path)
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
                cell_index INTEGER NOT NULL,
                comment_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(file_path, cell_index, comment_text)
            )
        ''')
        self.conn.commit()

    def is_starred(self, path):
        """Check if a path is starred"""
        self.cursor.execute('SELECT 1 FROM starred WHERE path = ?', (path,))
        return self.cursor.fetchone() is not None

    def add_star(self, path):
        """Add a star to a path"""
        try:
            self.cursor.execute('INSERT INTO starred (path) VALUES (?)', (path,))
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass  # Already starred

    def remove_star(self, path):
        """Remove a star from a path"""
        self.cursor.execute('DELETE FROM starred WHERE path = ?', (path,))
        self.conn.commit()

    def get_starred_items(self):
        """Get all starred paths"""
        self.cursor.execute('SELECT path FROM starred ORDER BY starred_at DESC')
        return [row[0] for row in self.cursor.fetchall()]

    def toggle_star(self, event):
        """Toggle star on selected item"""
        item = self.tree.identify_row(event.y)
        if not item:
            return

        values = self.tree.item(item)['values']
        if not values:
            return

        path = values[0]

        if self.is_starred(path):
            self.remove_star(path)
        else:
            self.add_star(path)

        # Update tree display
        self.update_tree_item_display(item, path)

    def update_tree_item_display(self, item, path):
        """Update tree item to show star status"""
        current_text = self.tree.item(item)['text']
        base_name = current_text.replace('⭐ ', '')

        if self.is_starred(path):
            self.tree.item(item, text=f'⭐ {base_name}')
        else:
            self.tree.item(item, text=base_name)

    def show_starred(self):
        """Show only starred items"""
        self.viewing_starred = not self.viewing_starred

        if self.viewing_starred:
            self.starred_button.config(
                bg=self.button_color,
                fg=self.button_text_color,
                font=('Consolas', 10, 'bold')
            )
            self.display_starred_items()
        else:
            self.starred_button.config(
                bg="#cccccc",
                fg="#000000",
                font=('Consolas', 10)
            )
            self.refresh_tree()

    def display_starred_items(self):
        """Display only starred items in tree"""
        self.tree.delete(*self.tree.get_children())
        starred_paths = self.get_starred_items()

        for path in starred_paths:
            if os.path.exists(path):
                name = os.path.basename(path)
                is_dir = os.path.isdir(path)

                node = self.tree.insert(
                    '',
                    'end',
                    text=f'⭐ {name}',
                    values=[path],
                    open=False
                )

                if is_dir:
                    self.tree.insert(node, 'end', text='Loading...')

    def toggle_markdown_filter(self):
        """Toggle markdown-only filter"""
        self.markdown_only.set(not self.markdown_only.get())

        # Update button appearance
        if self.markdown_only.get():
            self.md_button.config(
                bg=self.button_color,
                fg=self.button_text_color,
                text="Markdown Only ✓",
                font=('Consolas', 10, 'bold')
            )
        else:
            self.md_button.config(
                bg="#cccccc",
                fg="#000000",
                text="Markdown Only",
                font=('Consolas', 10)
            )

        # Refresh tree
        self.refresh_tree()

    def navigate_to_path(self, event):
        """Navigate to the path entered in the path entry"""
        path = self.path_entry.get()
        path = os.path.expanduser(path)

        if os.path.isdir(path):
            self.current_root = path
            self.refresh_tree()
        else:
            self.path_label.config(text=f"Error: '{path}' is not a valid directory")

    def refresh_tree(self):
        """Clear and repopulate the tree"""
        self.tree.delete(*self.tree.get_children())
        self.populate_tree(path=self.current_root)

    def populate_tree(self, parent='', path=None):
        """Populate tree view with directory structure"""
        if path is None:
            path = self.current_root

        try:
            items = sorted(os.listdir(path))
        except PermissionError:
            return

        for item in items:
            # Skip hidden files
            if item.startswith('.'):
                continue

            item_path = os.path.join(path, item)

            try:
                is_dir = os.path.isdir(item_path)
                is_markdown = item.endswith('.md')

                # Apply markdown filter
                if self.markdown_only.get():
                    # Only show directories and markdown files
                    if not is_dir and not is_markdown:
                        continue

                # Insert item into tree with star if starred
                display_name = f'⭐ {item}' if self.is_starred(item_path) else item
                node = self.tree.insert(
                    parent,
                    'end',
                    text=display_name,
                    values=[item_path],
                    open=False
                )

                # If directory, add dummy child to show expand arrow
                if is_dir:
                    self.tree.insert(node, 'end', text='Loading...')
                    self.tree.bind('<<TreeviewOpen>>', self.on_folder_open)

            except (PermissionError, OSError):
                continue

    def on_folder_open(self, event):
        """Handle folder expansion"""
        node = self.tree.focus()
        children = self.tree.get_children(node)

        # If dummy child exists, remove it and populate
        if len(children) == 1 and self.tree.item(children[0])['text'] == 'Loading...':
            self.tree.delete(children[0])
            path = self.tree.item(node)['values'][0]
            self.populate_tree(node, path)

    def on_file_select(self, event):
        """Handle file selection"""
        selected = self.tree.selection()
        if not selected:
            return

        item = selected[0]
        values = self.tree.item(item)['values']

        if not values:
            return

        file_path = values[0]

        # Check if it's a file
        if os.path.isfile(file_path):
            self.display_file(file_path)

    def get_comments(self, file_path, cell_index):
        """Get comments for a specific cell"""
        self.cursor.execute(
            'SELECT comment_text, created_at FROM comments WHERE file_path = ? AND cell_index = ? ORDER BY created_at',
            (file_path, cell_index)
        )
        return self.cursor.fetchall()

    def add_comment(self, file_path, cell_index, comment_text):
        """Add a comment to a cell"""
        try:
            self.cursor.execute(
                'INSERT INTO comments (file_path, cell_index, comment_text) VALUES (?, ?, ?)',
                (file_path, cell_index, comment_text)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Duplicate comment

    def delete_comment(self, file_path, cell_index, comment_text):
        """Delete a comment"""
        self.cursor.execute(
            'DELETE FROM comments WHERE file_path = ? AND cell_index = ? AND comment_text = ?',
            (file_path, cell_index, comment_text)
        )
        self.conn.commit()

    def on_arrow_key(self, event):
        """Handle arrow key navigation between cells and comments"""
        if not self.cells or not self.current_file or not self.current_file.endswith('.md'):
            return

        if self.viewing_comments:
            if event.keysym == 'Left':
                self.viewing_comments = False
                self.display_current_cell()
                return 'break'
        else:
            if event.keysym == 'Down':
                self.navigate_to_cell(self.current_cell + 1)
                return 'break'
            elif event.keysym == 'Up':
                self.navigate_to_cell(self.current_cell - 1)
                return 'break'
            elif event.keysym == 'Right':
                self.viewing_comments = True
                self.display_comments()
                return 'break'

    def navigate_to_cell(self, cell_index):
        """Navigate to a specific cell"""
        if not self.cells:
            return

        # Clamp to valid range
        cell_index = max(0, min(cell_index, len(self.cells) - 1))

        if cell_index == self.current_cell:
            return

        # Update current cell
        self.current_cell = cell_index
        self.display_current_cell()

    def display_current_cell(self):
        """Display only the current cell"""
        if not self.cells or self.current_cell >= len(self.cells):
            return

        self.text_widget.delete('1.0', tk.END)

        # Show cell indicator
        total_cells = len(self.cells)
        indicator = f"Cell {self.current_cell + 1} / {total_cells}   [→ Comments] [↑↓ Navigate]\n"
        self.text_widget.insert('1.0', indicator, 'cell_indicator')
        self.text_widget.insert(tk.END, '─' * 80 + '\n\n', 'separator')

        # Show current cell content
        cell_content = self.cells[self.current_cell]
        self.render_markdown_cell(cell_content)

        # Check if there are comments
        comments = self.get_comments(self.current_file, self.current_cell)
        if comments:
            self.text_widget.insert(tk.END, f'\n\n💬 {len(comments)} comment(s) - Press → to view', 'comment_hint')

    def display_comments(self):
        """Display comments for current cell"""
        self.text_widget.delete('1.0', tk.END)

        # Header
        self.text_widget.insert('1.0', f"💬 Comments for Cell {self.current_cell + 1}   [← Back]\n", 'comment_header')
        self.text_widget.insert(tk.END, '─' * 80 + '\n\n', 'separator')

        # Get comments
        comments = self.get_comments(self.current_file, self.current_cell)

        if comments:
            for i, (comment_text, created_at) in enumerate(comments, 1):
                self.text_widget.insert(tk.END, f"Comment {i}:\n", 'comment_number')
                self.text_widget.insert(tk.END, f"{comment_text}\n", 'comment_text')
                self.text_widget.insert(tk.END, f"Posted: {created_at}\n\n", 'comment_date')
        else:
            self.text_widget.insert(tk.END, "No comments yet.\n\n", 'no_comments')

        # Instructions
        self.text_widget.insert(tk.END, "\n" + "─" * 80 + "\n", 'separator')
        self.text_widget.insert(tk.END, "Type below to add a comment (press Enter to save):\n", 'instructions')

        # Comment input
        self.comment_input = tk.Text(
            self.text_widget,
            height=4,
            bg=self.border_color,
            fg=self.fg_color,
            font=('Consolas', 10),
            wrap=tk.WORD
        )
        self.text_widget.window_create(tk.END, window=self.comment_input)
        self.comment_input.bind('<Control-Return>', self.save_comment)
        self.comment_input.focus_set()

    def save_comment(self, event):
        """Save comment from input"""
        comment_text = self.comment_input.get('1.0', tk.END).strip()
        if comment_text:
            self.add_comment(self.current_file, self.current_cell, comment_text)
            self.display_comments()  # Refresh
        return 'break'

    def render_markdown_cell(self, content):
        """Render markdown content for a single cell"""
        import re

        lines = content.split('\n')
        in_code_block = False

        for line in lines:
            if line.startswith('```'):
                in_code_block = not in_code_block
                self.text_widget.insert(tk.END, line + '\n', 'code_block')
                continue

            if in_code_block:
                self.text_widget.insert(tk.END, line + '\n', 'code_block')
                continue

            # Headings
            if line.startswith('# '):
                self.text_widget.insert(tk.END, line + '\n', 'h1')
            elif line.startswith('## '):
                self.text_widget.insert(tk.END, line + '\n', 'h2')
            elif line.startswith('### '):
                self.text_widget.insert(tk.END, line + '\n', 'h3')
            elif line.startswith('#### '):
                self.text_widget.insert(tk.END, line + '\n', 'h4')
            elif line.startswith('##### '):
                self.text_widget.insert(tk.END, line + '\n', 'h5')
            elif line.startswith('###### '):
                self.text_widget.insert(tk.END, line + '\n', 'h6')
            elif line.startswith('>'):
                self.text_widget.insert(tk.END, line + '\n', 'blockquote')
            elif line.strip().startswith(('-', '*', '+')):
                self.text_widget.insert(tk.END, line + '\n', 'list_item')
            elif line.strip() and line.strip()[0].isdigit() and '.' in line[:4]:
                self.text_widget.insert(tk.END, line + '\n', 'list_item')
            else:
                self.text_widget.insert(tk.END, line + '\n')

    def display_file(self, file_path):
        """Display file content in text widget"""
        self.path_label.config(text=file_path)
        self.current_file = file_path
        self.text_widget.delete('1.0', tk.END)
        self.cells = []
        self.current_cell = 0
        self.viewing_comments = False

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # If markdown file, parse into cells and display
            if file_path.endswith('.md'):
                # Configure text tags for markdown elements
                self.text_widget.tag_configure('h1', font=('Consolas', 18, 'bold'), foreground='#569cd6', spacing3=10)
                self.text_widget.tag_configure('h2', font=('Consolas', 16, 'bold'), foreground='#4ec9b0', spacing3=8)
                self.text_widget.tag_configure('h3', font=('Consolas', 14, 'bold'), foreground='#4ec9b0', spacing3=6)
                self.text_widget.tag_configure('h4', font=('Consolas', 12, 'bold'), foreground='#4ec9b0', spacing3=4)
                self.text_widget.tag_configure('h5', font=('Consolas', 11, 'bold'), foreground='#4ec9b0', spacing3=4)
                self.text_widget.tag_configure('h6', font=('Consolas', 11, 'bold'), foreground='#4ec9b0', spacing3=4)
                self.text_widget.tag_configure('code_block', background='#2d2d2d', foreground='#ce9178', font=('Monaco', 10))
                self.text_widget.tag_configure('code_inline', background='#2d2d2d', foreground='#ce9178')
                self.text_widget.tag_configure('bold', font=('Consolas', 11, 'bold'))
                self.text_widget.tag_configure('italic', font=('Consolas', 11, 'italic'))
                self.text_widget.tag_configure('link', foreground='#569cd6', underline=True)
                self.text_widget.tag_configure('list_item', lmargin1=20, lmargin2=40)
                self.text_widget.tag_configure('blockquote', foreground='#6a9955', lmargin1=20, lmargin2=20)
                self.text_widget.tag_configure('cell_indicator', foreground='#888888', font=('Consolas', 10))
                self.text_widget.tag_configure('separator', foreground='#444444')
                self.text_widget.tag_configure('comment_hint', foreground='#ffd700')
                self.text_widget.tag_configure('comment_header', foreground='#ffd700', font=('Consolas', 12, 'bold'))
                self.text_widget.tag_configure('comment_number', foreground='#888888', font=('Consolas', 10, 'bold'))
                self.text_widget.tag_configure('comment_text', foreground='#d4d4d4')
                self.text_widget.tag_configure('comment_date', foreground='#666666', font=('Consolas', 9))
                self.text_widget.tag_configure('no_comments', foreground='#888888', font=('Consolas', 10, 'italic'))
                self.text_widget.tag_configure('instructions', foreground='#888888')

                # Parse content into cells
                self.parse_markdown_cells(content)

                # Display first cell
                if self.cells:
                    self.display_current_cell()

            else:
                self.text_widget.insert('1.0', content)

        except Exception as e:
            self.text_widget.insert('1.0', f"Error reading file:\n{str(e)}")

    def parse_markdown_cells(self, content):
        """Parse markdown content into cells based on headings"""
        lines = content.split('\n')
        current_cell = []

        for line in lines:
            if line.startswith('#') and current_cell:
                # Save previous cell
                self.cells.append('\n'.join(current_cell))
                current_cell = [line]
            else:
                current_cell.append(line)

        # Add last cell
        if current_cell:
            self.cells.append('\n'.join(current_cell))

        # If no headings, treat whole file as one cell
        if not self.cells:
            self.cells = [content]

                for line in lines:
                    start_pos = f'{line_num}.0'

                    # Code blocks
                    if line.startswith('```'):
                        in_code_block = not in_code_block
                        self.text_widget.insert(tk.END, line + '\n', 'code_block')
                        line_num += 1
                        continue

                    if in_code_block:
                        self.text_widget.insert(tk.END, line + '\n', 'code_block')
                        line_num += 1
                        continue

                    # Headings - create new cell on heading
                    if line.startswith('#'):
                        # Save previous cell
                        if cell_start != f'{line_num}.0':
                            cell_end = f'{line_num}.0'
                            self.cells.append((cell_start, cell_end))

                        # Add visual separator
                        if len(self.cells) > 0:
                            self.text_widget.insert(tk.END, '─' * 80 + '\n', 'cell_separator')
                            line_num += 1

                        # Start new cell
                        cell_start = f'{line_num}.0'

                        if line.startswith('# '):
                            self.text_widget.insert(tk.END, line + '\n', 'h1')
                        elif line.startswith('## '):
                            self.text_widget.insert(tk.END, line + '\n', 'h2')
                        elif line.startswith('### '):
                            self.text_widget.insert(tk.END, line + '\n', 'h3')
                        elif line.startswith('#### '):
                            self.text_widget.insert(tk.END, line + '\n', 'h4')
                        elif line.startswith('##### '):
                            self.text_widget.insert(tk.END, line + '\n', 'h5')
                        elif line.startswith('###### '):
                            self.text_widget.insert(tk.END, line + '\n', 'h6')
                    # Blockquotes
                    elif line.startswith('>'):
                        self.text_widget.insert(tk.END, line + '\n', 'blockquote')
                    # List items
                    elif line.strip().startswith(('-', '*', '+')):
                        self.text_widget.insert(tk.END, line + '\n', 'list_item')
                    elif line.strip() and line.strip()[0].isdigit() and '.' in line[:4]:
                        self.text_widget.insert(tk.END, line + '\n', 'list_item')
                    else:
                        # Handle inline formatting
                        self.text_widget.insert(tk.END, line + '\n')

                        # Apply inline code formatting
                        import re
                        for match in re.finditer(r'`([^`]+)`', line):
                            start_col = match.start()
                            end_col = match.end()
                            self.text_widget.tag_add('code_inline', f'{line_num}.{start_col}', f'{line_num}.{end_col}')

                        # Apply bold formatting
                        for match in re.finditer(r'\*\*([^*]+)\*\*|__([^_]+)__', line):
                            start_col = match.start()
                            end_col = match.end()
                            self.text_widget.tag_add('bold', f'{line_num}.{start_col}', f'{line_num}.{end_col}')

                        # Apply italic formatting
                        for match in re.finditer(r'\*([^*]+)\*|_([^_]+)_', line):
                            start_col = match.start()
                            end_col = match.end()
                            self.text_widget.tag_add('italic', f'{line_num}.{start_col}', f'{line_num}.{end_col}')

                        # Apply link formatting
                        for match in re.finditer(r'\[([^\]]+)\]\([^\)]+\)', line):
                            start_col = match.start()
                            end_col = match.end()
                            self.text_widget.tag_add('link', f'{line_num}.{start_col}', f'{line_num}.{end_col}')

                    line_num += 1

                # Add the last cell
                if cell_start != f'{line_num}.0':
                    self.cells.append((cell_start, f'{line_num}.0'))

                # Highlight the first cell
                if self.cells:
                    self.current_cell = 0
                    start, end = self.cells[0]
                    self.text_widget.tag_add('current_cell', start, end)

            else:
                self.text_widget.insert('1.0', content)

        except Exception as e:
            self.text_widget.insert('1.0', f"Error reading file:\n{str(e)}")


def main():
    root = tk.Tk()
    app = FileViewer(root)

    def on_closing():
        app.conn.close()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == '__main__':
    main()
