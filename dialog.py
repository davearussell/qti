from PySide6.QtWidgets import QDialog, QLabel, QDialogButtonBox, QLineEdit
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtCore import Qt, Signal

from fields import FieldList
import keys


class VBoxDialog(QDialog):
    def __init__(self, parent, title, label=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setLayout(QVBoxLayout())
        if label:
            self.layout().addWidget(QLabel(label))


class YesNoDialog(VBoxDialog):
    def __init__(self, parent, title, text):
        super().__init__(parent, title, label=text)
        buttons = QDialogButtonBox(QDialogButtonBox.Yes | QDialogButtonBox.No)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout().addWidget(buttons)
        for button in buttons.buttons():
            button.setShortcut(button.shortcut().toString()[-1]) # 'Alt+X' -> 'X'
            if buttons.buttonRole(button) == QDialogButtonBox.NoRole:
                button.setDefault(True)


class TextBoxDialog(VBoxDialog):
    result = Signal(str)

    def __init__(self, parent, title, label, value=''):
        super().__init__(parent, title, label)
        self.edit = QLineEdit(value)
        self.layout().addWidget(self.edit)
        self.edit.returnPressed.connect(self._result)
        self.edit.returnPressed.connect(self.accept)

    def _result(self):
        self.result.emit(self.edit.text())


class DataDialog(QDialog):
    title = 'Dialog'

    def __init__(self, app):
        super().__init__(app.window)
        self.app = app
        self.setWindowTitle(self.title)
        self.setLayout(QVBoxLayout())

    def add_buttons(self):
        roles = QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        self.buttons = QDialogButtonBox(roles)
        self.buttons.button(QDialogButtonBox.Apply).setEnabled(False)
        self.buttons.clicked.connect(self._clicked)
        for button in self.buttons.buttons():
            button.setFocusPolicy(Qt.NoFocus)
        self.layout().addWidget(self.buttons)

    def _clicked(self, button):
        role = self.buttons.buttonRole(button)
        if role == QDialogButtonBox.ApplyRole:
            self.commit()
            self.buttons.button(QDialogButtonBox.Apply).setEnabled(False)
        elif role == QDialogButtonBox.AcceptRole:
            self.accept()
        else:
            self.reject()

    def dirty(self):
        raise NotImplementedError()

    def commit(self):
        raise NotImplementedError()

    def accept(self):
        if self.dirty():
            self.commit()
        super().accept()

    def data_updated(self):
        self.buttons.button(QDialogButtonBox.Apply).setEnabled(self.dirty())


class FieldDialog(DataDialog):
    def __init__(self, app):
        super().__init__(app)
        self.field_list = FieldList()
        self.field_list.field_updated.connect(self.data_updated)
        self.layout().addWidget(self.field_list)
        self.add_buttons()

    def init_fields(self, fields):
        self.field_list.init_fields(fields)
        self.field_list.setFocus()

    def dirty(self):
        return any(field.dirty() for field in self.field_list.fields.values())

    def commit(self):
        for field in self.field_list.fields.values():
            if field.dirty():
                self.apply_field_update(field, field.get_value())
                field.mark_clean()

    def apply_field_update(self, field, value):
        raise NotImplementedError()
