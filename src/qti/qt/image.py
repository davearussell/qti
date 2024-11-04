from PySide6.QtGui import QPixmap, QImage, QPainter, QImageReader
from PySide6.QtCore import Qt, QSize

# By default QImageReader refuses to read anything over 256MiB
QImageReader.setAllocationLimit(0)

def load_image(image_path, for_display=True):
    cls = QPixmap if for_display else QImage
    return cls(image_path)


def save_image(image, image_path):
    image.save(image_path)


def scale_image(image, size, fast=False):
    mode = Qt.FastTransformation if fast else Qt.SmoothTransformation
    return image.scaled(QSize(*size), aspectMode=Qt.KeepAspectRatio, mode=mode)


def image_size(image):
    return image.size().toTuple()


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
