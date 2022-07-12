from PySide6.QtWidgets import QLabel, QLineEdit
from PySide6.QtGui import QFontMetrics
from PySide6.QtCore import Qt, Signal

class LineEdit(QLineEdit):
    commit = Signal(str, str)

    max_chars = 50

    def __init__(self, key, value):
        super().__init__()
        self.key = key
        self.setText(value)

    def sizeHint(self):
        size = super().sizeHint()
        text_width = QFontMetrics(self.font()).horizontalAdvance(self.text()[:self.max_chars])
        size.setWidth(text_width + 10)
        return size

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.commit.emit(self.key, self.text())
        else:
            super().keyPressEvent(event)


class Field:
    editable = True

    def __init__(self, key, value, keybind=None, commit_cb=None):
        self.key = key
        self.value = value
        self.keybind = keybind
        self.commit_cb = commit_cb
        self.label = self.make_label()
        self.box = self.make_box()

    def make_label(self):
        label = QLabel()
        text = self.key.title()
        if self.keybind:
            idx = text.upper().find(self.keybind)
            text = text[:idx] + '<u>%s</u>' % text[idx] + text[idx+1:]
        label.setText(text)
        return label

    def make_box(self):
        raise NotImplementedError()


class ReadOnlyField(Field):
    editable = False

    def make_box(self):
        label = QLabel()
        label.setText(self.value)
        return label


class TextField(Field):
    def make_box(self):
        box = LineEdit(self.key, self.value)
        return box
