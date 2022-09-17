import os

from PySide6.QtWidgets import QDialog, QWidget, QGridLayout, QVBoxLayout
from PySide6.QtWidgets import QLabel, QLineEdit, QCompleter
from PySide6.QtGui import QFontMetrics, QPalette
from PySide6.QtCore import Qt, Signal

from sets import SetPicker
import keys


class FieldDialog(QDialog):
    title = "Dialog"

    def __init__(self, main_window):
        super().__init__(main_window)
        self.setWindowTitle(self.title)
        self.main_window = main_window
        self.setLayout(QVBoxLayout())
        self.field_list = FieldList()
        self.field_list.field_committed.connect(self.field_committed)
        self.layout().addWidget(self.field_list)
        self.layout = None
        self.need_reload = False

    def init_fields(self, fields):
        self.field_list.init_fields(fields)
        self.field_list.setFocus()

    def field_committed(self, field, value):
        pass

    def reload(self):
        self.main_window.reload_tree()

    def accept(self):
        if self.need_reload:
            self.reload()
        super().accept()

    def keyPressEvent(self, event):
        if keys.get_action(event) == 'select':
            self.accept()
        else:
            event.ignore()


class FieldList(QWidget):
    field_committed = Signal(object, object)

    def __init__(self):
        super().__init__()
        self.fields = {}
        self.keybinds = {}

    def init_fields(self, fields):
        if self.layout():
            QWidget().setLayout(self.layout()) # purge existing layout and fields
        self.setLayout(QGridLayout())
        self.fields = {}
        self.keybinds = {}
        for row_i, field in enumerate(fields):
            self.fields[field.key] = field
            if field.keybind:
                self.keybinds[Qt.Key.values['Key_' + field.keybind]] = field.box
            self.layout().addWidget(field.label, row_i, 0)
            self.layout().addWidget(field.box, row_i, 1)
            if field.editable:
                field.box.commit.connect(self._field_committed)
        self.layout().setRowStretch(row_i + 1, 1)

    def _field_committed(self, key, value):
        self.setFocus()
        self.field_committed.emit(self.fields[key], value)

    def keyPressEvent(self, event):
        key = event.key()
        if key in self.keybinds:
            self.keybinds[key].setFocus()
        else:
            event.ignore()


class LineEdit(QLineEdit):
    commit = Signal(object, str)

    max_chars = 50

    def __init__(self, key, value, validator=None, normalizer=None):
        super().__init__()
        # Disable scrolling between fields with <TAB> as we want
        # to use it for tab-completion within some fields
        self.setFocusPolicy(Qt.ClickFocus)
        self.key = key
        self.validator = validator
        self.normalizer = normalizer
        self.valid = True
        self.setText(value)
        self.textChanged.connect(self.text_update)

    def sizeHint(self):
        size = super().sizeHint()
        text_width = QFontMetrics(self.font()).horizontalAdvance(self.text()[:self.max_chars])
        size.setWidth(text_width + 10)
        return size

    def text_update(self, value):
        self.valid = self.validator(value) if (self.validator and value) else True
        self.set_bg_color()

    def set_bg_color(self):
        palette = self.palette()
        palette.setColor(QPalette.Text, Qt.black if self.valid else Qt.red)
        self.setPalette(palette)

    def keyPressEvent(self, event):
        if keys.get_action(event) == 'select':
            if self.valid and self.normalizer:
                self.setText(self.normalizer(self.text()))
            elif not self.valid:
                self.setText('')
            self.commit.emit(self.key, self.text())
        else:
            super().keyPressEvent(event)


class Field:
    editable = True

    def __init__(self, key, value, keybind=None, commit_cb=None):
        self.key = key
        self.value = value
        self.keybind = keybind.upper() if keybind else None
        self.commit_cb = commit_cb
        self.label = self.make_label()
        self.box = self.make_box()

    def make_label(self):
        label = QLabel()
        text = self.key.replace('_', ' ').title()
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
    def __init__(self, *args, **kwargs):
        self.validator = kwargs.pop('validator', None)
        self.normalizer = kwargs.pop('normalizer', None)
        super().__init__(*args, **kwargs)

    def make_box(self):
        box = LineEdit(self.key, self.value, validator=self.validator, normalizer=self.normalizer)
        return box


class SetField(Field):
    def __init__(self, key, values, all_values, **kwargs):
        self.all_values = all_values
        super().__init__(key, values, **kwargs)

    def make_box(self):
        return SetPicker(self.key, self.value, self.all_values)
