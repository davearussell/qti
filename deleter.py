import os

from PySide6.QtWidgets import QDialog, QWidget, QDialogButtonBox, QRadioButton
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtCore import Qt


class DeleterDialog(QDialog):
    def __init__(self, app, node):
        super().__init__(app.window)
        self.node = node
        self.app = app
        self.library = app.library
        self.setWindowTitle("Confirm delete")
        self.setLayout(QVBoxLayout())
        self.setup_radio_buttons()
        self.setup_action_buttons()

    def mode_setter(self, mode):
        def set_mode():
            self.delete_mode = mode
        return set_mode

    def setup_radio_buttons(self):
        if self.node.type in self.library.sets:
            labels = [
                ('set', 'D&elete %s %r' % (self.node.type_label, self.node.name)),
                ('library', 'De&lete images with %s %r' % (self.node.type_label, self.node.name)),
                ('disk', 'Also delete images from &disk'),
            ]
        else:
            labels = [
                ('library', 'De&lete %s %r' % (self.node.type_label, self.node.name)),
                ('disk', 'Also delete images from &disk'),
            ]

        for i, (mode, label) in enumerate(labels):
            button = QRadioButton(label)
            if i == 0:
                self.delete_mode = mode
                button.setChecked(True)
            self.layout().addWidget(button)
            button.clicked.connect(self.mode_setter(mode))
            button.setShortcut(button.shortcut().toString()[-1]) # 'Alt+X' -> 'X'

    def setup_action_buttons(self):
        buttons = QDialogButtonBox(QDialogButtonBox.Yes | QDialogButtonBox.No)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout().addWidget(buttons)
        for button in buttons.buttons():
            button.setShortcut(button.shortcut().toString()[-1]) # 'Alt+X' -> 'X'
            if buttons.buttonRole(button) == QDialogButtonBox.NoRole:
                button.setDefault(True)

    def accept(self):
        parent = self.node.parent
        mode = self.app.browser.mode
        if len(parent.children) > 1:
            index = self.node.index + 1
            if index == len(parent.children):
                index -= 2
            target = parent.children[index]
        else:
            target = None
            mode = 'grid'
            while parent.parent and len(parent.children) == 1:
                parent = parent.parent

        if self.delete_mode == 'set':
            self.node.delete(preserve_images=True)
        else:
            self.node.delete(from_disk=(self.delete_mode == 'disk'))
        self.app.browser.load_node(parent, target=target, mode=mode)
        super().accept()
