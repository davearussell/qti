from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt, QSize


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
