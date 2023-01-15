from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QColorDialog
from PySide6.QtCore import Qt, QSettings, QSize, Signal
from PySide6.QtGui import QPalette, QColor

from dialog import FieldDialog
from fields import Field, TextField, ValidatedTextField
from line_edit import ValidatedLineEdit
import keys


_settings = [
    # Key                  Type      Default value
    ('background_color',          'color',  QColor(Qt.black)),
    ('text_color',                'color',  QColor(Qt.white)),
    ('selection_color',           'color',  QColor(Qt.yellow)),
    ('pathbar_separator',         'color',  QColor(Qt.cyan)),
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


class ColorPicker(QLabel):
    color_picked = Signal(QColor)

    def __init__(self):
        super().__init__()
        self.setContentsMargins(5, 5, 5, 5)
        self.setAutoFillBackground(True)

    def set_color(self, color):
        self.color = color
        self.setText("Click to edit [%s]" % color.name())
        self.apply_palette()

    def apply_palette(self):
        pal = self.palette()
        pal.setColor(QPalette.Window, self.color)
        pal.setColor(QPalette.WindowText, self.contrasting_color(self.color))
        self.setPalette(pal)

    def contrasting_color(self, color):
        values = [color.red(), color.green(), color.blue()]
        for i in range(len(values)):
            values[i] = 255 if values[i] < 128 else 0
        return QColor(*values)

    def pick_new_color(self):
        new_color = QColorDialog.getColor(self.color)
        if new_color.isValid():
            self.set_color(new_color)
            self.color_picked.emit(new_color)

    def mousePressEvent(self, event):
        self.pick_new_color()


class ColorField(Field):
    def make_body(self):
        self.picker = ColorPicker()
        self.picker.color_picked.connect(self.done)
        container = QWidget()
        layout = QHBoxLayout()
        container.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.picker)
        layout.addStretch(1)
        return container

    def focusInEvent(self, event):
        self.picker.pick_new_color()

    def done(self):
        self.updated.emit()
        super().done()

    def get_value(self):
        return self.picker.color

    def set_value(self, color):
        self.picker.set_color(color)


class TypedEdit(ValidatedLineEdit):
    def normalise(self, value):
        return self.to_text(self.from_text(value))

    @classmethod
    def from_text(cls, text):
        raise NotImplementedError()

    @classmethod
    def to_text(cls, value):
        return str(value)


class TypedField(ValidatedTextField):
    edit_cls = TypedEdit

    def set_value(self, value):
        super().set_value(self.edit_cls.to_text(value))

    def get_value(self):
        if self.body.valid:
            return self.edit_cls.from_text(super().get_value())
        return self.original_value


class IntField(TypedField):
    class edit_cls(TypedEdit):
        @classmethod
        def from_text(cls, text):
            return int(text, base=0)


class SizeField(TypedField):
    class edit_cls(TypedEdit):
        @classmethod
        def from_text(cls, text):
            values = text.split()
            if len(values) == 3 and values[1] in [',', 'x']:
                w, h = values[0], values[2]
            elif len(values) == 2:
                w, h = values
            else:
                w = h = ''
            return QSize(int(w), int(h))

        @classmethod
        def to_text(cls, value):
            return '%d x %d' % value.toTuple()


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
            'color': ColorField,
            }
        keymap = keys.KeyMap()
        return [
            field_types[_type](key, self.settings.get(key), keymap=keymap)
            for (key, _type, _) in _settings
        ]

    def apply_field_update(self, field, value):
        assert field.key in self.settings, (field.key, value)
        self.settings.set(field.key, value)

    def commit(self):
        super().commit()
        self.app.apply_settings()
        # The above call discards the custom palette on our ColorFields
        for field in self.field_list.fields.values():
            if isinstance(field, ColorField):
                field.picker.apply_palette()
