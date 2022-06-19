import os
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt


def get_cached_path(root_dir, image_path, size):
    relpath = os.path.relpath(image_path, root_dir)
    return os.path.join(root_dir, '.cache', '%dx%d' % size.toTuple(), relpath)


def save_cache(image_path, cache_path, size):
    image = QImage(image_path)
    scaled = image.scaled(size, aspectMode=Qt.KeepAspectRatio,
                          mode=Qt.SmoothTransformation)
    if not os.path.isdir(os.path.dirname(cache_path)):
        os.makedirs(os.path.dirname(cache_path))
    scaled.save(cache_path)


def load_pixmap(root_dir, image_path, size):
    cache_path = get_cached_path(root_dir, image_path, size)
    if not os.path.exists(cache_path):
        save_cache(image_path, cache_path, size)
    return QPixmap(cache_path)

