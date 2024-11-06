from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel


class ViewerWidget(QLabel):
    def __init__(self, mouse_cb):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.mouse_cb = mouse_cb

    def load(self, image):
        self.setPixmap(image.image)

    @property
    def size(self):
        return super().size().toTuple()

    def wheelEvent(self, event):
        direction = 1 if event.angleDelta().y() > 0 else -1
        if not self.mouse_cb('wheel', event.position().toTuple(), direction):
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        if not self.mouse_cb('click', event.position().toTuple(), None):
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # NOTE: QT will only call this while a mouse button is pressed
        if not self.mouse_cb('drag', event.position().toTuple(), None):
            super().mouseMoveEvent(event)
    
