from PySide6.QtCore import QObject, QTimer

class Timer(QObject):
    def __init__(self, callback, repeat=False):
        self.__timer = QTimer()
        self.__timer.timeout.connect(self.timeout)
        self.callback = callback
        self.repeat = repeat

    def start(self, duration_s):
        self.__timer.setSingleShot(not self.repeat)
        self.__timer.start(int(1000 * duration_s))

    def stop(self):
        self.__timer.stop()

    def timeout(self):
        if not self.repeat:
            self.stop()
        self.callback()
