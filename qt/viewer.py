from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel


class ViewerWidget(QLabel):
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)

    def load(self, image):
        self.setPixmap(image)

    @property
    def size(self):
        return super().size().toTuple()
