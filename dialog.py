from PySide6.QtWidgets import QDialog, QLabel, QDialogButtonBox, QLineEdit
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtCore import Qt, Signal

from fields import FieldGroup


class AbortCommit(Exception):
    pass


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


class InfoDialog(VBoxDialog):
    def __init__(self, parent, title, text):
        super().__init__(parent, title, label=text)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout().addWidget(buttons)
        for button in buttons.buttons():
            button.setShortcut(button.shortcut().toString()[-1]) # 'Alt+X' -> 'X'


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

    def add_buttons(self, apply=True, cancel=True):
        roles = QDialogButtonBox.Ok
        if cancel:
            roles |= QDialogButtonBox.Cancel
        if apply:
            roles |= QDialogButtonBox.Apply
        self.buttons = QDialogButtonBox(roles)
        if apply:
            self.buttons.button(QDialogButtonBox.Apply).setEnabled(False)
        self.buttons.clicked.connect(self._clicked)
        for button in self.buttons.buttons():
            button.setFocusPolicy(Qt.NoFocus)
        self.layout().addWidget(self.buttons)

    def _clicked(self, button):
        role = self.buttons.buttonRole(button)
        if role == QDialogButtonBox.ApplyRole:
            try:
                self.commit()
                self.buttons.button(QDialogButtonBox.Apply).setEnabled(False)
            except AbortCommit:
                pass
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
            try:
                self.commit()
            except AbortCommit:
                return
        super().accept()

    def data_updated(self):
        button = self.buttons.button(QDialogButtonBox.Apply)
        if button:
            button.setEnabled(self.dirty())


class FieldDialog(DataDialog):
    def __init__(self, app):
        super().__init__(app)
        self._group = FieldGroup()
        self._group.field_updated.connect(self.data_updated)
        self.layout().addWidget(self._group)
        self.add_buttons()

    @property
    def fields(self):
        return self._group.fields

    def init_fields(self, fields):
        self._group.init_fields(fields)
        self._group.setFocus()

    def dirty(self):
        return any(field.dirty() for field in self.fields)

    def commit(self):
        for field in self.fields:
            if field.dirty():
                self.apply_field_update(field, field.get_value())
                field.mark_clean()

    def apply_field_update(self, field, value):
        raise NotImplementedError()
