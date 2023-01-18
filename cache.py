import os
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt


ROOT_DIR = None
def set_root_dir(root_dir):
    global ROOT_DIR
    ROOT_DIR = root_dir


def get_cached_path(image_path, size):
    relpath = os.path.relpath(image_path, ROOT_DIR)
    return os.path.join(ROOT_DIR, '.cache', '%dx%d' % size.toTuple(), relpath)


def save_cache(image_path, cache_path, size):
    image = QImage(image_path)
    scaled = image.scaled(size, aspectMode=Qt.KeepAspectRatio,
                          mode=Qt.SmoothTransformation)
    if not os.path.isdir(os.path.dirname(cache_path)):
        os.makedirs(os.path.dirname(cache_path))
    scaled.save(cache_path)


def load_pixmap(image_path, size):
    cache_path = get_cached_path(image_path, size)
    if not os.path.exists(cache_path):
        save_cache(image_path, cache_path, size)
    return QPixmap(cache_path)
