from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QColor


DEFAULT_APP_SETTINGS = {
    'background_color':          QColor(Qt.black),
    'text_color':                QColor(Qt.white),
    'selection_color':           QColor(Qt.yellow),
    'mark_color':                QColor(Qt.gray),
    'pathbar_separator':         QColor(Qt.cyan),
    'thumbnail_size':            QSize(250, 200),
    'font':                      'Liberation mono',
    'zoom_rate':                 1.2,
    'pathbar_font_size':         16,
    'statusbar_font_size':       16,
    'thumbnail_name_font_size':  14,
    'thumbnail_count_font_size': 30,
    'key_picker_font_size':      20,
    'auto_scroll_period':        5,
}


class Settings:
    def __init__(self, store):
        self.store = store
        self.defaults = DEFAULT_APP_SETTINGS

    def get(self, key):
        if key not in self.defaults:
            raise KeyError(key)
        default = self.defaults[key]
        v = self.store.get(key)
        if v is not None:
            return type(default)(v)
        return default

    def to_dict(self):
        return {key: self.get(key) for key in self.defaults}

    def set(self, key, value):
        if key not in self.defaults:
            raise KeyError(key)
        self.store.set(key, value)

    def __getattr__(self, key):
        return self.get(key)
