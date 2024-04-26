import os

from PySide6.QtWidgets import QLineEdit, QCompleter
from PySide6.QtCore import Qt, Signal


class LineEdit(QLineEdit):
    def __init__(self, text='', read_only=False, update_cb=None, commit_cb=None):
        super().__init__()
        self.update_cb = update_cb
        self.commit_cb = commit_cb
        self.setFocusPolicy(Qt.ClickFocus) # We don't want <TAB> to jump between fields
        self.setText(text)
        self.setStyleSheet('QLineEdit[readOnly="true"] {background-color: #E0E0E0;}')
        if read_only:
            self.setReadOnly(True)
        self.textChanged.connect(self.update_cb)

    def get_value(self):
        return self.text()

    def set_value(self, text):
        self.setText(text)

    def set_property(self, key, value):
        self.setProperty(key, value)
        self.setStyleSheet("/* /") # force stylesheet recalc

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # Normally a QLineEdit will pass the <Enter> key event up
            # to its parent, which we don't want, so swallow it here.
            self.commit_cb()
        else:
            super().keyPressEvent(event)


class TabCompleteLineEdit(LineEdit):
    tab_complete = Signal(str)

    def __init__(self, completions, **kwargs):
        super().__init__(**kwargs)
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
