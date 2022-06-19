from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, Signal, QEvent
from library import Node

import cache

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
        key = event.key()
        if key in [Qt.Key_Left, Qt.Key_Right]:
            self.scroll(1 if key == Qt.Key_Right else -1)
        elif key == Qt.Key_Return:
            self.target_selected.emit(self.target)
        elif key == Qt.Key_Backspace:
            self.unselected.emit()
        else:
            event.ignore()
