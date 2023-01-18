import multiprocessing
import multiprocessing.connection
import os

from PySide6.QtCore import QObject, QTimer
import cache


class Worker:
    def __init__(self):
        self.ppipe, self.cpipe = multiprocessing.Pipe()
        self.job_count = 0
        self.process = multiprocessing.Process(target=self.main_loop, args=(self.cpipe,))
        self.process.start()

    def fileno(self):
        return self.ppipe.fileno()

    def dispatch(self, job):
        self.job_count += 1
        self.ppipe.send(job)

    def get_result(self):
        result = self.ppipe.recv()
        self.job_count -= 1
        return result

    def stop(self):
        self.process.terminate()

    # Remaining methods run in the child process

    def run_job(self, job):
        image_path, cache_path, size = job
        if not os.path.exists(cache_path):
            cache.save_cache(image_path, cache_path, size)

    def main_loop(self, pipe):
        while True:
            job = pipe.recv()
            result = self.run_job(job)
            pipe.send((job, result))


class BackgroundCacher(QObject):
    poll_interval_ms = 100
    max_job_count = 10

    def __init__(self, app, jobs, skipped):
        super().__init__()
        self.app = app
        self.timer = QTimer()
        self.timer.timeout.connect(self.poll)
        self.timer.start(self.poll_interval_ms)
        app.quitting.connect(self.stop)
        self.n_workers = multiprocessing.cpu_count() - 1
        self.workers = [Worker() for i in range(self.n_workers)]
        self.jobs = iter(jobs)
        self.done = 0
        self.dispatched = 0
        self.skipped = skipped
        self.total = len(jobs)

    def poll(self):
        while True:
            ready = multiprocessing.connection.wait(self.workers, timeout=0)
            if not ready:
                break
            for worker in ready:
                worker.get_result()
                self.done += 1

        for worker in self.workers:
            n = min(self.total - self.dispatched,
                    self.max_job_count - worker.job_count)
            if n > 0:
                for i in range(n):
                    self.dispatched += 1
                    worker.dispatch(next(self.jobs))

        text = "Cached %d / %d images" % (self.done + self.skipped, self.total + self.skipped)
        if self.done < self.total:
            self.app.status_bar.set_text(text, priority=-10, duration_s=self.poll_interval_ms / 800)
        else:
            self.app.status_bar.set_text(text, duration_s=5)
            self.stop()

    def stop(self):
        self.timer.stop()
        for worker in self.workers:
            worker.stop()



def background_cacher(app, images, sizes):
    jobs = []
    skipped = 0
    for image in images:
        image_path = os.path.join(cache.ROOT_DIR, image['path'])
        for size in sizes:
            cache_path = cache.get_cached_path(image_path, size)
            if os.path.exists(cache_path):
                skipped += 1
                continue
            if not os.path.isdir(os.path.dirname(cache_path)):
                os.makedirs(os.path.dirname(cache_path))
            jobs.append((image_path, cache_path, size))
    return BackgroundCacher(app, jobs, skipped) if jobs else None
