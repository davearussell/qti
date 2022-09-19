from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, Signal, QEvent
from library import Node

import keys
from cache import load_pixmap


class Viewer(QLabel):
    target_selected = Signal(Node)
    unselected = Signal(Node)
    target_updated = Signal(Node)

    def __init__(self, size):
        super().__init__()
        self.setFixedSize(size)
        self.setAlignment(Qt.AlignCenter)
        self.node = None
        self.target = None
        self.pixmap = None

    def load(self, node, target):
        self.node = node
        self.target = target
        self.pixmap = load_pixmap(self.target.library.root_dir, self.target.abspath, self.size())
        self.setPixmap(self.pixmap)
        self.target_updated.emit(target)

    def scroll(self, offset):
        images = self.node.children
        index = images.index(self.target)
        target = images[(index + offset) % (len(images))]
        self.load(self.node, target)
        self.target_updated.emit(target)

    def keyPressEvent(self, event):
        action = keys.get_action(event)
        if action in ['left', 'right']:
            self.scroll(1 if action == 'right' else -1)
        elif action == 'select':
            self.target_selected.emit(self.target)
        elif action == 'unselect':
            self.unselected.emit(self.target)
        else:
            event.ignore()
