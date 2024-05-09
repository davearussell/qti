from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtCore import QSize

from .common import DataDialogWidget


class ImporterDialogWidget(DataDialogWidget):
    def __init__(self, fields, grid, **kwargs):
        super().__init__(**kwargs)
        self.fields = fields
        self.grid = grid
        self.body = QWidget()
        self.body.setLayout(QHBoxLayout())
        self.body.layout().addWidget(self.fields)
        self.body.layout().addWidget(self.grid)
        self.layout().addWidget(self.body)
        self.setFixedSize(self.parent().size() - QSize(200, 200))
        self.fields.setFixedWidth(self.width() // 3)
        self.add_action_buttons()

    def focusInEvent(self, event):
        self.fields.setFocus()
