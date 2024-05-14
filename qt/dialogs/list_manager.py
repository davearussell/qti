from functools import partial

from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QGridLayout
from PySide6.QtCore import Qt

from .common import DataDialogWidget


def button(label, cb, **cb_args):
    button = QPushButton(label)
    button.setFocusPolicy(Qt.NoFocus)
    button.clicked.connect(partial(cb, **cb_args))
    return button


class ListManagerDialogWidget(DataDialogWidget):
    def __init__(self, item_names, new_cb, edit_cb, delete_cb, **kwargs):
        super().__init__(**kwargs)
        self.item_names = item_names
        self.new_cb = new_cb
        self.edit_cb = edit_cb
        self.delete_cb = delete_cb
        self.body = QWidget()
        self.layout().addWidget(self.body)
        self.load_items()
        self.add_action_buttons()

    def load_items(self):
        QWidget().setLayout(self.body.layout()) # clears any existing layout
        grid = QGridLayout()
        self.body.setLayout(grid)
        for i, name in enumerate(self.item_names):
            grid.addWidget(QLabel(name), i, 0)
            grid.addWidget(button('Edit', self.edit_cb, item_name=name), i, 1)
            grid.addWidget(button('Delete', self.delete_cb, item_name=name), i, 2)
        grid.addWidget(button('Add new', self.new_cb), len(self.item_names), 0, 1, 3)
