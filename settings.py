from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QColor


DEFAULT_APP_SETTINGS = [
    # Key                          Type     Default value
    ('background_color',           QColor,  QColor(Qt.black)),
    ('text_color',                 QColor,  QColor(Qt.white)),
    ('selection_color',            QColor,  QColor(Qt.yellow)),
    ('pathbar_separator',          QColor,  QColor(Qt.cyan)),
    ('thumbnail_size',             QSize,   QSize(250, 200)),
    ('font',                       str,     'Liberation mono'),
    ('zoom_rate',                  float,   1.2),
    ('pathbar_font_size',          int,     16),
    ('statusbar_font_size',        int,     16),
    ('thumbnail_name_font_size',   int,     14),
    ('thumbnail_count_font_size',  int,     30),
    ('key_picker_font_size',       int,     20),
]


class Settings:
    def __init__(self, qsettings):
        self.q = qsettings
        self.data = {}
        self.types = {}
        for k, _type, default in DEFAULT_APP_SETTINGS:
            self.types[k] = _type
            value = self.q.value(k)
            if value is None:
                value = default
            elif _type in(int, float):
                # QSettings returns numeric values as strings by default
                value = _type(value)
            self.data[k] = value

    def get(self, key):
        return self.data.get(key)

    def to_dict(self):
        return self.data.copy()

    def set(self, key, value):
        self.data[key] = value
        self.q.setValue(key, value)

    def __getattr__(self, key):
        return self.get(key)

    def __contains__(self, key):
        return key in self.data
