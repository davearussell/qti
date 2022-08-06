import os

from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QLineEdit, QCompleter
from PySide6.QtGui import QPalette
from PySide6.QtCore import Qt, Signal

from grid import FlowLayout


class TextBox(QLineEdit):
    commit = Signal()
    push_value = Signal(str)
    pop_value = Signal()

    def __init__(self, completions):
        super().__init__()
        self.setFocusPolicy(Qt.ClickFocus)
        self.completions = completions
        self._completer = QCompleter(self.completions)
        self.setCompleter(self._completer)

    def _commit(self):
        if self.text():
            self.push_value.emit(self.text())
        self.commit.emit()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)

    def keyPressEvent(self, event):
        self.setCompleter(self._completer)
        key = event.key()
        if key == Qt.Key_Backspace and not self.text():
            self.pop_value.emit()
            if event.modifiers() == Qt.ControlModifier:
                self.setText("")
        elif key == Qt.Key_Tab:
            matches = [value for value in self.completions if value.startswith(self.text())]
            self.setText(os.path.commonprefix(matches))
        elif key == Qt.Key_Space:
            if self.text():
                self.push_value.emit(self.text())
        elif key == Qt.Key_Return:
            self._commit()
        else:
            super().keyPressEvent(event)


class ValueBox(QLabel):
    clicked = Signal(QLabel)

    def __init__(self, value):
        super().__init__()
        self.value = value
        self.setText(value)
        self.setContentsMargins(3, 3, 3, 3)
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, Qt.white)
        self.setPalette(palette)

    def mousePressEvent(self, event):
        self.clicked.emit(self)


class SetPicker(QWidget):
    commit = Signal(str, list)

    def __init__(self, key, values, all_values):
        super().__init__()
        self.key = key
        self.boxes = []
        self.text = TextBox(all_values)
        self.text.push_value.connect(self.push_value)
        self.text.pop_value.connect(self.pop_value)
        self.text.commit.connect(self._commit)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        layout.addWidget(self.text)
        for value in values:
            self.add_box(ValueBox(value))

    def _commit(self):
        self.commit.emit(self.key, [box.value for box in self.boxes])

    def add_box(self, box):
        box.clicked.connect(self.box_clicked)
        self.boxes.append(box)
        self.layout().insertWidget(self.layout().count() - 1, box)

    def remove_box(self, box):
        self.boxes.remove(box)
        box.hide()
        self.layout().removeWidget(box)
        return box

    def focusInEvent(self, event):
        self.text.setFocus()

    def push_value(self, value):
        self.add_box(ValueBox(value))
        self.text.setText('')
        self.text.setCompleter(None)

    def pop_value(self):
        if self.boxes:
            box = self.remove_box(self.boxes[-1])
            self.text.setText(box.value)

    def box_clicked(self, box):
        self.remove_box(box)
        self.text.setFocus()
