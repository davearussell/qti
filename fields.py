from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, Signal

from sets import SetPicker
from line_edit import TabCompleteLineEdit
import keys


class FieldList(QWidget):
    field_committed = Signal(object, object)

    def __init__(self):
        super().__init__()
        self.fields = {}
        self.keybinds = {}

    def init_fields(self, fields):
        if self.layout():
            QWidget().setLayout(self.layout()) # purge existing layout and fields
        self.setLayout(QVBoxLayout())
        self.fields = {}
        self.keybinds = {}
        width = max(field.label.sizeHint().width() for field in fields)
        for row_i, field in enumerate(fields):
            field.label.setFixedWidth(width)
            self.fields[field.key] = field
            if field.keybind:
                self.keybinds[getattr(Qt.Key, 'Key_' + field.keybind)] = field
            self.layout().addWidget(field)
            field.commit.connect(self._field_committed)
        self.layout().addStretch(1)

    def _field_committed(self, field, value):
        self.setFocus()
        self.field_committed.emit(field, value)

    def keyPressEvent(self, event):
        key = event.key()
        if key in self.keybinds:
            self.keybinds[key].setFocus()
        else:
            event.ignore()


class Field(QWidget):
    commit = Signal(object, object)

    def __init__(self, key, value, keybind=None, keymap=None):
        super().__init__()
        self.key = key
        if keymap:
            assert keybind is None, (keybind, keymap)
            self.keybind = keymap.assign_keybind(self.key)
        else:
            self.keybind = keybind.upper() if keybind else None
        self.label = self.make_label()
        self.body = self.make_body(value)
        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.label)
        layout.addWidget(self.body)
        layout.setContentsMargins(0, 0, 0, 0)

    def focusInEvent(self, event):
        self.body.setFocus()

    def make_label(self):
        label = QLabel()
        text = self.key.replace('_', ' ').title()
        if self.keybind:
            idx = text.upper().find(self.keybind)
            text = text[:idx] + '<u>%s</u>' % text[idx] + text[idx+1:]
        label.setText(text)
        return label

    def commit_value(self, value):
        self.commit.emit(self, value)

    def make_body(self):
        raise NotImplementedError()

    def set_value(self, value):
        print(type(self), self.key, value)
        raise NotImplementedError()


class ReadOnlyField(Field):
    def make_body(self, value):
        label = QLabel()
        label.setText(value)
        return label

    def set_value(self, value):
        self.body.setText(value)


class TextField(Field):
    edit_cls = TabCompleteLineEdit

    def __init__(self, key, value, completions=None, **kwargs):
        self.edit_args = {} if completions is None else {'completions': completions}
        super().__init__(key, value, **kwargs)

    def make_body(self, value):
        box = self.edit_cls(value, **self.edit_args)
        box.commit.connect(self.commit_value)
        return box

    def set_value(self, value):
        self.body.setText(value)


class SetField(TextField):
    edit_cls = SetPicker
