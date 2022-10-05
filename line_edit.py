import os

from PySide6.QtWidgets import QLineEdit, QCompleter
from PySide6.QtCore import Qt, Signal

import keys


class LineEdit(QLineEdit):
    commit = Signal(str)
    tab_complete = Signal(str)

    def __init__(self, initial_value=None, completions=None):
        super().__init__()
        # Disable scrolling between fields with <TAB> as we want
        # to use it for tab-completion within some fields
        self.setFocusPolicy(Qt.ClickFocus)
        if initial_value is not None:
            self.setText(initial_value)
        self.completions = completions
        if completions is not None:
            self.setCompleter(QCompleter(completions))

    def _commit(self):
        self.commit.emit(self.text())

    def keyPressEvent(self, event):
        if keys.get_action(event) == 'select':
            # Normally a QLineEdit will pass the <Enter> key event up
            # to its parent, which we don't want, so swallow it here.
            self._commit()
        elif event.key() == Qt.Key_Tab and self.completions is not None:
            matches = [value for value in self.completions if value.startswith(self.text())]
            if matches:
                text = os.path.commonprefix(matches)
                self.setText(text)
                if not text: # Pop up all possible completions on <Tab> in an empty text box
                    self.completer().setCompletionPrefix('')
                    self.completer().complete()
                if len(matches) == 1:
                    self.tab_complete.emit(matches[0])
        else:
            super().keyPressEvent(event)
