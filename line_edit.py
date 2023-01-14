import os

from PySide6.QtWidgets import QLineEdit, QCompleter
from PySide6.QtCore import Qt, Signal

import keys


class LineEdit(QLineEdit):
    commit = Signal(str, object)
    updated = Signal(str, object)
    tab_complete = Signal(str)

    def __init__(self, initial_value=None, read_only=False, ctx=None, commit_cb=None):
        super().__init__()
        # Disable scrolling between fields with <TAB> as we want to define custom behaviour for it
        self.setFocusPolicy(Qt.ClickFocus)
        if initial_value is not None:
            self.setText(initial_value)
        self.setStyleSheet('QLineEdit[readOnly="true"] {background-color: #E0E0E0;}')
        if read_only:
            self.setReadOnly(True)
        self.ctx = ctx
        if commit_cb:
            self.commit.connect(commit_cb)
        self.textChanged.connect(self._update)

    def _commit(self):
        self.commit.emit(self.text(), self.ctx)

    def _update(self):
        self.updated.emit(self.text(), self.ctx)

    def focusOutEvent(self, event):
        self._commit()
        super().focusOutEvent(event)

    def keyPressEvent(self, event):
        if keys.get_action(event) == 'select':
            # Normally a QLineEdit will pass the <Enter> key event up
            # to its parent, which we don't want, so swallow it here.
            self.clearFocus()
        else:
            super().keyPressEvent(event)



class TabCompleteLineEdit(LineEdit):
    def __init__(self, *args, **kwargs):
        completions = kwargs.pop('completions', [])
        super().__init__(*args, **kwargs)
        self.completions = completions
        self.setCompleter(QCompleter(completions))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Tab:
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
