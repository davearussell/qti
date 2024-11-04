import argparse
import os
import multiprocessing
import multiprocessing.connection
import signal
import sys
import time

from cache import cache_path, ensure_cached, set_root_dir
from dialogs.importer import find_all_images



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

    def poll(self):
        self.ppipe.recv()
        self.job_count -= 1

    def stop(self):
        self.process.terminate()

    # This runs in the child process
    def main_loop(self, pipe):
        jobs = []
        while True:
            while pipe.poll() or not jobs:
                job = pipe.recv()
                jobs.append(job)
            job = jobs.pop(0)
            ensure_cached(*job)
            pipe.send(None)


class Cacher:
    max_job_count = 10

    def __init__(self, images, sizes):
        super().__init__()
        self.images = images
        self.sizes = sizes
        self.n_workers = multiprocessing.cpu_count() - 1
        self.workers = [Worker() for i in range(self.n_workers)]
        self.jobs = None
        self.dispatched = self.done = self.total = self.skipped = 0

    def start(self):
        jobs = []
        for image_path in self.images:
            for size in self.sizes:
                cached_path = cache_path(image_path, size)
                if os.path.exists(cached_path):
                    self.skipped += 1
                    continue
                if not os.path.isdir(os.path.dirname(cached_path)):
                    os.makedirs(os.path.dirname(cached_path))
                jobs.append((image_path, size))
        self.total = len(jobs)
        self.jobs = iter(jobs)

    def poll(self):
        while True:
            ready = multiprocessing.connection.wait(self.workers, timeout=0)
            if not ready:
                break
            for worker in ready:
                worker.poll()
                self.done += 1

        for worker in self.workers:
            n = min(self.total - self.dispatched,
                    self.max_job_count - worker.job_count)
            if n > 0:
                for i in range(n):
                    self.dispatched += 1
                    worker.dispatch(next(self.jobs))

        if self.done == self.total:
            self.stop()

        return self.done + self.skipped, self.total + self.skipped

    def stop(self):
        for worker in self.workers:
            worker.stop()


def main():
    options = parse_cmdline()
    done = -1
    total = 0

    set_root_dir(options.root_dir)
    cacher = Cacher(find_all_images(options.root_dir), options.size)

    def signal_handler(signum, _):
        cacher.stop()
        sys.exit(0)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    cacher.start()
    while done < total:
        done, total = cacher.poll()
        sys.stdout.write("%d %d\n" % (done, total))
        sys.stdout.flush()
        time.sleep(1)


def parse_cmdline():
    def size(s):
        w, h = s.split('x')
        return (int(w), int(h))
    parser = argparse.ArgumentParser()
    parser.add_argument('root_dir', help='Root directory to search for images under')
    parser.add_argument('-s', '--size', metavar='WIDTHxHEIGHT', action='append',
                        type=size, default=[], help='Cached image size')
    return parser.parse_args()
