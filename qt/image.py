from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt


def load_image(image_path, for_display=True):
    cls = QPixmap if for_display else QImage
    return cls(image_path)


def save_image(image, image_path):
    image.save(image_path)


def scale_image(image, size, fast=False):
    mode = Qt.FastTransformation if fast else Qt.SmoothTransformation
    return image.scaled(size, aspectMode=Qt.KeepAspectRatio, mode=mode)
