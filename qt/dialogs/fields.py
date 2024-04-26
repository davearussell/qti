from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, Signal

from qt.keys import event_keystroke
from qt.line_edit import TabCompleteLineEdit


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

    def __init__(self, key, keybind, update_cb, commit_cb):
        super().__init__()
        self.key = key
        self.keybind = keybind
        self.update_cb = update_cb
        self.commit_cb = commit_cb
        self.label = self.make_label()
        self.body = self.make_body()
        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.label)
        layout.addWidget(self.body)
        layout.setContentsMargins(0, 0, 0, 0)

    def focus(self):
        self.setFocus()

    def focusInEvent(self, event):
        self.body.setFocus()

    def make_label(self):
        label = QLabel()
        text = self.key.replace('_', ' ').title()
        if self.keybind:
            idx = text.lower().find(self.keybind)
            text = text[:idx] + '<u>%s</u>' % text[idx] + text[idx+1:]
        label.setText(text)
        return label

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


class TextFieldWidget(FieldWidget):
    body_cls = TabCompleteLineEdit

    def __init__(self, completions, **kwargs):
        self.completions = completions
        super().__init__(**kwargs)

    @property
    def body_args(self):
        return {
            'completions': self.completions,
        }
