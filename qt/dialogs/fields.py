from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtWidgets import QLabel, QComboBox
from PySide6.QtCore import Qt, Signal

from qt.keys import event_keystroke
from qt.line_edit import LineEdit, TabCompleteLineEdit
from qt.set_picker import SetPicker
from qt.color_picker import ColorPicker


class FieldGroupWidget(QWidget):
    def __init__(self, keystroke_cb):
        super().__init__()
        self.keystroke_cb = keystroke_cb
        self.fields = []
        self.keybinds = {}

    def set_fields(self, fields):
        if self.layout():
            QWidget().setLayout(self.layout()) # purge existing layout and fields
        self.setLayout(QVBoxLayout())
        width = max(field.label.sizeHint().width() for field in fields)
        for row_i, field in enumerate(fields):
            field.label.setFixedWidth(width)
            self.layout().addWidget(field)
        self.layout().addStretch(1)
        self.fields = fields

    def focus(self):
        self.setFocus()

    def keyPressEvent(self, event):
        if not self.keystroke_cb(event_keystroke(event)):
            event.ignore()


class FieldWidget(QWidget):
    body_cls = None
    body_args = {}

    def __init__(self, key, update_cb, commit_cb):
        super().__init__()
        self.key = key
        self.update_cb = update_cb
        self.commit_cb = commit_cb
        self.label = QLabel()
        self.set_keybind(None)
        self.body = self.make_body()
        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.label)
        layout.addWidget(self.body)
        layout.setContentsMargins(0, 0, 0, 0)

    def set_keybind(self, keybind):
        self.keybind = keybind
        text = self.key.replace('_', ' ').title()
        if self.keybind:
            idx = text.lower().find(self.keybind)
            text = text[:idx] + '<u>%s</u>' % text[idx] + text[idx+1:]
        self.label.setText(text)

    def focus(self):
        self.setFocus()

    def focusInEvent(self, event):
        self.body.setFocus()

    def done(self):
        self.unfocus.emit(self)

    @property
    def common_body_args(self):
        return {
            'update_cb': self.update_cb,
            'commit_cb': self.commit_cb,
        }

    def make_body(self):
        return self.body_cls(**(self.common_body_args | self.body_args))

    def get_value(self):
        return self.body.get_value()

    def set_value(self, value):
        self.body.set_value(value)

    def post_commit_cb(self):
        pass


class TextFieldWidget(FieldWidget):
    body_cls = TabCompleteLineEdit

    def __init__(self, completions=None, read_only=False, **kwargs):
        self.body_args = {'completions': completions, 'read_only': read_only}
        super().__init__(**kwargs)


class SetFieldWidget(TextFieldWidget):
    body_cls = SetPicker


class ValidatedTextFieldWidget(FieldWidget):
    body_cls = LineEdit

    def set_valid(self, valid):
        self.body.set_property("valid", valid)


class ColorFieldWidget(ValidatedTextFieldWidget):
    body_cls = ColorPicker

    def post_commit_cb(self):
        super().post_commit_cb()
        self.body.apply_palette() # App stylesheet updates undo our custom palette


class EnumBox(QComboBox):
    def __init__(self, values, update_cb, commit_cb):
        super().__init__()
        self.setFocusPolicy(Qt.NoFocus)
        for value in values:
            self.addItem(value)
        self.commit_cb = commit_cb
        self.currentTextChanged.connect(update_cb)

    def get_value(self):
        return self.currentText()

    def set_value(self, value):
        self.setCurrentText(value)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.commit_cb:
                self.commit_cb()
        else:
            super().keyPressEvent(event)


class EnumFieldWidget(FieldWidget):
    body_cls = EnumBox

    def __init__(self, values, **kwargs):
        self.body_args = {'values': values}
        super().__init__(**kwargs)
