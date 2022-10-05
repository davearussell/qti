from PySide6.QtWidgets import QDialog, QLabel, QDialogButtonBox
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtCore import Qt

from fields import FieldList
import keys


class YesNoDialog(QDialog):
    def __init__(self, parent, title, text):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setLayout(QVBoxLayout())
        label = QLabel()
        label.setText(text)
        self.layout().addWidget(label)
        buttons = QDialogButtonBox(QDialogButtonBox.Yes | QDialogButtonBox.No)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout().addWidget(buttons)
        for button in buttons.buttons():
            button.setShortcut(button.shortcut().toString()[-1]) # 'Alt+X' -> 'X'
            if buttons.buttonRole(button) == QDialogButtonBox.NoRole:
                button.setDefault(True)


class FieldDialog(QDialog):
    title = "Dialog"

    def __init__(self, app):
        super().__init__(app.window)
        self.setWindowTitle(self.title)
        self.app = app
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
