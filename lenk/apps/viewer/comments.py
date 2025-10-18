"""Comment and narration helpers."""

import subprocess
from typing import Optional


class CommentAudioMixin:
    """Provides comment reading, narration, and clipboard helpers."""

    dictation_process: Optional[subprocess.Popen] = None
    narration_process: Optional[subprocess.Popen] = None

    def stop_comment_dictation(self, event=None):
        """Stop any ongoing comment dictation."""
        if self.dictation_process:
            if self.dictation_process.poll() is None:
                try:
                    self.dictation_process.terminate()
                except Exception as exc:  # pylint: disable=broad-except
                    print(f"Dictation termination error: {exc}")
            self.dictation_process = None
            self.current_comment_reading_index = -1

            if self.current_file:
                self.path_label.config(text=self.current_file)

        return 'break'

    def read_previous_comment(self, event):
        return self._read_comment(direction=-1)

    def read_next_comment(self, event):
        return self._read_comment(direction=1)

    def _read_comment(self, direction: int):
        if not self.current_file or not self.current_file.endswith('.md') or not self.cells:
            return 'break'

        if self.dictation_process and self.dictation_process.poll() is None:
            try:
                self.dictation_process.terminate()
            except Exception as exc:  # pylint: disable=broad-except
                print(f"Dictation termination error: {exc}")
        self.dictation_process = None

        cell_content = self.cells[self.current_cell]
        comments = self.get_comments(self.current_file, cell_content, self.current_cell)

        if not comments:
            self.path_label.config(text="No comments for this cell")

            def reset_label():
                self.path_label.config(text=self.current_file)

            self.root.after(2000, reset_label)
            self.current_comment_reading_index = -1
            return 'break'

        if self.current_comment_reading_index == -1:
            target_index = 0 if direction >= 0 else len(comments) - 1
        else:
            target_index = (self.current_comment_reading_index + direction) % len(comments)

        self.current_comment_reading_index = target_index

        comment_text, created_at, confidence = comments[target_index]
        comment_number = target_index + 1
        confidence_note = "This comment may be outdated. " if confidence == 'fuzzy' else ""
        text_to_read = f"Comment {comment_number}. {confidence_note}{comment_text}"

        try:
            self.dictation_process = subprocess.Popen(
                ['say', '-r', str(self.voice_speed), text_to_read],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            self.path_label.config(text=f"🔊 Reading comment {comment_number} of {len(comments)}")

            def reset_label():
                self.path_label.config(text=self.current_file)

            self.root.after(3000, reset_label)
            self.root.after(100, self.check_comment_dictation_status)

        except Exception as exc:  # pylint: disable=broad-except
            print(f"Comment reading error: {exc}")

        return 'break'

    def copy_current_cell(self):
        if not self.current_file or not self.cells:
            return

        cell_content = self.cells[self.current_cell]
        comments = self.get_comments(self.current_file, cell_content, self.current_cell)

        lines = [
            f"File: {self.current_file}",
            f"Cell: {self.current_cell + 1} of {len(self.cells)}",
            "",
            "Content:",
            cell_content.strip() or "(empty)",
            ""
        ]

        if comments:
            lines.append("Comments:")
            for idx, (comment_text, created_at, confidence) in enumerate(comments, 1):
                status = " [may be outdated]" if confidence == 'fuzzy' else ""
                lines.append(f"{idx}. {comment_text}{status}")
                lines.append(f"   Added: {created_at}")
            lines.append("")
        else:
            lines.append("Comments: None")

        payload = '\n'.join(lines)

        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(payload)
            self.root.update()
            if self.current_file:
                self.path_label.config(text="📋 Cell copied to clipboard")

                def reset_label():
                    self.path_label.config(text=self.current_file)

                self.root.after(2000, reset_label)
        except Exception as exc:  # pylint: disable=broad-except
            print(f"Clipboard error: {exc}")

    def check_comment_dictation_status(self):
        if self.dictation_process and self.dictation_process.poll() is None:
            self.root.after(100, self.check_comment_dictation_status)
        else:
            self.dictation_process = None

    # Narration ---------------------------------------------------------
    def toggle_narration(self):
        self.narrate_comments = not self.narrate_comments

        if not self.narrate_comments:
            self.stop_narration()
            self.narration_queue = []

        self.display_comments()

    def stop_narration(self):
        if self.narration_process:
            self.narration_process.terminate()
            self.narration_process = None
        self.is_narrating = False

    def queue_comment_narration(self, comment_text, comment_number, is_ai=False):
        if not self.narrate_comments:
            return

        self.narration_queue.append({
            'text': comment_text,
            'number': comment_number,
            'is_ai': is_ai
        })

        if not self.is_narrating:
            self.process_narration_queue()

    def process_narration_queue(self):
        if not self.narration_queue or not self.narrate_comments:
            self.is_narrating = False
            return

        comment_data = self.narration_queue.pop(0)
        self.is_narrating = True

        self.narrate_single_comment(
            comment_data['text'],
            comment_data['number'],
            comment_data['is_ai']
        )

    def narrate_single_comment(self, comment_text, comment_number, is_ai=False):
        intro = "A I response. [[slnc 800]]" if is_ai else f"Comment {comment_number}. [[slnc 800]]"

        base_speed = 200
        pause_ms = int(1500 * (base_speed / self.voice_speed))
        full_text = f"{intro} {comment_text} [[slnc {pause_ms}]]"

        try:
            self.narration_process = subprocess.Popen(
                ['say', '-r', str(self.voice_speed), full_text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            if is_ai:
                self.path_label.config(text=f"🔊 Narrating AI response...")
            else:
                self.path_label.config(text=f"🔊 Narrating comment {comment_number}")

            self.root.after(100, self.check_narration_status)
        except Exception as exc:  # pylint: disable=broad-except
            print(f"Narration error: {exc}")
            self.is_narrating = False
            self.root.after(100, self.process_narration_queue)

    def check_narration_status(self):
        if self.narration_process and self.narration_process.poll() is None:
            self.root.after(100, self.check_narration_status)
        else:
            self.narration_process = None
            self.is_narrating = False

            def reset_label():
                if self.current_file:
                    self.path_label.config(text=self.current_file)

            self.root.after(100, reset_label)
            self.root.after(200, self.process_narration_queue)

