from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtCore import Qt, QSize

from ..import image

class Image(image.Image):
    def load(self, path):
        return QPixmap(path)

    def get_size(self):
        return self.image.size().toTuple()

    def scale(self, size):
        return type(self)(self.image.scaled(QSize(*size), aspectMode=Qt.KeepAspectRatio,
                                            mode=Qt.SmoothTransformation))

    def crop_and_pan(self, size, x, y, background_color=None):
        viewport = QPixmap(QSize(*size))
        if background_color:
            viewport.fill(str(background_color))
        p = QPainter(viewport)
        p.drawPixmap(x, y, self.image)
        p.end()
        return type(self)(viewport)
