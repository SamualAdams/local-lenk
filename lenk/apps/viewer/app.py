#!/usr/bin/env python3
"""Tkinter application wiring for the Lenk file viewer."""
import os
import tkinter as tk
from tkinter import ttk, filedialog

from .comments import CommentAudioMixin
from .database import DatabaseMixin
from .navigation import NavigationStateMixin


class FileViewer(DatabaseMixin, NavigationStateMixin, CommentAudioMixin):
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


        # Initialize database
        self.init_database()

        # Load settings
        self.load_settings()

        # Navigation state tracking
        self.tree_state_save_job = None
        self.tree_open_paths = set()
        self.tree_selected_path = None
        self.favorites_open_paths = set()
        self.favorites_selected_path = None
        self.load_navigation_state()

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

        # Left pane - Tabbed navigation
        left_frame = tk.Frame(main_container, bg=self.bg_color)
        main_container.add(left_frame, width=300)

        # Settings expanded state
        self.settings_expanded = False

        # Menu expansion state tracking
        self.expanded_menu_item = None  # Which accordion item is expanded (None, 'directories', 'paste', 'settings')
        self.favorites_open_paths = set()  # Expanded folders in favorites tree
        self.directories_open_paths = set()  # Expanded folders in directories tree

        # Path entry toolbar (shared across all tabs)
        toolbar = tk.Frame(left_frame, bg=self.bg_color)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

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
        self.path_entry.insert(0, self.home_directory)
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

        # Main content frame (holds favorites + accordion menu)
        content_frame = tk.Frame(left_frame, bg=self.bg_color)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        # ========== FAVORITES SECTION (always visible) ==========
        favorites_container = tk.Frame(content_frame, bg=self.bg_color)
        favorites_container.pack(fill=tk.BOTH, expand=True)

        # Favorites header
        favorites_header = tk.Frame(favorites_container, bg=self.border_color)
        favorites_header.pack(fill=tk.X, pady=(0, 2))

        tk.Label(
            favorites_header,
            text="⭐ Favorites",
            bg=self.border_color,
            fg=self.fg_color,
            font=('Consolas', 10, 'bold'),
            anchor='w',
            padx=10,
            pady=5
        ).pack(fill=tk.X)

        # Favorites tree
        favorites_tree_frame = tk.Frame(favorites_container, bg=self.bg_color)
        favorites_tree_frame.pack(fill=tk.BOTH, expand=True)
        self.favorites_tree = ttk.Treeview(favorites_tree_frame, selectmode='browse')
        self.favorites_tree.pack(fill=tk.BOTH, expand=True)

        # ========== ACCORDION MENU (expandable items) ==========
        accordion_container = tk.Frame(content_frame, bg=self.bg_color)
        accordion_container.pack(fill=tk.X, pady=(5, 0))

        # Menu item: Directories
        self.directories_header_frame = tk.Frame(accordion_container, bg=self.border_color, cursor='hand2')
        self.directories_header_frame.pack(fill=tk.X, pady=(0, 2))

        self.directories_header_button = tk.Label(
            self.directories_header_frame,
            text="📁 Directories ▶",
            bg=self.border_color,
            fg=self.fg_color,
            font=('Consolas', 10, 'bold'),
            anchor='w',
            padx=10,
            pady=5,
            cursor='hand2'
        )
        self.directories_header_button.pack(fill=tk.X)
        self.directories_header_button.bind('<Button-1>', lambda e: self.toggle_accordion_item('directories'))
        self.directories_header_frame.bind('<Button-1>', lambda e: self.toggle_accordion_item('directories'))

        self.directories_content_frame = tk.Frame(accordion_container, bg=self.bg_color)
        # Don't pack yet - will show when expanded

        self.tree = ttk.Treeview(self.directories_content_frame, selectmode='browse', height=10)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Menu item: New Paste
        self.paste_header_frame = tk.Frame(accordion_container, bg=self.border_color, cursor='hand2')
        self.paste_header_frame.pack(fill=tk.X, pady=(0, 2))

        self.paste_header_button = tk.Label(
            self.paste_header_frame,
            text="📋 New Paste ▶",
            bg=self.border_color,
            fg=self.fg_color,
            font=('Consolas', 10, 'bold'),
            anchor='w',
            padx=10,
            pady=5,
            cursor='hand2'
        )
        self.paste_header_button.pack(fill=tk.X)
        self.paste_header_button.bind('<Button-1>', lambda e: self.toggle_accordion_item('paste'))
        self.paste_header_frame.bind('<Button-1>', lambda e: self.toggle_accordion_item('paste'))

        self.paste_content_frame = tk.Frame(accordion_container, bg=self.bg_color)
        # Don't pack yet - will show when expanded
        # Content will be populated by show_paste_inline()

        # Menu item: Settings
        self.settings_header_frame = tk.Frame(accordion_container, bg=self.border_color, cursor='hand2')
        self.settings_header_frame.pack(fill=tk.X, pady=(0, 2))

        self.settings_header_button = tk.Label(
            self.settings_header_frame,
            text="⚙️ Settings ▶",
            bg=self.border_color,
            fg=self.fg_color,
            font=('Consolas', 10, 'bold'),
            anchor='w',
            padx=10,
            pady=5,
            cursor='hand2'
        )
        self.settings_header_button.pack(fill=tk.X)
        self.settings_header_button.bind('<Button-1>', lambda e: self.toggle_accordion_item('settings'))
        self.settings_header_frame.bind('<Button-1>', lambda e: self.toggle_accordion_item('settings'))

        self.settings_content_frame = tk.Frame(accordion_container, bg=self.bg_color)
        # Don't pack yet - will show when expanded

        # Bottom controls container (Shortcuts button only)
        self.bottom_controls = tk.Frame(left_frame, bg=self.bg_color)
        self.bottom_controls.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        # Keyboard Shortcuts button
        self.shortcuts_button = tk.Button(
            self.bottom_controls,
            text="⌨️ Shortcuts",
            bg="#cccccc",
            fg="#000000",
            activebackground="#aaaaaa",
            activeforeground="#000000",
            font=('Consolas', 10),
            relief=tk.RAISED,
            pady=8,
            cursor='hand2',
            borderwidth=1,
            highlightthickness=0,
            command=self.show_shortcuts
        )
        self.shortcuts_button.pack(fill=tk.X)

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

        # Configure tag for favorite items - this won't gray out the path,
        # but we can use a dimmer color for the entire row
        # Note: tkinter ttk.Treeview doesn't support styling parts of text in a cell
        # So we'll rely on spacing to de-emphasize the path

        # Right pane - File content viewer
        right_frame = tk.Frame(main_container, bg=self.bg_color)
        main_container.add(right_frame)
        self.right_frame = right_frame

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

        # Text widget without scrollbar for file content (default viewer)
        text_frame = tk.Frame(right_frame, bg=self.bg_color)
        text_frame.pack(fill=tk.BOTH, expand=True)
        self.text_frame = text_frame

        self.text_widget = tk.Text(
            text_frame,
            bg=self.bg_color,
            fg=self.fg_color,
            insertbackground=self.fg_color,
            selectbackground=self.select_color,
            font=('Consolas', 11),
            wrap=tk.WORD,
            padx=10,
            pady=10
        )
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Python outline + code viewer (lazy toggled)
        self.py_frame = tk.PanedWindow(right_frame, orient=tk.HORIZONTAL, bg=self.bg_color, sashwidth=5, sashrelief=tk.FLAT)
        # Left: outline tree
        outline_container = tk.Frame(self.py_frame, bg=self.bg_color)
        self.py_outline = ttk.Treeview(outline_container, selectmode='browse')
        self.py_outline.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.py_frame.add(outline_container, width=280)

        # Right: code/details
        code_container = tk.Frame(self.py_frame, bg=self.bg_color)
        self.py_text = tk.Text(
            code_container,
            bg=self.bg_color,
            fg=self.fg_color,
            insertbackground=self.fg_color,
            selectbackground=self.select_color,
            font=('Consolas', 11),
            wrap=tk.NONE,
            padx=10,
            pady=10
        )
        self.py_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.py_frame.add(code_container)

        # Hide Python view by default; shown for .py files
        self.py_frame.pack_forget()

        # Outline selection handler
        self.py_outline.bind('<<TreeviewSelect>>', self.on_python_symbol_select)

        # Cache for docstrings and nodes
        self._py_outline_cache = {}
        self._py_current_content = None  # Cache Python file content to avoid re-reading

        # Bind tree selection events
        # Directories tab tree (self.tree)
        self.tree.bind('<<TreeviewSelect>>', self.on_file_select)
        self.tree.bind('<Button-2>', self.toggle_star)
        self.tree.bind('<Button-3>', self.toggle_star)
        self.tree.bind('<Control-Button-1>', self.toggle_star)
        self.tree.bind('<<TreeviewOpen>>', self.on_folder_open)
        self.tree.bind('<<TreeviewClose>>', self.on_folder_close)

        # Favorites tab tree
        self.favorites_tree.bind('<<TreeviewSelect>>', self.on_file_select)
        self.favorites_tree.bind('<Button-2>', self.toggle_star)
        self.favorites_tree.bind('<Button-3>', self.toggle_star)
        self.favorites_tree.bind('<Control-Button-1>', self.toggle_star)
        self.favorites_tree.bind('<<TreeviewOpen>>', self.on_folder_open)
        self.favorites_tree.bind('<<TreeviewClose>>', self.on_folder_close)

        # Cell navigation for markdown
        self.cells = []  # List of cell content (text)
        self.current_cell = 0
        self.current_file = None
        self.viewing_comments = False
        self.reading_mode = False
        self.tts_process = None

        # Bind arrow keys globally
        self.root.bind('<Up>', self.on_arrow_key)
        self.root.bind('<Down>', self.on_arrow_key)
        self.root.bind('<Left>', self.on_arrow_key)
        self.root.bind('<Right>', self.on_arrow_key)

        # Bind Command+/ to toggle focus
        self.root.bind('<Command-slash>', self.toggle_focus)

        # Bind Command+E to export annotated version (bind_all to ensure it fires)
        self.root.bind_all('<Command-e>', self.save_annotated_file)

        # Bind Command+R to refresh tree
        self.root.bind('<Command-r>', self.refresh_tree_manual)

        # Bind Command+Shift+Up to read the previous comment aloud
        self.root.bind('<Command-Shift-Up>', self.read_previous_comment)

        # Bind Command+Shift+Down to read the next comment aloud
        self.root.bind('<Command-Shift-Down>', self.read_next_comment)

        # Bind Command+Shift+Left to stop comment dictation
        self.root.bind('<Command-Shift-Left>', self.stop_comment_dictation)

        # Bind Command+K to show shortcuts viewer
        self.root.bind('<Command-k>', self.show_shortcuts)

        # Track which pane has focus
        self.focus_on_reader = False

        # Track comment reading state
        self.current_comment_reading_index = -1
        self.dictation_process = None  # Process for reading comments aloud
        self.dictation_temp_file = None

        # Comment narration state
        self.narrate_comments = False  # Toggle for auto-narration
        self.narration_queue = []  # Queue of comments to narrate
        self.is_narrating = False  # Currently narrating flag
        self.narration_process = None  # Current narration subprocess

        # Populate both tabs
        self.populate_favorites()
        self.populate_directories_tree()

        # Restore previous session
        self.restore_session()

    def restore_session(self):
        """Restore the previous session state"""
        try:
            saved_dir, saved_file, saved_cell = self.load_session_state()

            # Restore directory if available
            if saved_dir and os.path.isdir(saved_dir):
                self.current_root = saved_dir
                self.path_entry.delete(0, tk.END)
                self.path_entry.insert(0, saved_dir)
                try:
                    # Refresh directories tab with new root
                    self.tree.delete(*self.tree.get_children())
                    self.populate_directories_tree()
                except Exception as e:
                    print(f"Error refreshing trees: {e}")
                    # Reset to home on error
                    self.current_root = self.home_directory
                    self.path_entry.delete(0, tk.END)
                    self.path_entry.insert(0, self.home_directory)

            # Restore file if available
            if saved_file and os.path.isfile(saved_file):
                # Check file size before attempting to load (skip files > 10MB)
                file_size = os.path.getsize(saved_file)
                if file_size < 10 * 1024 * 1024:  # 10MB limit
                    # Use root.after to ensure UI is fully initialized
                    self.root.after(100, lambda: self._restore_file_and_cell(saved_file, saved_cell))
                else:
                    print(f"Skipping large file ({file_size} bytes): {saved_file}")
        except Exception as e:
            print(f"Error restoring session: {e}")
            # Continue with default state

    def _restore_file_and_cell(self, file_path, cell_index):
        """Helper method to restore file and cell position"""
        try:
            self.display_file(file_path)
            # Navigate to saved cell if it exists
            if self.cells and 0 <= cell_index < len(self.cells):
                self.current_cell = cell_index
                self.display_current_cell()
        except Exception as e:
            print(f"Error restoring session: {e}")

    def populate_favorites(self):
        """Populate favorites tree with starred items"""
        self.favorites_tree.delete(*self.favorites_tree.get_children())

        # Configure favorites tree with no extra columns (simpler approach)
        self.favorites_tree['columns'] = ()
        self.favorites_tree.column('#0', width=400)

        starred_paths = self.get_starred_items()

        for path in starred_paths:
            if os.path.exists(path):
                name = os.path.basename(path)
                is_dir = os.path.isdir(path)

                # Just show the starred item name
                display_text = f'⭐ {name}'

                node = self.favorites_tree.insert(
                    '',
                    'end',
                    text=display_text,
                    values=[path],
                    open=is_dir and path in self.favorites_open_paths,
                    tags=('favorite',)
                )

                if is_dir and path in self.favorites_open_paths:
                    self.populate_favorites_subtree(node, path)
                elif is_dir:
                    self.favorites_tree.insert(node, 'end', text='Loading...')

        self.restore_navigation_state()
        self.schedule_navigation_state_save()

    def toggle_star(self, event):
        """Toggle star on selected item"""
        # Determine which tree was clicked
        widget = event.widget
        item = widget.identify_row(event.y)
        if not item:
            return

        values = widget.item(item)['values']
        if not values:
            return

        path = values[0]

        if self.is_starred(path):
            self.remove_star(path)
        else:
            self.add_star(path)

        # Refresh both trees
        self.update_tree_item_display(item, path, widget)
        self.populate_favorites()
        if widget == self.tree:
            self.refresh_tree()

    def update_tree_item_display(self, item, path, widget):
        """Update tree item to show star status"""
        current_text = widget.item(item)['text']
        base_name = current_text.replace('⭐ ', '')

        if self.is_starred(path):
            widget.item(item, text=f'⭐ {base_name}')
        else:
            widget.item(item, text=base_name)

    def toggle_settings(self):
        """Toggle settings panel visibility"""
        if self.settings_expanded:
            # Collapse settings
            self.settings_panel.pack_forget()
            self.settings_expanded = False
            self.settings_button.config(
                bg="#cccccc",
                fg="#000000",
                font=('Consolas', 10)
            )
        else:
            # Expand settings
            self.settings_expanded = True
            self.settings_button.config(
                bg=self.button_color,
                fg=self.button_text_color,
                font=('Consolas', 10, 'bold')
            )

            # Clear and rebuild settings panel
            for widget in self.settings_panel.winfo_children():
                widget.destroy()

            self.settings_panel.config(bg=self.border_color, padx=10, pady=10)
            # Pack settings panel before the bottom_controls frame for proper positioning
            self.settings_panel.pack(side=tk.BOTTOM, fill=tk.X, before=self.bottom_controls, padx=5, pady=(0, 5))

            # Home Directory setting
            tk.Label(
                self.settings_panel,
                text="Home Directory:",
                bg=self.border_color,
                fg=self.fg_color,
                font=('Consolas', 10, 'bold')
            ).pack(pady=(5, 3), anchor='w')

            home_frame = tk.Frame(self.settings_panel, bg=self.border_color)
            home_frame.pack(fill=tk.X, pady=3)

            self.home_entry = tk.Entry(
                home_frame,
                bg=self.bg_color,
                fg=self.fg_color,
                insertbackground=self.fg_color,
                font=('Consolas', 9),
                width=25
            )
            self.home_entry.insert(0, self.home_directory)
            self.home_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

            def browse_directory():
                from tkinter import filedialog
                directory = filedialog.askdirectory(initialdir=self.home_directory)
                if directory:
                    self.home_entry.delete(0, tk.END)
                    self.home_entry.insert(0, directory)

            tk.Button(
                home_frame,
                text="...",
                bg="#cccccc",
                fg="#000000",
                font=('Consolas', 9),
                relief=tk.RAISED,
                padx=8,
                pady=2,
                command=browse_directory
            ).pack(side=tk.LEFT)

            # Voice Speed setting
            tk.Label(
                self.settings_panel,
                text="Voice Speed:",
                bg=self.border_color,
                fg=self.fg_color,
                font=('Consolas', 10, 'bold')
            ).pack(pady=(10, 3), anchor='w')

            speed_frame = tk.Frame(self.settings_panel, bg=self.border_color)
            speed_frame.pack(fill=tk.X, pady=3)

            self.speed_var = tk.IntVar(value=self.voice_speed)
            self.speed_label = tk.Label(
                speed_frame,
                text=f"{self.voice_speed} wpm",
                bg=self.border_color,
                fg=self.fg_color,
                font=('Consolas', 9),
                width=8
            )
            self.speed_label.pack(side=tk.LEFT, padx=(0, 5))

            def update_speed_label(val):
                self.speed_label.config(text=f"{int(float(val))} wpm")

            speed_slider = tk.Scale(
                speed_frame,
                from_=100,
                to=400,
                orient=tk.HORIZONTAL,
                variable=self.speed_var,
                bg=self.border_color,
                fg=self.fg_color,
                highlightthickness=0,
                command=update_speed_label,
                length=130,
                font=('Consolas', 8)
            )
            speed_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

            def test_voice():
                sample_text = "This is a sample of the voice speed you have selected."
                temp_speed = self.speed_var.get()
                # Test with the selected speed
                import subprocess
                try:
                    test_process = subprocess.Popen(
                        ['say', '-r', str(temp_speed), sample_text],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                except Exception as e:
                    print(f"TTS test error: {e}")

            tk.Button(
                speed_frame,
                text="Test",
                bg="#cccccc",
                fg="#000000",
                font=('Consolas', 9),
                relief=tk.RAISED,
                padx=8,
                pady=2,
                command=test_voice
            ).pack(side=tk.LEFT)

            # Export behavior
            tk.Label(
                self.settings_panel,
                text="Export Behavior:",
                bg=self.border_color,
                fg=self.fg_color,
                font=('Consolas', 10, 'bold')
            ).pack(pady=(10, 3), anchor='w')

            export_frame = tk.Frame(self.settings_panel, bg=self.border_color)
            export_frame.pack(fill=tk.X, pady=3)

            self.export_prompt_var = tk.BooleanVar(value=getattr(self, 'export_prompt', True))
            tk.Checkbutton(
                export_frame,
                text="Always prompt for save location on Cmd+E",
                variable=self.export_prompt_var,
                onvalue=True,
                offvalue=False,
                bg=self.border_color,
                fg=self.fg_color,
                selectcolor=self.border_color,
                activebackground=self.border_color,
                activeforeground=self.fg_color,
                highlightthickness=0,
                font=('Consolas', 9)
            ).pack(anchor='w')

            # OpenAI API Key setting
            tk.Label(
                self.settings_panel,
                text="OpenAI API Key:",
                bg=self.border_color,
                fg=self.fg_color,
                font=('Consolas', 10, 'bold')
            ).pack(pady=(10, 3), anchor='w')

            api_frame = tk.Frame(self.settings_panel, bg=self.border_color)
            api_frame.pack(fill=tk.X, pady=3)

            self.api_key_entry = tk.Entry(
                api_frame,
                bg=self.bg_color,
                fg=self.fg_color,
                insertbackground=self.fg_color,
                font=('Consolas', 9),
                show="•",
                width=35
            )
            self.api_key_entry.insert(0, self.openai_api_key)
            self.api_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

            tk.Label(
                self.settings_panel,
                text="Used for @chat commands in comments",
                bg=self.border_color,
                fg="#888888",
                font=('Consolas', 8)
            ).pack(pady=(2, 0), anchor='w')

            def save_settings():
                new_home = self.home_entry.get()
                new_speed = self.speed_var.get()
                new_api_key = self.api_key_entry.get()
                new_export_prompt = bool(self.export_prompt_var.get())

                if os.path.isdir(new_home):
                    self.home_directory = new_home
                    self.current_root = new_home
                    self.save_setting('home_directory', new_home)
                    self.path_entry.delete(0, tk.END)
                    self.path_entry.insert(0, new_home)
                    # Refresh directories tab with new home (favorites auto-updates)
                    self.tree.delete(*self.tree.get_children())
                    self.populate_directories_tree()

                self.voice_speed = new_speed
                self.save_setting('voice_speed', new_speed)

                self.openai_api_key = new_api_key
                self.save_setting('openai_api_key', new_api_key)

                # Save export behavior
                self.export_prompt = new_export_prompt
                self.save_setting('export_prompt', '1' if new_export_prompt else '0')

                self.toggle_settings()

            tk.Button(
                self.settings_panel,
                text="Save Settings",
                bg=self.button_color,
                fg=self.button_text_color,
                font=('Consolas', 10, 'bold'),
                relief=tk.RAISED,
                padx=15,
                pady=5,
                command=save_settings
            ).pack(pady=(10, 5))

    def toggle_accordion_item(self, item_name):
        """Toggle expansion of an accordion menu item"""
        # If clicking the currently expanded item, collapse it
        if self.expanded_menu_item == item_name:
            # Collapse current item
            if item_name == 'directories':
                self.directories_content_frame.pack_forget()
                self.directories_header_button.config(text="📁 Directories ▶")
            elif item_name == 'paste':
                self.paste_content_frame.pack_forget()
                self.paste_header_button.config(text="📋 New Paste ▶")
            elif item_name == 'settings':
                self.settings_content_frame.pack_forget()
                self.settings_header_button.config(text="⚙️ Settings ▶")

            self.expanded_menu_item = None
        else:
            # Collapse previously expanded item (if any)
            if self.expanded_menu_item == 'directories':
                self.directories_content_frame.pack_forget()
                self.directories_header_button.config(text="📁 Directories ▶")
            elif self.expanded_menu_item == 'paste':
                self.paste_content_frame.pack_forget()
                self.paste_header_button.config(text="📋 New Paste ▶")
            elif self.expanded_menu_item == 'settings':
                self.settings_content_frame.pack_forget()
                self.settings_header_button.config(text="⚙️ Settings ▶")

            # Expand the clicked item
            if item_name == 'directories':
                self.directories_header_button.config(text="📁 Directories ▼")
                self.directories_content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 2), after=self.directories_header_frame)
                # Populate directories tree if empty
                if not self.tree.get_children():
                    self.populate_directories_tree()
            elif item_name == 'paste':
                self.paste_header_button.config(text="📋 New Paste ▼")
                # Clear and rebuild paste content
                for widget in self.paste_content_frame.winfo_children():
                    widget.destroy()
                self.build_paste_inline_ui()
                self.paste_content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 2), after=self.paste_header_frame)
            elif item_name == 'settings':
                self.settings_header_button.config(text="⚙️ Settings ▼")
                # Clear and rebuild settings content
                for widget in self.settings_content_frame.winfo_children():
                    widget.destroy()
                self.build_settings_inline_ui()
                self.settings_content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 2), after=self.settings_header_frame)

            self.expanded_menu_item = item_name

    def build_paste_inline_ui(self):
        """Build the paste UI inline in the accordion"""
        # Instruction label
        label = tk.Label(
            self.paste_content_frame,
            text="Paste your content below (split by blank lines into cells):",
            bg=self.bg_color,
            fg=self.fg_color,
            font=('Consolas', 9)
        )
        label.pack(fill=tk.X, pady=(5, 5), padx=10)

        # Text area for pasting
        text_frame = tk.Frame(self.paste_content_frame, bg=self.border_color)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5), padx=10)

        paste_text = tk.Text(
            text_frame,
            bg=self.bg_color,
            fg=self.fg_color,
            insertbackground=self.fg_color,
            font=('Consolas', 9),
            wrap=tk.WORD,
            relief=tk.FLAT,
            borderwidth=1,
            height=8
        )
        paste_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = tk.Scrollbar(text_frame, command=paste_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        paste_text.config(yscrollcommand=scrollbar.set)

        # Buttons frame
        button_frame = tk.Frame(self.paste_content_frame, bg=self.bg_color)
        button_frame.pack(fill=tk.X, pady=(0, 5), padx=10)

        def create_file():
            """Create file from pasted content"""
            content = paste_text.get('1.0', tk.END).strip()
            if not content:
                from tkinter import messagebox
                messagebox.showwarning("Empty Content", "Please paste some content first")
                return

            # Ask user where to save
            try:
                self.root.update_idletasks()
            except Exception:
                pass

            save_path = filedialog.asksaveasfilename(
                title="Save Paste File",
                initialfile="pasted_content.md",
                defaultextension=".md",
                filetypes=[("Markdown", "*.md"), ("Text", "*.txt"), ("All Files", "*.*")]
            )

            if not save_path:
                return  # User cancelled

            try:
                # Parse content into cells
                self.cells = []
                self.parse_paste_cells(content)

                # Reconstruct file content with headings
                file_content = '\n\n'.join(self.cells)

                # Write to file
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(file_content)

                # Collapse paste menu
                self.toggle_accordion_item('paste')

                # Open the file in viewer
                self.display_file(save_path)

            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Error", f"Failed to create file: {e}")

        create_button = tk.Button(
            button_frame,
            text="Create File",
            bg=self.button_color,
            fg=self.button_text_color,
            activebackground=self.button_active_color,
            activeforeground=self.button_text_color,
            font=('Consolas', 9, 'bold'),
            relief=tk.RAISED,
            padx=15,
            pady=3,
            cursor='hand2',
            borderwidth=1,
            highlightthickness=0,
            command=create_file
        )
        create_button.pack(side=tk.LEFT)

    def build_settings_inline_ui(self):
        """Build the settings UI inline in the accordion"""
        self.settings_content_frame.config(bg=self.border_color, padx=10, pady=10)

        # Home Directory setting
        tk.Label(
            self.settings_content_frame,
            text="Home Directory:",
            bg=self.border_color,
            fg=self.fg_color,
            font=('Consolas', 9, 'bold')
        ).pack(pady=(5, 3), anchor='w')

        home_frame = tk.Frame(self.settings_content_frame, bg=self.border_color)
        home_frame.pack(fill=tk.X, pady=3)

        self.home_entry = tk.Entry(
            home_frame,
            bg=self.bg_color,
            fg=self.fg_color,
            insertbackground=self.fg_color,
            font=('Consolas', 8),
            width=25
        )
        self.home_entry.insert(0, self.home_directory)
        self.home_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        def browse_directory():
            from tkinter import filedialog
            directory = filedialog.askdirectory(initialdir=self.home_directory)
            if directory:
                self.home_entry.delete(0, tk.END)
                self.home_entry.insert(0, directory)

        tk.Button(
            home_frame,
            text="...",
            bg="#cccccc",
            fg="#000000",
            font=('Consolas', 8),
            relief=tk.RAISED,
            padx=6,
            pady=1,
            command=browse_directory
        ).pack(side=tk.LEFT)

        # Voice Speed setting
        tk.Label(
            self.settings_content_frame,
            text="Voice Speed:",
            bg=self.border_color,
            fg=self.fg_color,
            font=('Consolas', 9, 'bold')
        ).pack(pady=(10, 3), anchor='w')

        speed_frame = tk.Frame(self.settings_content_frame, bg=self.border_color)
        speed_frame.pack(fill=tk.X, pady=3)

        self.speed_entry = tk.Entry(
            speed_frame,
            bg=self.bg_color,
            fg=self.fg_color,
            insertbackground=self.fg_color,
            font=('Consolas', 8),
            width=10
        )
        self.speed_entry.insert(0, str(self.voice_speed))
        self.speed_entry.pack(side=tk.LEFT)

        tk.Label(
            speed_frame,
            text=" words/min",
            bg=self.border_color,
            fg=self.fg_color,
            font=('Consolas', 8)
        ).pack(side=tk.LEFT, padx=(5, 0))

        # OpenAI API Key setting
        tk.Label(
            self.settings_content_frame,
            text="OpenAI API Key:",
            bg=self.border_color,
            fg=self.fg_color,
            font=('Consolas', 9, 'bold')
        ).pack(pady=(10, 3), anchor='w')

        self.api_key_entry = tk.Entry(
            self.settings_content_frame,
            bg=self.bg_color,
            fg=self.fg_color,
            insertbackground=self.fg_color,
            font=('Consolas', 8),
            show="*",
            width=30
        )
        self.api_key_entry.insert(0, self.openai_api_key)
        self.api_key_entry.pack(fill=tk.X, pady=3)

        # Export prompt checkbox
        self.export_prompt_var = tk.BooleanVar(value=getattr(self, 'export_prompt', True))
        tk.Checkbutton(
            self.settings_content_frame,
            text="Always prompt for save location on Cmd+E",
            variable=self.export_prompt_var,
            bg=self.border_color,
            fg=self.fg_color,
            selectcolor=self.bg_color,
            activebackground=self.border_color,
            activeforeground=self.fg_color,
            font=('Consolas', 8)
        ).pack(pady=(10, 5), anchor='w')

        # Save button
        def save_settings():
            # Get new values
            new_home = self.home_entry.get().strip()
            new_speed = int(self.speed_entry.get().strip()) if self.speed_entry.get().strip().isdigit() else self.voice_speed
            new_api_key = self.api_key_entry.get().strip()
            export_prompt_value = '1' if self.export_prompt_var.get() else '0'

            # Save to database
            if new_home != self.home_directory:
                self.home_directory = new_home
                self.current_root = new_home
                self.save_setting('home_directory', new_home)
                self.path_entry.delete(0, tk.END)
                self.path_entry.insert(0, new_home)
                # Refresh directories tree with new home
                self.tree.delete(*self.tree.get_children())
                self.populate_directories_tree()

            self.voice_speed = new_speed
            self.save_setting('voice_speed', new_speed)

            self.openai_api_key = new_api_key
            self.save_setting('openai_api_key', new_api_key)

            self.export_prompt = self.export_prompt_var.get()
            self.save_setting('export_prompt', export_prompt_value)

            # Collapse settings
            self.toggle_accordion_item('settings')

        tk.Button(
            self.settings_content_frame,
            text="Save Settings",
            bg=self.button_color,
            fg=self.button_text_color,
            font=('Consolas', 9, 'bold'),
            relief=tk.RAISED,
            padx=15,
            pady=4,
            command=save_settings
        ).pack(pady=(10, 5))

    def navigate_to_path(self, event):
        """Navigate to the path entered in the path entry"""
        path = self.path_entry.get()
        path = os.path.expanduser(path)

        if os.path.isdir(path):
            self.current_root = path
            # Refresh directories tab with new root (favorites stays same)
            self.tree.delete(*self.tree.get_children())
            self.populate_directories_tree()
            self.save_session_state()
        else:
            self.path_label.config(text=f"Error: '{path}' is not a valid directory")

    def refresh_tree_manual(self, event=None):
        """Manually refresh all trees (triggered by Command+R)"""
        # Refresh favorites
        self.favorites_tree.delete(*self.favorites_tree.get_children())
        self.populate_favorites()

        # Refresh directories if expanded
        if self.expanded_menu_item == 'directories':
            self.tree.delete(*self.tree.get_children())
            self.populate_directories_tree(path=self.current_root)

        # Show brief confirmation in path label
        original_text = self.path_label.cget('text')
        self.path_label.config(text="🔄 Trees refreshed")

        def reset_label():
            self.path_label.config(text=original_text)

        self.root.after(1000, reset_label)

        return 'break'

    def show_shortcuts(self, event=None):
        """Display a simple Keyboard Shortcuts viewer grouped by section."""
        # If already open, focus it
        if getattr(self, 'shortcuts_window', None) is not None:
            if self.shortcuts_window.winfo_exists():
                self.shortcuts_window.lift()
                self.shortcuts_window.focus_force()
                return 'break'

        win = tk.Toplevel(self.root)
        win.title("Keyboard Shortcuts")
        win.configure(bg=self.bg_color)
        win.geometry("660x540")
        self.shortcuts_window = win

        # Close on Escape
        win.bind('<Escape>', lambda e: win.destroy())

        container = tk.Frame(win, bg=self.bg_color)
        container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        tk.Label(container, text="Keyboard Shortcuts", bg=self.bg_color, fg=self.fg_color,
                 font=('Consolas', 14, 'bold')).pack(anchor='w', pady=(0, 8))

        text = tk.Text(container,
                       bg=self.border_color,
                       fg=self.fg_color,
                       insertbackground=self.fg_color,
                       wrap=tk.WORD,
                       height=24,
                       relief=tk.FLAT)
        text.pack(fill=tk.BOTH, expand=True)

        # Sections and shortcuts
        sections = [
            ("General", [
                ("Cmd+K", "Open this shortcuts viewer"),
                ("Cmd+R", "Refresh trees (files and favorites)"),
                ("Cmd+/", "Toggle focus between left pane and reader"),
            ]),
            ("File/Export", [
                ("Cmd+E", "Save annotated copy of current markdown"),
            ]),
            ("Cell Navigation", [
                ("Up/Down", "Move to previous/next cell"),
                ("Left", "Start/stop reading current cell"),
                ("Right", "View comments for current cell"),
            ]),
            ("Comments", [
                ("Cmd+Shift+Up", "Read previous comment (voice)"),
                ("Cmd+Shift+Down", "Read next comment (voice)"),
                ("Cmd+Shift+Left", "Stop reading comment (voice)"),
                ("Cmd+Enter (in comment box)", "Save new comment or @chat question"),
            ]),
            ("Mouse & Tips", [
                ("Right‑click/Ctrl‑click in trees", "Toggle star on a file or folder"),
            ]),
        ]

        text.tag_configure('section', foreground=self.fg_color, font=('Consolas', 12, 'bold'))

        for title, items in sections:
            text.insert(tk.END, f"{title}\n", 'section')
            for keys, desc in items:
                text.insert(tk.END, f"  • {keys}: {desc}\n")
            text.insert(tk.END, "\n")

        text.config(state=tk.DISABLED)
        return 'break'

    def populate_directories_tree(self, parent='', path=None, depth=0, max_depth=10):
        """Populate Directories tab tree with all files and directories"""
        # Clear tree only on root-level population (when parent is empty and depth is 0)
        if parent == '' and depth == 0:
            self.tree.delete(*self.tree.get_children())
            # Configure tree columns (like in populate_favorites)
            self.tree['columns'] = ()
            self.tree.column('#0', width=400)

        if path is None:
            path = self.current_root

        # Prevent infinite recursion and symlink loops
        if depth >= max_depth:
            return

        # Skip symlinks to prevent loops
        if os.path.islink(path):
            return

        try:
            items = sorted(os.listdir(path))
            # Limit items to prevent UI freeze on huge directories
            if len(items) > 1000:
                items = items[:1000]
        except (PermissionError, OSError):
            return

        for item in items:
            if item.startswith('.'):
                continue

            item_path = os.path.join(path, item)

            try:
                # Skip symlinks
                if os.path.islink(item_path):
                    continue

                is_dir = os.path.isdir(item_path)

                # Show all files and directories (no filter)

                display_name = f'⭐ {item}' if self.is_starred(item_path) else item
                open_paths = self.directories_open_paths  # Directories tree open paths

                node = self.tree.insert(
                    parent,
                    'end',
                    text=display_name,
                    values=[item_path],
                    open=False
                )

                if is_dir:
                    if item_path in open_paths:
                        self.tree.item(node, open=True)
                        self.populate_directories_tree(node, item_path, depth=depth+1, max_depth=max_depth)
                    else:
                        self.tree.insert(node, 'end', text='Loading...')

            except (PermissionError, OSError):
                continue

    def on_folder_open(self, event):
        """Handle folder expansion"""
        widget = event.widget
        node = widget.focus()
        children = widget.get_children(node)

        if len(children) == 1 and widget.item(children[0])['text'] == 'Loading...':
            widget.delete(children[0])
            path = widget.item(node)['values'][0]
            if widget == self.tree:
                # Directories tab
                self.populate_directories_tree(node, path)
            else:  # favorites_tree
                self.populate_favorites_subtree(node, path)

        self.save_current_tab_state()

    def on_folder_close(self, event):
        """Handle folder collapse events"""
        self.save_current_tab_state()

    def populate_favorites_subtree(self, parent, path, depth=0, max_depth=10):
        """Populate subtree in favorites tree"""
        # Prevent infinite recursion
        if depth >= max_depth:
            return

        # Skip symlinks to prevent loops
        if os.path.islink(path):
            return

        try:
            items = sorted(os.listdir(path))
            # Limit items to prevent UI freeze
            if len(items) > 1000:
                items = items[:1000]
        except (PermissionError, OSError):
            return

        for item in items:
            if item.startswith('.'):
                continue

            # Hide Python dunder files/directories (__name__ or __name__.py)
            if item.startswith('__'):
                # For directories, check if ends with __
                if item.endswith('__'):
                    continue
                # For .py files, check if the name without .py ends with __
                if item.endswith('.py') and item[:-3].endswith('__'):
                    continue

            item_path = os.path.join(path, item)

            try:
                # Skip symlinks
                if os.path.islink(item_path):
                    continue

                is_dir = os.path.isdir(item_path)

                display_name = f'⭐ {item}' if self.is_starred(item_path) else item
                open_paths = self.favorites_open_paths  # Favorites tree open paths

                node = self.favorites_tree.insert(
                    parent,
                    'end',
                    text=display_name,
                    values=[item_path],
                    open=False
                )

                if is_dir:
                    if item_path in open_paths:
                        self.favorites_tree.item(node, open=True)
                        self.populate_favorites_subtree(node, item_path, depth=depth+1, max_depth=max_depth)
                    else:
                        self.favorites_tree.insert(node, 'end', text='Loading...')

            except (PermissionError, OSError):
                continue

    def on_file_select(self, event):
        """Handle file selection"""
        widget = event.widget
        selected = widget.selection()
        if not selected:
            return

        item = selected[0]
        values = widget.item(item)['values']

        if not values:
            return

        file_path = values[0]

        if os.path.isfile(file_path):
            self.display_file(file_path)

        self.schedule_navigation_state_save()

    def get_cell_hash(self, content):
        """Generate hash for cell content"""
        import hashlib
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def extract_heading(self, cell_content):
        """Extract heading text from cell content"""
        lines = cell_content.strip().split('\n')
        for line in lines:
            if line.startswith('#'):
                return line.strip()
        return "[No Heading]"

    def get_comments(self, file_path, cell_content, cell_index):
        """Get comments for a specific cell with fuzzy matching"""
        heading = self.extract_heading(cell_content)
        content_hash = self.get_cell_hash(cell_content)

        # Try exact match first
        self.cursor.execute(
            '''SELECT id, comment_text, created_at, match_confidence 
               FROM comments 
               WHERE file_path = ? AND heading_text = ? AND content_hash = ?
               ORDER BY created_at''',
            (file_path, heading, content_hash)
        )
        exact_matches = self.cursor.fetchall()

        if exact_matches:
            # Update last_matched_at
            for comment_id, *_ in exact_matches:
                self.cursor.execute(
                    'UPDATE comments SET last_matched_at = CURRENT_TIMESTAMP, match_confidence = ? WHERE id = ?',
                    ('exact', comment_id)
                )
            self.conn.commit()
            return [(text, created, conf) for _, text, created, conf in exact_matches]

        # Try heading match only
        self.cursor.execute(
            '''SELECT id, comment_text, created_at, match_confidence 
               FROM comments 
               WHERE file_path = ? AND heading_text = ?
               ORDER BY created_at''',
            (file_path, heading)
        )
        heading_matches = self.cursor.fetchall()

        if heading_matches:
            # Update with fuzzy confidence
            for comment_id, *_ in heading_matches:
                self.cursor.execute(
                    'UPDATE comments SET last_matched_at = CURRENT_TIMESTAMP, match_confidence = ? WHERE id = ?',
                    ('fuzzy', comment_id)
                )
            self.conn.commit()
            return [(text, created, 'fuzzy') for _, text, created, _ in heading_matches]

        return []

    def add_comment(self, file_path, cell_content, cell_index, comment_text):
        """Add a comment to a cell"""
        heading = self.extract_heading(cell_content)
        content_hash = self.get_cell_hash(cell_content)

        print(f"DEBUG add_comment: file={file_path}, heading={heading}, hash={content_hash[:8]}, index={cell_index}")

        try:
            self.cursor.execute(
                '''INSERT INTO comments
                   (file_path, heading_text, content_hash, cell_index, comment_text, match_confidence)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (file_path, heading, content_hash, cell_index, comment_text, 'exact')
            )
            self.conn.commit()
            print("DEBUG: Comment inserted successfully")
            return True
        except Exception as e:
            print(f"DEBUG: Error inserting comment: {e}")
            return False

    def stop_reading(self):
        """Stop text-to-speech"""
        if self.tts_process:
            self.tts_process.terminate()
            self.tts_process = None
        self.reading_mode = False
        self.display_current_cell()

    def clean_text_for_reading(self, text):
        """Clean markdown text for TTS reading"""
        import re

        # Remove code blocks entirely
        text = re.sub(r'```[\s\S]*?```', '', text)

        # Remove inline code
        text = re.sub(r'`[^`]+`', '', text)

        # Remove heading markers but keep the text
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

        # Remove bold/italic markers
        text = re.sub(r'\*\*\*(.+?)\*\*\*', r'\1', text)  # Bold+italic
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.+?)\*', r'\1', text)  # Italic
        text = re.sub(r'__(.+?)__', r'\1', text)  # Bold (underscore)
        text = re.sub(r'_(.+?)_', r'\1', text)  # Italic (underscore)

        # Remove links but keep text
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

        # Remove images
        text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', text)

        # Remove horizontal rules
        text = re.sub(r'^[-*_]{3,}$', '', text, flags=re.MULTILINE)

        # Remove blockquote markers
        text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)

        # Remove list markers but keep content
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Remove strikethrough
        text = re.sub(r'~~(.+?)~~', r'\1', text)

        # Clean up excessive whitespace but preserve paragraph breaks
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)

        # Remove empty lines at start/end
        text = text.strip()

        return text

    def start_reading(self, text=None):
        """Start reading the current cell aloud"""
        import subprocess
        import re

        if self.reading_mode and text is None:
            self.stop_reading()
            return

        if text is None:
            cell_content = self.cells[self.current_cell]
        else:
            cell_content = text

        if not cell_content.strip():
            return  # Don't read empty content

        # Calculate pause durations proportional to speed
        # Slower speed = longer pause, faster speed = shorter pause
        base_speed = 200
        heading_pause_ms = int(1200 * (base_speed / self.voice_speed))  # Longer pause after headings
        paragraph_pause_ms = int(600 * (base_speed / self.voice_speed))  # Medium pause between paragraphs

        print(f"DEBUG: Reading with voice_speed={self.voice_speed} wpm, heading_pause={heading_pause_ms}ms, paragraph_pause={paragraph_pause_ms}ms")

        # Process the text differently to preserve heading structure
        lines = cell_content.split('\n')
        processed_parts = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if line is a heading
            if line.startswith('#'):
                # Extract heading text without markdown
                heading_text = re.sub(r'^#{1,6}\s+', '', line)
                # Add heading with pause after
                processed_parts.append(heading_text + f' [[slnc {heading_pause_ms}]]')
            else:
                # Regular text - clean markdown
                cleaned = self.clean_text_for_reading(line)
                if cleaned:
                    processed_parts.append(cleaned)

        # Join parts with paragraph pauses
        text_with_pauses = f' [[slnc {paragraph_pause_ms}]] '.join(processed_parts)

        # Use macOS 'say' command with voice speed
        try:
            self.reading_mode = True
            cmd = ['say', '-r', str(self.voice_speed), text_with_pauses]
            print(f"DEBUG: Running command: say -r {self.voice_speed} [text with {len(text_with_pauses)} chars]")
            self.tts_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            if hasattr(self, 'cells') and self.cells:
                self.display_current_cell()  # Refresh to show reading indicator

            # Monitor when reading finishes
            self.root.after(100, self.check_reading_status)
        except Exception as e:
            print(f"TTS error: {e}")
            self.reading_mode = False

    def check_reading_status(self):
        """Check if TTS is still running"""
        if self.tts_process and self.tts_process.poll() is None:
            # Still reading, check again
            self.root.after(100, self.check_reading_status)
        else:
            # Finished reading
            self.reading_mode = False
            self.tts_process = None
            self.display_current_cell()

    def toggle_focus(self, event):
        """Toggle focus between left panel and reader/outline"""
        # Check if Python outline view is active
        python_outline_active = self.py_frame.winfo_ismapped()

        if python_outline_active:
            # Python outline mode: toggle between left tabs and middle outline
            self.focus_on_reader = not self.focus_on_reader

            if self.focus_on_reader:
                # Focus on middle outline
                self.py_outline.focus_set()
            else:
                # Focus on left panel (current tab's tree)
                self.focus_current_tree()
        else:
            # Normal mode: toggle between left tabs and text widget
            self.focus_on_reader = not self.focus_on_reader

            if self.focus_on_reader:
                # Focus on text widget
                self.text_widget.focus_set()
            else:
                # Focus on left panel (current tab's tree)
                self.focus_current_tree()

        return 'break'

    def focus_current_tree(self):
        """Focus the appropriate tree (favorites or expanded accordion item)"""
        if self.expanded_menu_item == 'directories':
            self.tree.focus_set()
        else:
            # Default to favorites tree (always visible)
            self.favorites_tree.focus_set()

    def save_annotated_file(self, event):
        """Save an annotated version of the current markdown file with comments embedded.

        Prompts for a destination file (defaults to the current file's directory)
        and filename with an '__annotated__YYYYMMDD_HHMM.md' suffix.
        """
        if not self.current_file or not self.current_file.endswith('.md'):
            return 'break'

        if not self.cells:
            return 'break'

        # Get the directory and filename
        file_dir = os.path.dirname(self.current_file)
        file_name = os.path.basename(self.current_file).rsplit('.', 1)[0]

        # Create timestamp suffix (format: YYYYMMDD_HHMM)
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")

        # Create new filename with __annotated and timestamp suffix
        annotated_filename = f"{file_name}__annotated__{timestamp}.md"

        # Decide save path
        save_path = ''
        if getattr(self, 'export_prompt', True):
            # Ask user where to save (defaults to same directory)
            try:
                # Ensure window is realized to avoid macOS sheet errors
                try:
                    self.root.update_idletasks()
                except Exception:
                    pass

                save_path = filedialog.asksaveasfilename(
                    title="Save Annotated Markdown",
                    initialdir=file_dir,
                    initialfile=annotated_filename,
                    defaultextension=".md",
                    filetypes=[("Markdown", "*.md"), ("All Files", "*.*")]
                )
            except Exception:
                save_path = ''
            if not save_path:
                # User cancelled
                return 'break'
        else:
            # Auto-save next to current file
            save_path = os.path.join(file_dir, annotated_filename)

        # Build annotated content
        annotated_lines = []

        for i, cell_content in enumerate(self.cells):
            # Add the cell content
            annotated_lines.append(cell_content)

            # Get comments for this cell
            comments = self.get_comments(self.current_file, cell_content, i)

            if comments:
                # Add comments as blockquotes
                annotated_lines.append("\n")
                annotated_lines.append("---")
                annotated_lines.append("\n**💬 Comments:**\n")
                for comment_text, created_at, confidence in comments:
                    confidence_marker = " ⚠️ (may be outdated)" if confidence == 'fuzzy' else ""
                    annotated_lines.append(f"\n> **Comment** ({created_at}){confidence_marker}:")
                    annotated_lines.append(f"> {comment_text}")
                annotated_lines.append("\n---\n")

        # Write to file
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(annotated_lines))

            # Update status in path label
            self.path_label.config(text=f"✓ Saved: {save_path}")
            print(f"Saved annotated file: {save_path}")

            # Refresh the directory in the tree that contains this file
            file_dir = os.path.dirname(self.current_file)

            # If we're currently viewing this directory, refresh it
            if file_dir == self.current_root or self.current_root in file_dir:
                self.refresh_tree()

            # Also refresh favorites in case this directory is starred
            self.populate_favorites()

            # Show a temporary notification
            def reset_label():
                self.path_label.config(text=self.current_file)

            self.root.after(3000, reset_label)  # Reset after 3 seconds

        except Exception as e:
            self.path_label.config(text=f"❌ Error: {e}")
            print(f"Error saving annotated file: {e}")

        return 'break'

    def on_arrow_key(self, event):
        """Handle arrow key navigation"""
        # Check if focus is on the tree views - let them handle arrow keys natively
        focused_widget = self.root.focus_get()
        if focused_widget in (self.tree, self.favorites_tree):
            return  # Let the tree handle the arrow key

        # Only handle arrow keys for markdown cell navigation
        if not self.cells or not self.current_file or not self.current_file.endswith('.md'):
            return

        if self.viewing_comments:
            if event.keysym == 'Left':
                self.viewing_comments = False
                self.display_current_cell()
                return 'break'
        else:
            if event.keysym == 'Left':
                if self.reading_mode:
                    # Stop reading
                    self.stop_reading()
                else:
                    # Start reading
                    self.start_reading()
                return 'break'
            elif event.keysym == 'Down':
                self.stop_reading()  # Stop if navigating away
                self.navigate_to_cell(self.current_cell + 1)
                return 'break'
            elif event.keysym == 'Up':
                self.stop_reading()  # Stop if navigating away
                self.navigate_to_cell(self.current_cell - 1)
                return 'break'
            elif event.keysym == 'Right':
                self.stop_reading()  # Stop if going to comments
                self.viewing_comments = True
                self.display_comments()
                return 'break'

    def navigate_to_cell(self, cell_index):
        """Navigate to a specific cell"""
        if not self.cells:
            return

        cell_index = max(0, min(cell_index, len(self.cells) - 1))

        if cell_index == self.current_cell:
            return

        # Reset comment narration state when moving between cells
        self.stop_comment_dictation()
        self.current_comment_reading_index = -1

        self.current_cell = cell_index
        self.display_current_cell()
        self.save_session_state()

    def display_current_cell(self):
        """Display only the current cell (Instagram shorts style)"""
        if not self.cells or self.current_cell >= len(self.cells):
            return

        self.text_widget.delete('1.0', tk.END)

        total_cells = len(self.cells)
        reading_status = " 🔊 READING..." if self.reading_mode else ""
        indicator = f"Cell {self.current_cell + 1} / {total_cells}{reading_status}   [← Read/Stop] [→ Comments] [↑↓ Navigate]\n"
        self.text_widget.insert('1.0', indicator, 'cell_indicator')
        self.text_widget.insert(tk.END, '─' * 80 + '\n\n', 'separator')

        cell_content = self.cells[self.current_cell]
        self.render_markdown_cell(cell_content)

        comments = self.get_comments(self.current_file, cell_content, self.current_cell)
        if comments:
            fuzzy_count = sum(1 for _, _, conf in comments if conf == 'fuzzy')
            if fuzzy_count > 0:
                self.text_widget.insert(tk.END, f'\n\n💬 {len(comments)} comment(s) (⚠️ {fuzzy_count} may be outdated) - Press → to view', 'comment_hint')
            else:
                self.text_widget.insert(tk.END, f'\n\n💬 {len(comments)} comment(s) - Press → to view', 'comment_hint')
        else:
            self.text_widget.insert(tk.END, '\n\n💬 No comments yet - Press → to add or review', 'comment_hint')

        # Copy cell button
        self.text_widget.insert(tk.END, '\n\n')
        copy_frame = tk.Frame(self.text_widget, bg=self.bg_color)
        self.text_widget.window_create(tk.END, window=copy_frame)

        tk.Button(
            copy_frame,
            text="📋 Copy Cell",
            bg="#4ec9b0",
            fg="#000000",
            font=('Consolas', 9, 'bold'),
            relief=tk.RAISED,
            padx=10,
            pady=3,
            cursor='hand2',
            command=self.copy_current_cell
        ).pack()

    def display_comments(self):
        """Display comments for current cell"""
        self.text_widget.delete('1.0', tk.END)

        self.text_widget.insert('1.0', f"💬 Comments for Cell {self.current_cell + 1}   [← Back]\n", 'comment_header')
        self.text_widget.insert(tk.END, '─' * 80 + '\n\n', 'separator')

        cell_content = self.cells[self.current_cell]
        comments = self.get_comments(self.current_file, cell_content, self.current_cell)

        if comments:
            for i, (comment_text, created_at, confidence) in enumerate(comments, 1):
                prefix = "⚠️ " if confidence == 'fuzzy' else ""
                self.text_widget.insert(tk.END, f"{prefix}Comment {i}:\n", 'comment_number')
                self.text_widget.insert(tk.END, f"{comment_text}\n", 'comment_text')
                confidence_text = " (Content may have changed)" if confidence == 'fuzzy' else ""
                self.text_widget.insert(tk.END, f"Posted: {created_at}{confidence_text}\n\n", 'comment_date')
        else:
            self.text_widget.insert(tk.END, "No comments yet.\n\n", 'no_comments')

        self.text_widget.insert(tk.END, "\n" + "─" * 80 + "\n", 'separator')

        # Narrate toggle button
        narrate_frame = tk.Frame(self.text_widget, bg=self.bg_color)
        self.text_widget.window_create(tk.END, window=narrate_frame)

        narrate_button_text = "🔊 Narrate: ON" if self.narrate_comments else "🔇 Narrate: OFF"
        narrate_button_bg = "#4ec9b0" if self.narrate_comments else "#cccccc"

        self.narrate_button = tk.Button(
            narrate_frame,
            text=narrate_button_text,
            bg=narrate_button_bg,
            fg="#000000",
            font=('Consolas', 9, 'bold'),
            relief=tk.RAISED,
            padx=10,
            pady=3,
            cursor='hand2',
            command=self.toggle_narration
        )
        self.narrate_button.pack(side=tk.LEFT, pady=5)

        narrate_status = " (Comments will be read aloud)" if self.narrate_comments else ""
        status_label = tk.Label(
            narrate_frame,
            text=narrate_status,
            bg=self.bg_color,
            fg="#888888",
            font=('Consolas', 8)
        )
        status_label.pack(side=tk.LEFT, padx=(5, 0))

        self.text_widget.insert(tk.END, "\n")
        self.text_widget.insert(tk.END, "Type a comment or '@chat <question>' to ask AI (Cmd+Enter to save):\n", 'instructions')

        self.comment_input = tk.Text(
            self.text_widget,
            height=4,
            bg=self.border_color,
            fg=self.fg_color,
            font=('Consolas', 10),
            wrap=tk.WORD
        )
        self.text_widget.window_create(tk.END, window=self.comment_input)
        self.comment_input.bind('<Command-Return>', self.save_comment)
        self.comment_input.focus_set()

    def call_openai(self, prompt, cell_context, file_content, previous_comments):
        """Call OpenAI API with the prompt, cell context, file content, and previous comments"""
        if not self.openai_api_key:
            return "Error: OpenAI API key not configured. Please add it in Settings."

        try:
            import json
            import urllib.request
            import urllib.error
            import ssl

            # Create SSL context with certifi bundle (fixes certificate verification issues on macOS)
            try:
                import certifi
                ssl_context = ssl.create_default_context(cafile=certifi.where())
            except ImportError:
                # Fallback: disable SSL verification if certifi not available (not ideal but works)
                ssl_context = ssl._create_unverified_context()
                print("Warning: SSL verification disabled. Install certifi for secure connections.")

            # Prepare the request
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_api_key}"
            }

            # Build context with previous comments
            comments_context = ""
            if previous_comments:
                comments_context = "\n\n## Previous Comments on This Cell:\n"
                for i, (comment_text, created_at, confidence) in enumerate(previous_comments, 1):
                    comments_context += f"\n{i}. {comment_text}\n"

            # Build full context
            full_context = f"""## Full File Content:
{file_content}

## Current Cell Being Discussed:
{cell_context}
{comments_context}

## User Question:
{prompt}"""

            # Build the payload
            payload = {
                "model": "gpt-4",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant analyzing markdown content. The user is reviewing a markdown file and has questions about a specific section (cell). Provide concise, informative, and contextual responses based on the full file content, the current cell, and any previous comments."
                    },
                    {
                        "role": "user",
                        "content": full_context
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 500
            }

            # Make the request
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers=headers,
                method='POST'
            )

            with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result['choices'][0]['message']['content'].strip()

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"OpenAI API Error: {e.code} - {error_body}")
            return f"Error: OpenAI API request failed ({e.code}). Check your API key."
        except Exception as e:
            print(f"OpenAI Error: {e}")
            return f"Error: {str(e)}"

    def save_comment(self, event):
        """Save comment from input"""
        comment_text = self.comment_input.get('1.0', tk.END).strip()
        print(f"DEBUG: Saving comment: '{comment_text}'")

        if comment_text:
            cell_content = self.cells[self.current_cell]

            # Check if comment starts with @chat (AI command)
            if comment_text.lower().startswith('@chat'):
                # Remove the @chat and get the question
                question = comment_text[5:].strip()  # Remove '@chat'

                if not question:
                    # Show error if no question provided
                    self.path_label.config(text="Error: Please provide a question after @chat")
                    def reset_label():
                        self.path_label.config(text=self.current_file)
                    self.root.after(2000, reset_label)
                    return 'break'

                # Show loading message
                self.path_label.config(text="🤖 Asking AI...")
                self.root.update()

                # Get previous comments for context
                previous_comments = self.get_comments(self.current_file, cell_content, self.current_cell)

                # Get full file content
                try:
                    with open(self.current_file, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                except Exception as e:
                    file_content = f"[Error reading file: {e}]"

                # Call OpenAI with full context
                ai_response = self.call_openai(question, cell_content, file_content, previous_comments)

                # Save both the question and the response as comments
                question_comment = f"@chat {question}"
                self.add_comment(self.current_file, cell_content, self.current_cell, question_comment)

                ai_comment = f"🤖 AI: {ai_response}"
                self.add_comment(self.current_file, cell_content, self.current_cell, ai_comment)

                print(f"DEBUG: AI question and response saved")

                # Queue for narration if enabled
                if self.narrate_comments:
                    # Get total comments to determine comment numbers
                    all_comments = self.get_comments(self.current_file, cell_content, self.current_cell)
                    # Queue the question (second to last comment)
                    if len(all_comments) >= 2:
                        self.queue_comment_narration(question, len(all_comments) - 1, is_ai=False)
                    # Queue the AI response (last comment)
                    self.queue_comment_narration(ai_response, len(all_comments), is_ai=True)

            else:
                # Regular comment
                result = self.add_comment(self.current_file, cell_content, self.current_cell, comment_text)
                print(f"DEBUG: Add comment result: {result}")

                # Queue for narration if enabled
                if self.narrate_comments and result:
                    # Get total comments to determine comment number
                    all_comments = self.get_comments(self.current_file, cell_content, self.current_cell)
                    self.queue_comment_narration(comment_text, len(all_comments), is_ai=False)

            print(f"DEBUG: File: {self.current_file}, Cell: {self.current_cell}")
            self.display_comments()
        else:
            print("DEBUG: Comment text was empty")
        return 'break'

    def render_markdown_cell(self, content):
        """Render markdown content for a single cell with basic formatting."""
        import re
        lines = content.split('\n')
        in_code_block = False
        fence_lang = ''

        def insert_inline(text):
            # simple inline parser for `code`, **bold**, *italic*, [text](url)
            code_pat = re.compile(r"`([^`]+)`")
            bold_pat = re.compile(r"\*\*([^*]+)\*\*")
            italic_pat = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")
            link_pat = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

            pos = 0
            while pos < len(text):
                # find earliest of code/bold/italic/link
                candidates = []
                for pat, tag in ((code_pat, 'inline_code'), (bold_pat, 'bold'), (italic_pat, 'italic'), (link_pat, 'link')):
                    m = pat.search(text, pos)
                    if m:
                        candidates.append((m.start(), m, tag))
                if not candidates:
                    self.text_widget.insert(tk.END, text[pos:])
                    break
                candidates.sort(key=lambda x: x[0])
                start, m, tag = candidates[0]
                if start > pos:
                    self.text_widget.insert(tk.END, text[pos:start])
                if tag == 'link':
                    self.text_widget.insert(tk.END, m.group(1), 'link')
                else:
                    self.text_widget.insert(tk.END, m.group(1), tag)
                pos = m.end()

        for line in lines:
            # fenced code
            if line.startswith('```'):
                if not in_code_block:
                    fence_lang = line.strip('`').strip()
                    if fence_lang:
                        self.text_widget.insert(tk.END, fence_lang + '\n', 'code_block')
                    in_code_block = True
                else:
                    in_code_block = False
                continue

            if in_code_block:
                self.text_widget.insert(tk.END, line + '\n', 'code_block')
                continue

            # headings
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                text = line[level:].strip()
                tag = f'h{min(level,6)}'
                self.text_widget.insert(tk.END, text + '\n', tag)
                continue

            # blockquote
            if line.startswith('>'):
                self.text_widget.insert(tk.END, line.lstrip('> ').rstrip() + '\n', 'blockquote')
                continue

            stripped = line.lstrip()
            # unordered list
            if stripped.startswith(('-', '*', '+')):
                bullet_text = '• ' + stripped[1:].lstrip()
                self.text_widget.insert(tk.END, bullet_text + '\n', 'list_item')
                continue
            # ordered list
            if re.match(r"^\s*\d+\.", line):
                self.text_widget.insert(tk.END, line.strip() + '\n', 'list_item')
                continue

            # paragraph spacing on blank lines
            if not line.strip():
                self.text_widget.insert(tk.END, '\n', 'paragraph')
                continue

            # normal text with inline markup
            insert_inline(line + '\n')

    def parse_markdown_cells(self, content):
        """Parse markdown content into cells based on headings"""
        # Safety limit - don't parse files that are too large
        if len(content) > 5 * 1024 * 1024:  # 5MB text limit
            self.cells = ["[File too large to parse into cells - displaying as single block]", content[:100000]]
            return

        lines = content.split('\n')

        # Safety limit on number of lines
        if len(lines) > 50000:
            lines = lines[:50000]

        current_cell = []

        for line in lines:
            if line.startswith('#') and current_cell:
                self.cells.append('\n'.join(current_cell))
                current_cell = [line]
            else:
                current_cell.append(line)

        if current_cell:
            self.cells.append('\n'.join(current_cell))

        if not self.cells:
            self.cells = [content]

        # Limit number of cells to prevent UI freeze
        if len(self.cells) > 1000:
            self.cells = self.cells[:1000] + ["[Remaining cells truncated - file too large]"]

    def parse_paste_cells(self, content):
        """Parse pasted content into cells based on blank line separation"""
        # Safety limit - don't parse files that are too large
        if len(content) > 5 * 1024 * 1024:  # 5MB text limit
            self.cells = ["[File too large to parse into cells - displaying as single block]", content[:100000]]
            return

        # Split by blank lines (2+ consecutive newlines)
        # First, normalize line endings
        content = content.replace('\r\n', '\n').replace('\r', '\n')

        # Split by blank lines (one or more empty lines)
        import re
        blocks = re.split(r'\n\s*\n', content.strip())

        # Filter out empty blocks and create cells with auto-generated headings
        self.cells = []
        for i, block in enumerate(blocks, 1):
            block = block.strip()
            if block:  # Skip empty blocks
                # Add auto-generated heading
                heading = f'# Cell {i}'
                cell_content = f'{heading}\n{block}'
                self.cells.append(cell_content)

        if not self.cells:
            self.cells = [content]

        # Limit number of cells to prevent UI freeze
        if len(self.cells) > 1000:
            self.cells = self.cells[:1000] + ["[Remaining cells truncated - file too large]"]

    def show_paste_dialog(self):
        """Show a dialog to paste content and create a new file"""
        # Create a new top-level window
        dialog = tk.Toplevel(self.root)
        dialog.title("New Paste")
        dialog.geometry("600x400")
        dialog.configure(bg=self.bg_color)

        # Main frame
        main_frame = tk.Frame(dialog, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Instruction label
        label = tk.Label(
            main_frame,
            text="Paste your content below (split by blank lines into cells):",
            bg=self.bg_color,
            fg=self.fg_color,
            font=('Consolas', 10)
        )
        label.pack(fill=tk.X, pady=(0, 5))

        # Text area for pasting
        text_frame = tk.Frame(main_frame, bg=self.border_color)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        paste_text = tk.Text(
            text_frame,
            bg=self.bg_color,
            fg=self.fg_color,
            insertbackground=self.fg_color,
            font=('Consolas', 10),
            wrap=tk.WORD,
            relief=tk.FLAT,
            borderwidth=1
        )
        paste_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = tk.Scrollbar(text_frame, command=paste_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        paste_text.config(yscrollcommand=scrollbar.set)

        # Preview label and frame
        preview_label = tk.Label(
            main_frame,
            text="Preview (how content will be split into cells):",
            bg=self.bg_color,
            fg=self.fg_color,
            font=('Consolas', 9)
        )
        preview_label.pack(fill=tk.X, pady=(0, 5))

        preview_frame = tk.Frame(main_frame, bg=self.border_color, relief=tk.FLAT, borderwidth=1)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        preview_text = tk.Text(
            preview_frame,
            bg=self.bg_color,
            fg=self.fg_color,
            font=('Consolas', 9),
            wrap=tk.WORD,
            relief=tk.FLAT,
            borderwidth=0,
            height=4,
            state=tk.DISABLED
        )
        preview_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        def update_preview(event=None):
            """Update preview as user types"""
            content = paste_text.get('1.0', tk.END).strip()
            preview_text.config(state=tk.NORMAL)
            preview_text.delete('1.0', tk.END)

            if not content:
                preview_text.insert(tk.END, "(paste content to see preview)")
                preview_text.config(state=tk.DISABLED)
                return

            # Parse and show preview
            import re
            blocks = re.split(r'\n\s*\n', content)
            cell_count = len([b for b in blocks if b.strip()])

            preview_lines = [f"Total cells: {cell_count}\n", "---\n"]
            for i, block in enumerate(blocks[:4], 1):
                block = block.strip()
                if block:
                    # Truncate preview
                    preview_block = block[:100]
                    if len(block) > 100:
                        preview_block += "..."
                    preview_lines.append(f"# Cell {i}\n{preview_block}\n---\n")

            preview_text.insert(tk.END, ''.join(preview_lines))
            preview_text.config(state=tk.DISABLED)

        # Bind to text changes
        paste_text.bind('<KeyRelease>', update_preview)

        # Buttons frame
        button_frame = tk.Frame(main_frame, bg=self.bg_color)
        button_frame.pack(fill=tk.X, pady=(0, 0))

        def create_file():
            """Create file from pasted content"""
            content = paste_text.get('1.0', tk.END).strip()
            if not content:
                from tkinter import messagebox
                messagebox.showwarning("Empty Content", "Please paste some content first")
                return

            # Ask user where to save
            try:
                self.root.update_idletasks()
            except Exception:
                pass

            save_path = filedialog.asksaveasfilename(
                title="Save Paste File",
                initialfile="pasted_content.md",
                defaultextension=".md",
                filetypes=[("Markdown", "*.md"), ("Text", "*.txt"), ("All Files", "*.*")]
            )

            if not save_path:
                return  # User cancelled

            try:
                # Parse content into cells
                self.cells = []
                self.parse_paste_cells(content)

                # Reconstruct file content with headings
                file_content = '\n\n'.join(self.cells)

                # Write to file
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(file_content)

                # Close dialog
                dialog.destroy()

                # Open the file in viewer
                self.display_file(save_path)

            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Error", f"Failed to create file: {e}")

        create_button = tk.Button(
            button_frame,
            text="Create File",
            bg=self.button_color,
            fg=self.button_text_color,
            activebackground=self.button_active_color,
            activeforeground=self.button_text_color,
            font=('Consolas', 10, 'bold'),
            relief=tk.RAISED,
            padx=20,
            pady=5,
            cursor='hand2',
            borderwidth=1,
            highlightthickness=0,
            command=create_file
        )
        create_button.pack(side=tk.LEFT, padx=(0, 5))

        cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            bg="#cccccc",
            fg=self.button_text_color,
            activebackground="#aaaaaa",
            activeforeground=self.button_text_color,
            font=('Consolas', 10),
            relief=tk.RAISED,
            padx=20,
            pady=5,
            cursor='hand2',
            borderwidth=1,
            highlightthickness=0,
            command=dialog.destroy
        )
        cancel_button.pack(side=tk.LEFT)

    def display_file(self, file_path):
        """Display file content"""
        # Ensure comment dictation stops when switching files
        self.stop_comment_dictation()
        self.current_comment_reading_index = -1

        self.path_label.config(text=file_path)
        self.current_file = file_path
        self.text_widget.delete('1.0', tk.END)
        self.cells = []
        self.current_cell = 0
        self.viewing_comments = False

        # Save session state when file is opened
        self.save_session_state()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if file_path.endswith('.md'):
                # Ensure text view visible, Python view hidden
                self.show_text_view()
                self.text_widget.tag_configure('h1', font=('Consolas', 18, 'bold'), foreground='#569cd6', spacing3=10)
                self.text_widget.tag_configure('h2', font=('Consolas', 16, 'bold'), foreground='#4ec9b0', spacing3=8)
                self.text_widget.tag_configure('h3', font=('Consolas', 14, 'bold'), foreground='#4ec9b0', spacing3=6)
                self.text_widget.tag_configure('h4', font=('Consolas', 12, 'bold'), foreground='#4ec9b0', spacing3=4)
                self.text_widget.tag_configure('h5', font=('Consolas', 11, 'bold'), foreground='#4ec9b0', spacing3=4)
                self.text_widget.tag_configure('h6', font=('Consolas', 11, 'bold'), foreground='#4ec9b0', spacing3=4)
                self.text_widget.tag_configure('code_block', background='#2d2d2d', foreground='#ce9178', font=('Monaco', 10), lmargin1=16, lmargin2=16, spacing1=2, spacing3=6)
                self.text_widget.tag_configure('blockquote', foreground='#6a9955', lmargin1=20, lmargin2=20)
                self.text_widget.tag_configure('list_item', lmargin1=24, lmargin2=48, spacing1=1, spacing3=1)
                self.text_widget.tag_configure('paragraph', spacing1=2, spacing3=6)
                self.text_widget.tag_configure('inline_code', background='#2d2d2d', foreground='#ce9178', font=('Monaco', 10))
                self.text_widget.tag_configure('bold', font=('Consolas', 11, 'bold'))
                self.text_widget.tag_configure('italic', font=('Consolas', 11, 'italic'))
                self.text_widget.tag_configure('link', foreground='#4aa3ff', underline=True)
                self.text_widget.tag_configure('cell_indicator', foreground='#888888', font=('Consolas', 10))
                self.text_widget.tag_configure('separator', foreground='#444444')
                self.text_widget.tag_configure('comment_hint', foreground='#ffd700')
                self.text_widget.tag_configure('comment_header', foreground='#ffd700', font=('Consolas', 12, 'bold'))
                self.text_widget.tag_configure('comment_number', foreground='#888888', font=('Consolas', 10, 'bold'))
                self.text_widget.tag_configure('comment_text', foreground='#d4d4d4')
                self.text_widget.tag_configure('comment_date', foreground='#666666', font=('Consolas', 9))
                self.text_widget.tag_configure('no_comments', foreground='#888888', font=('Consolas', 10, 'italic'))
                self.text_widget.tag_configure('instructions', foreground='#888888')

                self.parse_markdown_cells(content)

                if self.cells:
                    self.display_current_cell()
            elif file_path.endswith('.py'):
                # Show Python as plain text initially (render outline on demand)
                self.show_text_view()
                self.text_widget.insert('1.0', content)
                # Show render button for Python files
                self.show_python_render_button()
            else:
                self.show_text_view()
                self.text_widget.insert('1.0', content)

        except Exception as e:
            self.text_widget.insert('1.0', f"Error reading file:\n{str(e)}")

    def show_text_view(self):
        """Ensure the plain text/markdown view is visible and Python view hidden."""
        try:
            self.py_frame.pack_forget()
        except Exception:
            pass
        # Show text frame
        if not self.text_frame.winfo_ismapped():
            self.text_frame.pack(fill=tk.BOTH, expand=True)

    def show_python_render_button(self):
        """Show a button to render Python code outline on demand."""
        # Create button frame at the top
        button_frame = tk.Frame(self.text_widget, bg=self.bg_color)
        self.text_widget.window_create('1.0', window=button_frame)

        # Create render button
        render_button = tk.Button(
            button_frame,
            text="📊 Render Code Outline",
            bg=self.button_color,
            fg=self.button_text_color,
            activebackground=self.button_active_color,
            activeforeground=self.button_text_color,
            font=('Consolas', 10, 'bold'),
            relief=tk.RAISED,
            padx=20,
            pady=8,
            cursor='hand2',
            borderwidth=1,
            highlightthickness=0,
            command=self.render_current_python_file
        )
        render_button.pack(pady=5)

        # Add instruction text
        instruction_label = tk.Label(
            button_frame,
            text="Click to parse Python file and show class/function outline",
            bg=self.bg_color,
            fg="#888888",
            font=('Consolas', 9)
        )
        instruction_label.pack(pady=(0, 10))

        # Add separator line
        separator = tk.Frame(button_frame, bg=self.border_color, height=2)
        separator.pack(fill=tk.X, pady=(0, 10))

    def render_current_python_file(self):
        """Parse and render the current Python file's outline view."""
        if not self.current_file or not self.current_file.endswith('.py'):
            return

        try:
            # Check file size first
            file_size = os.path.getsize(self.current_file)

            # Warn about large files (> 500KB)
            if file_size > 500 * 1024:
                self.path_label.config(text=f"⚠️ Large file ({file_size // 1024}KB) - parsing may be slow...")
                self.root.update()
            else:
                self.path_label.config(text="⏳ Parsing Python file...")
                self.root.update()

            # Read the file content
            with open(self.current_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Limit content size to prevent UI freeze (max 2MB of Python code)
            if len(content) > 2 * 1024 * 1024:
                self.text_widget.delete('1.0', tk.END)
                self.text_widget.insert('1.0', f"Python file too large to render outline ({len(content) // 1024}KB).\n\n")
                self.text_widget.insert(tk.END, "Showing first 100 lines of raw code:\n\n")
                lines = content.split('\n')[:100]
                self.text_widget.insert(tk.END, '\n'.join(lines))
                self.path_label.config(text=self.current_file)
                return

            # Call the existing Python view rendering
            self.show_python_view(self.current_file, content)

            # Restore path label after successful render
            self.path_label.config(text=self.current_file)
        except Exception as e:
            # Show error in text view
            self.text_widget.delete('1.0', tk.END)
            self.text_widget.insert('1.0', f"Error rendering Python file:\n{str(e)}")
            self.path_label.config(text=self.current_file)

    def show_python_view(self, file_path, content):
        """Show the Python outline + code viewer for the given file content."""
        # Cache the content to avoid re-reading file on every symbol select
        self._py_current_content = content

        # Hide text view
        try:
            self.text_frame.pack_forget()
        except Exception:
            pass

        # Show python frame if not shown
        if not self.py_frame.winfo_ismapped():
            self.py_frame.pack(fill=tk.BOTH, expand=True)

        # Build or refresh outline
        self.build_python_outline(file_path, content)

    def build_python_outline(self, file_path, content):
        """Parse Python AST and populate the outline tree."""
        import ast
        self.py_outline.delete(*self.py_outline.get_children())
        self.py_text.delete('1.0', tk.END)

        try:
            tree = ast.parse(content)
        except Exception as e:
            self.py_text.insert('1.0', f"Error parsing Python file: {e}")
            return

        lines = content.splitlines()

        # Helper to get end lineno if available
        def get_end_lineno(node):
            return getattr(node, 'end_lineno', getattr(node, 'lineno', 1))

        # Root node
        root_id = self.py_outline.insert('', 'end', text=os.path.basename(file_path), values=("module", 1, len(lines)))

        # Cache docstrings by iid
        self._py_outline_cache.clear()

        # Limit top-level items to prevent UI freeze on huge files
        max_top_level_items = 500
        items_processed = 0

        for node in tree.body:
            if items_processed >= max_top_level_items:
                # Add indicator that outline was truncated
                self.py_outline.insert(root_id, 'end', text=f"... ({len(tree.body) - items_processed} more items truncated)", values=("truncated", 0, 0))
                break
            items_processed += 1
            if isinstance(node, ast.ClassDef):
                doc = ast.get_docstring(node) or ""
                iid = self.py_outline.insert(root_id, 'end', text=f"class {node.name}", values=("class", node.lineno, get_end_lineno(node)))
                self._py_outline_cache[iid] = {"doc": doc, "type": "class"}

                # Limit methods per class to prevent UI freeze
                max_methods_per_class = 100
                methods_processed = 0

                for sub in node.body:
                    if isinstance(sub, ast.FunctionDef) or isinstance(sub, ast.AsyncFunctionDef):
                        if methods_processed >= max_methods_per_class:
                            # Add indicator that methods were truncated
                            remaining = sum(1 for s in node.body if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef))) - methods_processed
                            self.py_outline.insert(iid, 'end', text=f"... ({remaining} more methods truncated)", values=("truncated", 0, 0))
                            break
                        methods_processed += 1

                        sdoc = ast.get_docstring(sub) or ""
                        smark = "async def" if isinstance(sub, ast.AsyncFunctionDef) else "def"
                        sid = self.py_outline.insert(iid, 'end', text=f"{smark} {sub.name}()", values=("method", sub.lineno, get_end_lineno(sub)))
                        self._py_outline_cache[sid] = {"doc": sdoc, "type": "method"}
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                doc = ast.get_docstring(node) or ""
                mark = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
                iid = self.py_outline.insert(root_id, 'end', text=f"{mark} {node.name}()", values=("function", node.lineno, get_end_lineno(node)))
                self._py_outline_cache[iid] = {"doc": doc, "type": "function"}
            elif isinstance(node, ast.Assign):
                # show top-level assignment names
                names = []
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        names.append(t.id)
                if names:
                    text = ", ".join(names)
                    self.py_outline.insert(root_id, 'end', text=f"const {text}", values=("const", node.lineno, get_end_lineno(node)))

        self.py_outline.item(root_id, open=True)
        # Select root by default
        self.py_outline.selection_set(root_id)
        self.on_python_symbol_select(None)

    def on_python_symbol_select(self, event):
        """When a symbol is selected in outline, show docstring and code snippet."""
        sel = self.py_outline.selection()
        if not sel:
            return
        iid = sel[0]
        vals = self.py_outline.item(iid).get('values')
        if not vals or len(vals) < 3:
            return
        node_type, start, end = vals[0], int(vals[1]), int(vals[2])

        # Use cached content instead of re-reading file (major perf improvement!)
        content = getattr(self, '_py_current_content', None)
        if not content:
            # Fallback: read from file if cache not available
            try:
                with open(self.current_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                self.py_text.delete('1.0', tk.END)
                self.py_text.insert('1.0', f"Error reading file: {e}")
                return

        lines = content.splitlines()
        snippet = "\n".join(lines[start-1:end])
        meta = self._py_outline_cache.get(iid, {})
        doc = (meta.get('doc') or '').strip()

        # Render into right text
        self.py_text.delete('1.0', tk.END)
        header = self.py_outline.item(iid).get('text')
        self.py_text.insert(tk.END, f"{header}\n", ('h2',))
        if doc:
            first_line = doc.splitlines()[0]
            self.py_text.insert(tk.END, f"{first_line}\n\n", ('doc',))

        self.py_text.insert(tk.END, snippet, ('code',))

        # Basic styles
        self.py_text.tag_configure('h2', font=('Consolas', 14, 'bold'), foreground='#4ec9b0', spacing3=6)
        self.py_text.tag_configure('doc', foreground='#aaaaaa', font=('Consolas', 10, 'italic'))
        self.py_text.tag_configure('code', font=('Monaco', 10))

        # Optional: simple syntax highlight
        self.syntax_highlight_python()

    def syntax_highlight_python(self):
        """Very simple Python syntax highlighting for the current py_text buffer."""
        import re
        text = self.py_text
        code_start = '1.0'
        # configure tags
        text.tag_configure('kw', foreground='#569cd6')
        text.tag_configure('str', foreground='#ce9178')
        text.tag_configure('com', foreground='#6a9955')
        # keywords
        keywords = r"\b(False|class|finally|is|return|None|continue|for|lambda|try|True|def|from|nonlocal|while|and|del|global|not|with|as|elif|if|or|yield|assert|else|import|pass|break|except|in|raise)\b"
        content = text.get('1.0', tk.END)
        # clear previous tags
        for tag in ('kw','str','com'):
            text.tag_remove(tag, '1.0', tk.END)
        # strings
        for m in re.finditer(r"(?s)('''.*?'''|\"\"\".*?\"\"\"|'[^'\n]*'|\"[^\"\n]*\")", content):
            start = f"1.0+{m.start()}c"
            end = f"1.0+{m.end()}c"
            text.tag_add('str', start, end)
        # comments
        for m in re.finditer(r"#[^\n]*", content):
            start = f"1.0+{m.start()}c"
            end = f"1.0+{m.end()}c"
            text.tag_add('com', start, end)
        # keywords (after strings/comments to avoid coloring inside)
        for m in re.finditer(keywords, content):
            start = f"1.0+{m.start()}c"
            end = f"1.0+{m.end()}c"
            # Skip if inside a string/comment tag
            ranges = text.tag_ranges('str') + text.tag_ranges('com')
            inside = False
            for i in range(0, len(ranges), 2):
                if text.compare(start, '>=', ranges[i]) and text.compare(end, '<=', ranges[i+1]):
                    inside = True
                    break
            if not inside:
                text.tag_add('kw', start, end)


def main():
    root = tk.Tk()
    app = FileViewer(root)

    def on_closing():
        app.save_session_state()
        app.save_navigation_state()
        app.conn.close()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == '__main__':
    main()
