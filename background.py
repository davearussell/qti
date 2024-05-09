import multiprocessing
import multiprocessing.connection
import os

from cache import cache_path, ensure_cached
from qt.timer import Timer


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

    def drain(self):
        self.ppipe.send('drain')

    def drained(self):
        if not self.ppipe.poll():
            return False
        result = self.get_result()
        return result == 'drained'

    # Remaining methods run in the child process

    def run_job(self, job):
        ensure_cached(*job)

    def main_loop(self, pipe):
        jobs = []
        while True:
            while pipe.poll() or not jobs:
                job = pipe.recv()
                if job == 'drain':
                    for job in jobs:
                        pipe.send('aborted')
                    jobs = []
                    pipe.send('drained')
                else:
                    jobs.append(job)

            job = jobs.pop(0)
            result = self.run_job(job)
            pipe.send((job, result))


class BackgroundCacher:
    poll_interval_s = 0.1
    max_job_count = 10

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.timer = Timer(self.poll, repeat=True)
        self.n_workers = multiprocessing.cpu_count() - 1
        self.workers = [Worker() for i in range(self.n_workers)]
        self.draining = []
        self.jobs = None
        self.dispatched = self.done = self.total = self.skipped = 0

    def assign_jobs(self, jobs, skipped):
        if self.done < self.total:
            assert not self.draining
            self.draining = self.workers.copy()
            for worker in self.workers:
                worker.drain()
        self.jobs = iter(jobs)
        self.done = 0
        self.dispatched = 0
        self.skipped = skipped
        self.total = len(jobs)
        self.timer.start(self.poll_interval_s)

    def cache_all_images(self):
        sizes = [self.app.size,
                 self.app.settings.thumbnail_size]
        jobs = []
        skipped = 0
        for image in self.app.library.images():
            image_path = image.abspath
            for size in sizes:
                cached_path = cache_path(image_path, size)
                if os.path.exists(cached_path):
                    skipped += 1
                    continue
                if not os.path.isdir(os.path.dirname(cached_path)):
                    os.makedirs(os.path.dirname(cached_path))
                jobs.append((image_path, size))
        self.assign_jobs(jobs, skipped)

    def poll(self):
        if self.draining:
            for worker in self.draining.copy():
                if worker.drained():
                    self.draining.remove(worker)
            if self.draining:
                return

        while True:
            ready = multiprocessing.connection.wait(self.workers, timeout=0)
            if not ready:
                break
            for worker in ready:
                result = worker.get_result()
                assert isinstance(result, tuple), result
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
            self.app.status_bar.set_text(text, priority=-10, duration_s=self.poll_interval_s * 1.25)
        else:
            self.app.status_bar.set_text(text, duration_s=5)
            self.timer.stop()

    def stop(self):
        self.timer.stop()
        for worker in self.workers:
            worker.stop()
