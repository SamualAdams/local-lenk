"""Navigation state persistence mixin."""

import json
from typing import Optional


class NavigationStateMixin:
    """Adds tree/favorites expansion persistence to the viewer."""

    tree_state_save_job = None
    tree_open_paths = set()
    tree_selected_path: Optional[str] = None
    favorites_open_paths = set()
    favorites_selected_path: Optional[str] = None

    def load_navigation_state(self) -> None:
        try:
            tree_state_raw = self.get_setting('tree_state')
            if tree_state_raw:
                state = json.loads(tree_state_raw)
                self.tree_open_paths = set(state.get('open_paths', []))
                self.tree_selected_path = state.get('selected_path')
        except (ValueError, TypeError):
            self.tree_open_paths = set()
            self.tree_selected_path = None

        try:
            fav_state_raw = self.get_setting('favorites_state')
            if fav_state_raw:
                state = json.loads(fav_state_raw)
                self.favorites_open_paths = set(state.get('open_paths', []))
                self.favorites_selected_path = state.get('selected_path')
        except (ValueError, TypeError):
            self.favorites_open_paths = set()
            self.favorites_selected_path = None

    def save_navigation_state(self) -> None:
        if self.tree_state_save_job is not None:
            self.root.after_cancel(self.tree_state_save_job)
            self.tree_state_save_job = None

        tree_open = self.collect_open_paths(self.tree)
        favorites_open = self.collect_open_paths(self.favorites_tree)
        tree_selected = self.get_selected_path(self.tree)
        favorites_selected = self.get_selected_path(self.favorites_tree)

        self.tree_open_paths = set(tree_open)
        self.tree_selected_path = tree_selected
        self.favorites_open_paths = set(favorites_open)
        self.favorites_selected_path = favorites_selected

        self.save_setting('tree_state', json.dumps({
            'open_paths': tree_open,
            'selected_path': tree_selected
        }))
        self.save_setting('favorites_state', json.dumps({
            'open_paths': favorites_open,
            'selected_path': favorites_selected
        }))

    def collect_open_paths(self, tree):
        open_paths = []
        nodes_to_check = list(tree.get_children(''))

        while nodes_to_check:
            node = nodes_to_check.pop()
            item = tree.item(node)
            values = item.get('values')

            if item.get('open') and values:
                open_paths.append(values[0])
                nodes_to_check.extend(tree.get_children(node))

        return open_paths

    def get_selected_path(self, tree):
        selection = tree.selection()
        if not selection:
            return None
        values = tree.item(selection[0]).get('values')
        return values[0] if values else None

    def restore_navigation_state(self) -> None:
        self.restore_tree_selection(self.tree, self.tree_selected_path)
        self.restore_tree_selection(self.favorites_tree, self.favorites_selected_path)

    def restore_tree_selection(self, tree, target_path: Optional[str]) -> None:
        if not target_path:
            return

        node = self.find_node_by_path(tree, target_path)
        if node:
            tree.selection_set(node)
            tree.focus(node)
            tree.see(node)

    def find_node_by_path(self, tree, target_path: Optional[str]):
        if not target_path:
            return None

        stack = list(tree.get_children(''))
        while stack:
            node = stack.pop()
            values = tree.item(node).get('values')
            if values and values[0] == target_path:
                return node
            stack.extend(tree.get_children(node))

        return None

    def schedule_navigation_state_save(self) -> None:
        if self.tree_state_save_job is not None:
            self.root.after_cancel(self.tree_state_save_job)
        self.tree_state_save_job = self.root.after(500, self._navigation_state_save_job)

    def _navigation_state_save_job(self) -> None:
        self.tree_state_save_job = None
        self.save_navigation_state()
