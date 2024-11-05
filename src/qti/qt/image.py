from PySide6.QtGui import QPixmap, QImage, QPainter
from PySide6.QtCore import Qt, QSize


def load_image(image_path):
    return QPixmap(image_path)


def scale_image(image, size):
    return image.scaled(QSize(*size), aspectMode=Qt.KeepAspectRatio, mode=Qt.SmoothTransformation)


def crop_and_pan(image, size, x, y, background_color='black'):
    viewport = QPixmap(QSize(*size))
    viewport.fill(str(background_color))
    p = QPainter(viewport)
    p.drawPixmap(x, y, image)
    p.end()
    return viewport


def center_image(image, size, **kwargs):
    w, h = size
    iw, ih = image.size().toTuple()
    return crop_and_pan(image, size, (w - iw) // 2, (h - ih) // 2, **kwargs)
