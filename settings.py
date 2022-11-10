from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PySide6.QtCore import Qt, QSettings, QSize, Signal
from PySide6.QtGui import QFontMetrics

from dialog import FieldDialog
from fields import Field, TextField
from line_edit import LineEdit
import keys


_settings = [
    # Key                  Type      Default value
    ('thumbnail_size',            'qsize',  QSize(250, 200)),
    ('font',                      'str',    'Liberation mono'),
    ('pathbar_font_size',         'int',    16),
    ('statusbar_font_size',       'int',    16),
    ('thumbnail_name_font_size',  'int',    14),
    ('thumbnail_count_font_size', 'int',    30),
]

_type_map = {key: (_type, default) for (key, _type, default) in _settings}


class Settings:
    def __init__(self, orgname, appname):
        self.q = QSettings(orgname, appname)

    def get(self, key):
        _type, default = _type_map[key]
        value = self.q.value(key, defaultValue=default)
        if _type == 'int':
            # QSettings bug: if you store an int, restart the app and then read it back,
            # it is returned as a str
            value = int(value)
        return value

    def to_dict(self):
        return {key: self.get(key) for key in _type_map}

    def set(self, key, value):
        self.q.setValue(key, value)

    def __getattr__(self, key):
        return self.get(key)

    def __contains__(self, key):
        return key in _type_map


class NumberEdit(LineEdit):
    def __init__(self, initial_value, max_digits=3):
        super().__init__(str(initial_value))
        self.max_digits = max_digits
        self.setInputMask('0' * (max_digits - 1) + '9;')
        max_width = QFontMetrics(self.font()).boundingRect('0' * (max_digits + 1)).width()
        self.setMaximumWidth(max_width)


class DimensionEdit(NumberEdit):
    tab = Signal()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Tab:
            self.tab.emit()
        else:
            super().keyPressEvent(event)


class IntField(Field):
    def __init__(self, key, value, max_digits=3, *args, **kwargs):
        self.max_digits = max_digits
        super().__init__(key, value, *args, **kwargs)
        # Because our editor has a fixed width, we need a stretch to
        # keep ourselves horozontally aligned with other fields
        self.layout().addStretch(1)

    def make_body(self, value):
        edit = NumberEdit(value, self.max_digits)
        edit.commit.connect(self.commit_value)
        return edit

    def commit_value(self, value):
        self.commit.emit(self, int(value))


class SizeField(Field):
    def make_body(self, size):
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        container.setLayout(layout)

        self.xbox = DimensionEdit(str(size.width()))
        self.cross = QLabel('x')
        self.ybox = DimensionEdit(str(size.height()))

        layout.addWidget(self.xbox)
        layout.addWidget(self.cross)
        layout.addWidget(self.ybox)
        layout.addStretch(1)

        self.xbox.commit.connect(self.commit_value)
        self.ybox.commit.connect(self.commit_value)
        self.xbox.tab.connect(self.ybox.setFocus)
        self.ybox.tab.connect(self.xbox.setFocus)

        return container

    def commit_value(self, _):
        size = QSize(int(self.xbox.text()), int(self.ybox.text()))
        self.commit.emit(self, size)

    def focusInEvent(self, event):
        self.xbox.setFocus()


class SettingsDialog(FieldDialog):
    title = 'App settings'

    def __init__(self, app):
        super().__init__(app)
        self.settings = app.settings
        self.init_fields(self.choose_fields())

    def choose_fields(self):
        field_types = {
            'qsize': SizeField,
            'str': TextField,
            'int': IntField,
            }
        keymap = keys.KeyMap()
        return [
            field_types[_type](key, self.settings.get(key), keymap=keymap)
            for (key, _type, _) in _settings
        ]

    def field_committed(self, field, value):
        self.need_reload = True
        assert field.key in self.settings, (field.key, value)
        self.settings.set(field.key, value)
        super().field_committed(field, value)

    def reload(self):
        super().reload()
        self.app.apply_settings()
