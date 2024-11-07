import os
from PIL import Image


ROOT_DIR = None
def set_root_dir(root_dir): # Called by App.__init__
    global ROOT_DIR
    ROOT_DIR = root_dir


def cache_path(image_path, size):
    relpath = os.path.relpath(image_path, ROOT_DIR)
    return os.path.join(ROOT_DIR, '.cache', '%dx%d' % tuple(size), relpath)


def ensure_cached(image_path, size):
    scaled_path = cache_path(image_path, size)
    if not os.path.exists(os.path.dirname(scaled_path)):
        try:
            os.makedirs(os.path.dirname(scaled_path))
        except FileExistsError:
            pass
    if not os.path.isfile(scaled_path):
        image = Image.open(image_path)
        old_size = image.size
        ratio = min(size[0] / old_size[0], size[1] / old_size[1])
        new_size = (int(old_size[0] * ratio), int(old_size[1] * ratio))
        image.resize(new_size).save(scaled_path)
    return scaled_path
