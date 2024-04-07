from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QColorDialog
from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QPalette, QColor

from dialog import FieldDialog
from fields import Field, TextField, ValidatedTextField
from line_edit import ValidatedLineEdit
from keys import KeyMap


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


class FloatField(TypedField):
    class edit_cls(TypedEdit):
        @classmethod
        def from_text(cls, text):
            return float(text)


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


class AppSettingsDialog(FieldDialog):
    title = 'App settings'

    def __init__(self, app):
        super().__init__(app)
        self.settings = app.settings
        self.init_fields(self.choose_fields())

    def choose_fields(self):
        field_types = {
            QSize: SizeField,
            str: TextField,
            int: IntField,
            float: FloatField,
            QColor: ColorField,
        }
        keymap = KeyMap()
        return [
            field_types[type(value)](key, value, keymap=keymap)
            for key, value in self.settings.to_dict().items()
        ]

    def apply_field_update(self, field, value):
        self.settings.set(field.key, value)

    def commit(self):
        super().commit()
        self.app.apply_settings()
        # The above call discards the custom palette on our ColorFields
        for field in self.fields:
            if isinstance(field, ColorField):
                field.picker.apply_palette()
