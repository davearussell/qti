from PySide6.QtCore import QSettings


class Datastore:
    def __init__(self):
        self.q = QSettings('davesoft', 'qti')

    def contains(self, key):
        return self.q.contains(key)

    def get(self, key):
        return self.q.value(key)

    def set(self, key, value):
        if value is None:
            self.q.remove(key)
        else:
            self.q.setValue(key, value)

    def remove(self, key):
        self.q.remove(key)

    def keys(self):
        return self.q.allKeys()
