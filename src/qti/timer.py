class Timer:
    def __init__(self, app, callback=None, repeat=False):
        self.app = app
        self.callback = callback
        self.repeat = repeat
        self.token = 0
        self.duration_s = None
        self._timer = None

    def _start(self):
        self._timer = self.app.ui.call_later(self.duration_s, self.timeout, self.token)

    def start(self, duration_s):
        self.token += 1
        self.duration_s = duration_s
        self._start()

    def stop(self):
        self.token += 1

    def timeout(self, token):
        self._timer = None
        if token == self.token:
            self.callback()
            if self.repeat and token == self.token:
                self._start()
