from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QColorDialog
from PySide6.QtCore import Signal
from PySide6.QtGui import QPalette

from dialog import FieldDialog
from fields import Field, TextField, ValidatedTextField
from line_edit import ValidatedLineEdit
from keys import KeyMap
from color import Color


class ColorPicker(QLabel):
    color_picked = Signal(Color)

    def __init__(self):
        super().__init__()
        self.setContentsMargins(5, 5, 5, 5)
        self.setAutoFillBackground(True)

    def set_color(self, color):
        self.color = color
        self.setText("Click to edit [%s]" % color)
        self.apply_palette()

    def apply_palette(self):
        pal = self.palette()
        pal.setColor(QPalette.Window, self.color)
        pal.setColor(QPalette.WindowText, self.color.contrasting())
        self.setPalette(pal)

    def pick_new_color(self):
        qcolor = QColorDialog.getColor(self.color)
        if qcolor.isValid():
            new_color = Color(qcolor.name())
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


class TypedField(ValidatedTextField):
    class edit_cls(ValidatedLineEdit):
        value_type = None # updated by set_value below

        def normalise(self, value):
            return str(self.value_type(value))

    def set_value(self, value):
        self.body.value_type = type(value)
        super().set_value(str(value))

    def get_value(self):
        if self.body.valid:
            return self.body.value_type(super().get_value())
        return self.original_value


class AppSettingsDialog(FieldDialog):
    title = 'App settings'

    def __init__(self, app):
        super().__init__(app)
        self.settings = app.settings
        self.init_fields(self.choose_fields())

    def choose_fields(self):
        field_types = {
            Color: ColorField,
        }
        keymap = KeyMap()
        return [
            field_types.get(type(value), TypedField)(key, value, keymap=keymap)
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
