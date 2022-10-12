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


class FieldDialog(VBoxDialog):
    title = "Dialog"

    def __init__(self, app):
        super().__init__(app.window, self.title)
        self.app = app
        self.field_list = FieldList()
        self.field_list.field_committed.connect(self.field_committed)
        self.layout().addWidget(self.field_list)
        self.need_reload = False

    def init_fields(self, fields):
        self.field_list.init_fields(fields)
        self.field_list.setFocus()

    def field_committed(self, field, value):
        pass

    def reload(self):
        self.app.reload_tree()

    def accept(self):
        if self.need_reload:
            self.reload()
        super().accept()

    def keyPressEvent(self, event):
        if keys.get_action(event) == 'select':
            self.accept()
        else:
            event.ignore()
