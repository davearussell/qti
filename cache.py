import os
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
from background import Worker, Dispatcher


class ImageCacher(Worker):
    def run_job(self, job):
        image_path, cache_path, size = job
        if not os.path.exists(cache_path):
            save_cache(image_path, cache_path, size)


class BackgroundCacher(Dispatcher):
    max_job_count = 10
    poll_interval_ms = 100
    worker_type = ImageCacher

    def __init__(self, app, jobs, status_cb):
        super().__init__(app, jobs)
        self.status_cb = status_cb

    def poll(self):
        super().poll()
        if self.done < self.total:
            self.status_cb("Cached %d / %d images" % (self.done, self.total))
        else:
            self.status_cb('')


def background_cacher(app, root_dir, images, sizes, status_cb):
    jobs = []
    for image in images:
        image_path = os.path.join(root_dir, image['path'])
        for size in sizes:
            cache_path = get_cached_path(root_dir, image_path, size)
            if os.path.exists(cache_path):
                continue
            if not os.path.isdir(os.path.dirname(cache_path)):
                os.makedirs(os.path.dirname(cache_path))
            jobs.append((image_path, cache_path, size))
    return BackgroundCacher(app, jobs, status_cb)


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
