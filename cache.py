import os
from qt.image import load_image, save_image, scale_image


ROOT_DIR = None
def set_root_dir(root_dir): # Called by App.__init__
    global ROOT_DIR
    ROOT_DIR = root_dir


def cache_path(image_path, size):
    relpath = os.path.relpath(image_path, ROOT_DIR)
    return os.path.join(ROOT_DIR, '.cache', '%dx%d' % tuple(size), relpath)


def ensure_cached(image_path, size):
    scaled_path = cache_path(image_path, size)
    if not os.path.isfile(scaled_path):
        image = load_image(image_path, for_display=False)
        scaled = scale_image(image, size)
        if not os.path.isdir(os.path.dirname(scaled_path)):
            os.makedirs(os.path.dirname(scaled_path))
        save_image(scaled, scaled_path)
    return scaled_path


def load_scaled(image_path, size):
    scaled_path = ensure_cached(image_path, size)
    return load_image(scaled_path)
