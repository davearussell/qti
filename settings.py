from PySide6.QtCore import QSettings, QSize


_defaults = {
    'thumbnail_size': QSize(250, 200),
}


class Settings:
    def __init__(self, orgname, appname):
        self.q = QSettings(orgname, appname)

    def get(self, key):
        return self.q.value(key, defaultValue=_defaults[key])

    def set(self, key, value):
        self.q.setValue(key, value)

    def __getattr__(self, key):
        if key not in _defaults:
            raise AttributeError("'%s' object has no attribute '%s'" % (type(self).__name__, key))
        return self.get(key)
