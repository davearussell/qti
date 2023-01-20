import os

from PySide6.QtWidgets import QLineEdit, QCompleter
from PySide6.QtCore import Qt, Signal


class LineEdit(QLineEdit):
    commit = Signal(str, object)
    updated = Signal(str, object)
    tab_complete = Signal(str)

    def __init__(self, initial_value=None, read_only=False, ctx=None, commit_on_unfocus=True,
                 commit_cb=None):
        super().__init__()
        self.commit_on_unfocus = commit_on_unfocus
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
        if self.commit_on_unfocus:
            self._commit()
        super().focusOutEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # Normally a QLineEdit will pass the <Enter> key event up
            # to its parent, which we don't want, so swallow it here.
            if not self.commit_on_unfocus:
                self._commit()
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


class ValidatedLineEdit(LineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.textChanged.connect(self.check_valid)
        self.valid = True

    def check_valid(self, value):
        self.valid = self.is_valid(value)
        self.setProperty("valid", self.valid)
        self.setStyleSheet("/* /") # force stylesheet recalc

    def is_valid(self, text):
        try:
            self.normalise(self.text())
            return True
        except:
            return False

    def try_normalise(self):
        try:
            self.setText(self.normalise(self.text()))
        except:
            self.setText('')
            self.valid = False

    def _commit(self):
        self.try_normalise()
        super()._commit()

    def normalise(self, value):
        raise NotImplementedError()
