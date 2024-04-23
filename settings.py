from color import Color

class Size(list):
    def __init__(self, text):
        values = text.split()
        if len(values) == 3 and values[1] in [',', 'x']:
            values = values[::2] # drop middle value
        self.w, self.h = map(int, values)
        super().__init__((self.w, self.h))

    def __str__(self):
        return "%d x %d" % (self.w, self.h)


DEFAULT_APP_SETTINGS = {
    'background_color':          Color('black'),
    'text_color':                Color('white'),
    'selection_color':           Color('yellow'),
    'mark_color':                Color('gray'),
    'pathbar_separator':         Color('cyan'),
    'thumbnail_size':            Size("250 x 200"),
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
