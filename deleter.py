import os

from PySide6.QtWidgets import QDialog, QWidget, QDialogButtonBox, QRadioButton
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtCore import Qt


class DeleterDialog(QDialog):
    def __init__(self, app, nodes):
        super().__init__(app.window)
        self.nodes = nodes
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
        if len(self.nodes) == 1:
            desc = '%s %r' % (self.nodes[0].type_label, self.nodes[0].name)
        else:
            desc = 'these %ss (%d)' % (self.nodes[0].type_label, len(self.nodes))

        if self.nodes[0].type in self.library.metadata.multi_value_keys():
            labels = [
                ('set', 'D&elete %s' % (desc,)),
                ('library', 'De&lete images with %s' % (desc,)),
                ('disk', 'Also delete images from &disk'),
            ]
        else:
            labels = [
                ('library', 'De&lete %s' % (desc,)),
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

    def delete_node(self, node):
        for image in list(node.images()):
            if self.delete_mode == 'set':
                image.spec[node.type].remove(node.name)
            else:
                if self.delete_mode == 'disk':
                    image.base_node.delete_file()
                image.base_node.delete()
                for alias in image.aliases:
                    alias.delete()
            image.delete()

    def accept(self):
        index = self.nodes[0].index
        ancestors = list(self.nodes[0].ancestors())
        parent = ancestors[1]
        grandparent = parent.parent
        root = ancestors[-1]

        for node in self.nodes:
            self.delete_node(node)

        # NOTE: here we rely on the fact that deleting a node from the tree
        # clears its parent attribute, so a null parent indicates that either
        # the node was deleted, or it is the root.
        parent_was_deleted = parent.parent != grandparent
        if parent_was_deleted:
            target_node = root
            for ancestor in ancestors:
                if ancestor.parent:
                    target_node = ancestor
                    break
            self.app.browser.load_node(target_node, mode='grid')
        else:
            index = min(index, len(parent.children) - 1)
            target = None if index == -1 else parent.children[index]
            self.app.browser.load_node(parent, target=target)

        super().accept()
