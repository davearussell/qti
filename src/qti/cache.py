import os
import select
import subprocess

from PIL import Image

from xui.timer import Timer


ROOT_DIR = None
def set_root_dir(root_dir): # Called by App.__init__
    global ROOT_DIR
    ROOT_DIR = root_dir


def cache_path(image_path, size):
    relpath = os.path.relpath(image_path, ROOT_DIR)
    as_jpg = os.path.splitext(relpath)[0] + '.jpg'
    return os.path.join(ROOT_DIR, '.cache', '%dx%d' % tuple(size), as_jpg)


def ensure_cached(image_path, size):
    scaled_path = cache_path(image_path, size)
    try:
        if not os.path.exists(os.path.dirname(scaled_path)):
            try:
                os.makedirs(os.path.dirname(scaled_path))
            except FileExistsError:
                pass
        if not os.path.isfile(scaled_path):
            image = Image.open(image_path)
            if image.mode == 'RGBA':
                image = image.convert('RGB')
            old_size = image.size
            ratio = min(size[0] / old_size[0], size[1] / old_size[1])
            new_size = (int(old_size[0] * ratio), int(old_size[1] * ratio))
            image.resize(new_size).save(scaled_path)
    except Exception as e:
        # If the image is corrupt, create an empty file so that we don't keep
        # retrying it. We'll report the error when we try to display the image.
        print("WARNING: corrupt or missing image:", image_path)
        if not os.path.exists(scaled_path):
            open(scaled_path, 'wb').close()
    return scaled_path


class BackgroundCacher:
    poll_interval_s = 1.0

    def __init__(self, app):
        self.app = app
        self.timer = Timer(self.poll)
        self.done = None
        self.total = None
        self.proc = None

    def cache_all_images(self):
        if self.proc:
            self.stop()
        sizes = [self.app.size,
                 self.app.settings.thumbnail_size]
        cmd = ['qti-image-cacher', self.app.library.root_dir]
        for size in sizes:
            cmd += ['-s', '%dx%d' % tuple(size)]
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        self.timer.start(self.poll_interval_s, repeat=True)

    def poll(self):
        if not select.select([self.proc.stdout], [], [], 0)[0]:
            return

        data = self.proc.stdout.read1(4096)
        assert data.endswith(b'\n')
        self.done, self.total = map(int, data.split(b'\n')[-2].split())

        text = "Cached %d / %d images" % (self.done, self.total)
        if self.done < self.total:
            self.app.status_bar.set_text(text, priority=-10, duration_s=self.poll_interval_s * 1.25)
        else:
            self.app.status_bar.set_text(text, duration_s=5)
            self.stop()

    def stop(self):
        self.timer.stop()
        if self.proc:
            self.proc.terminate()
            self.proc = None
