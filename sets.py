import os

from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QLineEdit, QCompleter
from PySide6.QtCore import Qt, Signal

from grid import FlowLayout
from line_edit import TabCompleteLineEdit
import keys


class TextBox(TabCompleteLineEdit):
    push_value = Signal(str)
    pop_value = Signal()

    def __init__(self, completions):
        super().__init__(initial_value='', completions=completions)
        self.setMinimumWidth(self.sizeHint().width())
        self.tab_complete.connect(self.push_value)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Backspace and not self.text():
            self.pop_value.emit()
            if event.modifiers() == Qt.ControlModifier:
                self.setText("")
        elif key == Qt.Key_Space:
            if self.text():
                self.push_value.emit(self.text())
        else:
            super().keyPressEvent(event)


class ValueBox(QLabel):
    clicked = Signal(QLabel)

    def __init__(self, value):
        super().__init__()
        self.setObjectName("ValueBox")
        self.value = value
        self.setText(value)
        self.setContentsMargins(3, 3, 3, 3)

    def mousePressEvent(self, event):
        self.clicked.emit(self)


class SetPicker(QWidget):
    commit = Signal(list)

    def __init__(self, values, completions):
        super().__init__()
        self.boxes = []
        self.text = TextBox(completions)
        self.text.push_value.connect(self.push_value)
        self.text.pop_value.connect(self.pop_value)
        self.text.commit.connect(self._commit)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        layout.addWidget(self.text)
        for value in values:
            self.add_box(ValueBox(value))

    def _commit(self, text):
        if text:
            self.push_value(text)
        self.commit.emit([box.value for box in self.boxes])

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
        # Reposition completer to match resized self.text
        completer = self.text.completer()
        self.text.setCompleter(None)
        self.text.setCompleter(completer)

    def pop_value(self):
        if self.boxes:
            box = self.remove_box(self.boxes[-1])
            self.text.setText(box.value)

    def box_clicked(self, box):
        self.remove_box(box)
        self.text.setFocus()
