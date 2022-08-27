from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, Signal, QEvent
from library import Node

import cache
import keys


class Viewer(QLabel):
    target_selected = Signal(Node)
    unselected = Signal()
    target_updated = Signal(Node)

    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.node = None
        self.target = None
        self.pixmap = None

    def load(self, node, target):
        self.node = node
        self.target = target
        self.pixmap = cache.load_pixmap(self.target.root_dir, self.target.abspath, self.size())
        self.setPixmap(self.pixmap)

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
            self.unselected.emit()
        else:
            event.ignore()
