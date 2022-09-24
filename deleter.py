import os

from PySide6.QtWidgets import QDialog, QWidget, QDialogButtonBox, QRadioButton
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtCore import Qt


class DeleterDialog(QDialog):
    def __init__(self, main_window, node):
        super().__init__(main_window)
        self.node = node
        self.main_window = main_window
        self.setWindowTitle("Confirm delete")
        self.setLayout(QVBoxLayout())
        self.setup_radio_buttons()
        self.setup_action_buttons()

    def mode_setter(self, mode):
        def set_mode():
            self.delete_mode = mode
        return set_mode

    def setup_radio_buttons(self):
        if self.node.is_set:
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
        self.node.library.refresh_images()
        for image in self.node.leaves():
            if self.delete_mode == 'set':
                image.spec[self.node.type].remove(self.node.name)
            else:
                assert self.delete_mode in ['disk', 'library']
                image.delete_from_library()
                if self.delete_mode == 'disk':
                    if os.path.exists(image.abspath):
                        print("Deleting", image.abspath)
                        os.unlink(image.abspath)
                    else:
                        print("Would delete", image.abspath, "but it is not there")
        self.main_window.reload_tree()
        super().accept()
