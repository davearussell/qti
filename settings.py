from PySide6.QtCore import QSettings
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QColor


APP_SETTINGS = [
    # Key                          Type     Default value
    ('background_color',          'color',  QColor(Qt.black)),
    ('text_color',                'color',  QColor(Qt.white)),
    ('selection_color',           'color',  QColor(Qt.yellow)),
    ('pathbar_separator',         'color',  QColor(Qt.cyan)),
    ('thumbnail_size',            'qsize',  QSize(250, 200)),
    ('font',                      'str',    'Liberation mono'),
    ('pathbar_font_size',         'int',    16),
    ('statusbar_font_size',       'int',    16),
    ('thumbnail_name_font_size',  'int',    14),
    ('thumbnail_count_font_size', 'int',    30),
    ('key_picker_font_size',      'int',    20),
]


KEYBINDS = {
    #Action   First bind     Second bind(key, modifier)
    'up':    [Qt.Key_Up,    (Qt.Key_5, Qt.KeypadModifier)],
    'down':  [Qt.Key_Down,  (Qt.Key_2, Qt.KeypadModifier)],
    'left':  [Qt.Key_Left,  (Qt.Key_1, Qt.KeypadModifier)],
    'right': [Qt.Key_Right, (Qt.Key_3, Qt.KeypadModifier)],

    'swap_up':  [(Qt.Key_Up, Qt.ControlModifier)],
    'swap_down':  [(Qt.Key_Down, Qt.ControlModifier)],
    'swap_left':  [(Qt.Key_Left, Qt.ControlModifier)],
    'swap_right':  [(Qt.Key_Right, Qt.ControlModifier)],

    'prev':  [Qt.Key_PageUp,   (Qt.Key_4, Qt.KeypadModifier)],
    'next':  [Qt.Key_PageDown, (Qt.Key_6, Qt.KeypadModifier)],

    'select':   [Qt.Key_Return,    (Qt.Key_Enter, Qt.KeypadModifier)],
    'unselect': [Qt.Key_Backspace, (Qt.Key_0, Qt.KeypadModifier)],
    'cancel':   [Qt.Key_Escape],

    'toggle_hide':   [Qt.Key_H],
    'quit':          [Qt.Key_Q],
    'edit':          [Qt.Key_E],
    'filter_config': [Qt.Key_V],
    'delete':        [Qt.Key_D],
    'edit_metadata': [Qt.Key_M],
    'app_settings':  [Qt.Key_A],
    'edit_keybinds': [Qt.Key_K],

    'save_snapshot':    [Qt.Key_S],
    'restore_snapshot': [Qt.Key_R],
    'jump_to_subject': [Qt.Key_J],

    'add_new_images':   [Qt.Key_N],
}


KEY_SETTINGS = {}
for action, bindings in KEYBINDS.items():
    for i, binding in enumerate(bindings):
        if not isinstance(binding, tuple):
            binding = (binding, Qt.KeyboardModifier(0))
            bindings[i] = binding
        KEY_SETTINGS['keybind_%s_%d' % (action, i)] = binding
    if len(bindings) == 1:
       KEY_SETTINGS['keybind_%s_1' % (action,)] = None


TYPE_MAP = {}
for k, _type, default in APP_SETTINGS:
    TYPE_MAP[k] = (_type, default)
for k, binding in KEY_SETTINGS.items():
    TYPE_MAP[k] = ('keybind', binding)


class Settings:
    def __init__(self, orgname, appname):
        self.q = QSettings(orgname, appname)

    def get(self, key):
        _type, default = TYPE_MAP[key]
        value = self.q.value(key, defaultValue=default)
        if _type == 'int':
            # QSettings bug: if you store an int, restart the app and then read it back,
            # it is returned as a str
            value = int(value)
        return value

    def to_dict(self):
        return {key: self.get(key) for key in TYPE_MAP}

    def set(self, key, value):
        self.q.setValue(key, value)

    def __getattr__(self, key):
        return self.get(key)

    def __contains__(self, key):
        return key in TYPE_MAP
