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
        self.setProperty("qtiColors", "default")
        self.setFixedSize(size)
        self.setAlignment(Qt.AlignCenter)
        self.node = None
        self.target = None
        self.pixmap = None
        self.action_map = {
            'left': self.scroll,
            'right': self.scroll,
            'select': self.select,
            'unselect': self.unselect,
        }

    def load(self, node, target):
        self.node = node
        self.target = target
        self.pixmap = load_pixmap(self.target.library.root_dir, self.target.abspath, self.size())
        self.setPixmap(self.pixmap)
        self.target_updated.emit(target)

    def scroll(self, action):
        images = self.node.children
        index = images.index(self.target)
        offset = {'right': 1, 'left': -1}[action]
        target = images[(index + offset) % (len(images))]
        self.load(self.node, target)
        self.target_updated.emit(target)

    def select(self, _action=None):
        self.target_selected.emit(self.target)

    def unselect(self, _action=None):
        self.unselected.emit(self.target)

    def keyPressEvent(self, event):
        action = keys.get_action(event)
        if action in self.action_map:
            self.action_map[action](action)
        else:
            event.ignore()
