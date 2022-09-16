from PySide6.QtWidgets import QDialog, QLabel, QDialogButtonBox
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtCore import Qt


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
