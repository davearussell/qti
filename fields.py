from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtWidgets import QLabel, QComboBox
from PySide6.QtCore import Qt, Signal

from sets import SetPicker
from line_edit import TabCompleteLineEdit, ValidatedLineEdit


class FieldList(QWidget):
    field_updated = Signal()
    field_unfocused = Signal(object)

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
            field.unfocus.connect(self.handle_unfocus)
            field.updated.connect(self.field_updated)
        self.layout().addStretch(1)

    def handle_unfocus(self, field):
        self.setFocus()
        self.field_unfocused.emit(field)

    def keyPressEvent(self, event):
        key = event.key()
        if key in self.keybinds:
            self.keybinds[key].setFocus()
        else:
            event.ignore()


class Field(QWidget):
    unfocus = Signal(object)
    updated = Signal()

    def __init__(self, key, value, keybind=None, keymap=None):
        super().__init__()
        self.key = key
        self.original_value = value
        if keymap:
            assert keybind is None, (keybind, keymap)
            self.keybind = keymap.assign_keybind(self.key)
        else:
            self.keybind = keybind.upper() if keybind else None
        self.label = self.make_label()
        self.body = self.make_body()
        self.set_value(value)
        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.label)
        layout.addWidget(self.body)
        layout.setContentsMargins(0, 0, 0, 0)

    def focusInEvent(self, event):
        self.body.setFocus()

    def dirty(self):
        return self.get_value() != self.original_value

    def mark_clean(self):
        self.original_value = self.get_value()

    def make_label(self):
        label = QLabel()
        text = self.key.replace('_', ' ').title()
        if self.keybind:
            idx = text.upper().find(self.keybind)
            text = text[:idx] + '<u>%s</u>' % text[idx] + text[idx+1:]
        label.setText(text)
        return label

    def done(self):
        self.unfocus.emit(self)

    def make_body(self):
        raise NotImplementedError()

    def get_value(self):
        raise NotImplementedError()

    def set_value(self, value):
        raise NotImplementedError()


class EnumField(Field):
    def __init__(self, key, value, values, **kwargs):
        self.values = values
        super().__init__(key, value, **kwargs)

    def make_body(self):
        box = QComboBox()
        box.setFocusPolicy(Qt.NoFocus)
        for value in self.values:
            box.addItem(value)
        return box

    def get_value(self):
        return self.body.currentText()

    def set_value(self, value):
        assert value in self.values, value
        self.body.setCurrentText(value)


class TextField(Field):
    edit_cls = TabCompleteLineEdit

    def __init__(self, key, value, completions=None, **kwargs):
        self.edit_args = {} if completions is None else {'completions': completions}
        super().__init__(key, value, **kwargs)

    def make_body(self):
        box = self.edit_cls(**self.edit_args)
        box.commit.connect(self.done)
        box.textChanged.connect(self.updated)
        return box

    def get_value(self):
        return self.body.text()

    def set_value(self, value):
        self.body.setText(value)


class ValidatedTextField(TextField):
    edit_cls = ValidatedLineEdit

    def get_value(self):
        return super().get_value() if self.body.valid else self.original_value

    def done(self):
        if not self.body.valid:
            self.set_value(self.original_value)
        super().done()


class ReadOnlyField(TextField):
    def make_body(self):
        return QLabel()


class SetField(TextField):
    edit_cls = SetPicker

    def get_value(self):
        return self.body.get_value()

    def set_value(self, value):
        self.body.set_value(value)
