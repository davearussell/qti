import multiprocessing
import multiprocessing.connection
import os

from PySide6.QtCore import QObject, QTimer


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
        raise NotImplementedError()

    def main_loop(self, pipe):
        while True:
            job = pipe.recv()
            if job is None:
                break
            result = self.run_job(job)
            pipe.send((job, result))


class BackgroundJob(QObject):
    poll_interval_ms = 100

    def __init__(self, app):
        super().__init__()
        self.timer = QTimer()
        self.timer.timeout.connect(self._poll)
        self.timer.start(self.poll_interval_ms)
        app.quitting.connect(self.stop)

    def poll(self):
        raise NotImplementedError()

    def _poll(self):
        if self.poll():
            self.stop()

    def stop(self):
        self.timer.stop()


class Dispatcher(BackgroundJob):
    max_job_count = 10

    def __init__(self, app, jobs):
        super().__init__(app)
        self.n_workers = multiprocessing.cpu_count() - 1
        self.workers = [self.worker_type() for i in range(self.n_workers)]
        self.jobs = iter(jobs)
        self.done = 0
        self.dispatched = 0
        self.total = len(jobs)

    @property
    def worker_type(self):
        raise NotImplementedError()

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
        return self.done == self.total

    def stop(self):
        super().stop()
        for worker in self.workers:
            worker.stop()
