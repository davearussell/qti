import select
import subprocess


class BackgroundCacher:
    poll_interval_s = 1.0

    def __init__(self, app):
        self.app = app
        self.timer = app.timer(self.poll, repeat=True)
        self.done = None
        self.total = None
        self.proc = None

    def cache_all_images(self):
        sizes = [self.app.size,
                 self.app.settings.thumbnail_size]
        cmd = ['qti-image-cacher', self.app.library.root_dir]
        for size in sizes:
            cmd += ['-s', '%dx%d' % tuple(size)]
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        self.timer.start(self.poll_interval_s)

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
