from PySide6.QtCore import Qt

ACTIONS = {
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

    'save_snapshot':    [Qt.Key_S],
    'restore_snapshot': [Qt.Key_R],
    'jump_to_subject': [Qt.Key_J],

    'add_new_images':   [Qt.Key_N],
}

SCROLL_ACTIONS = ['up', 'down', 'left', 'right', 'prev', 'next']


KEYS = {} # KEY -> action
for action, keys in ACTIONS.items():
    for key in keys:
        if isinstance(key, tuple): # (keycode, modifier)
            key = (key[0], key[1].value)
        else:
            key = (key, 0)
        if key in KEYS:
            raise Exception("Duplicate  keybind %s  (%s, %s)" % (key, KEYS[key], action))
        KEYS[key] = action


def get_action(event):
    k = (event.key(), event.modifiers().value)
    return KEYS.get(k)


class KeyMap:
    def __init__(self):
        self.keys = {}

    def assign_keybind(self, word):
        for char in word.upper():
            if char not in self.keys:
                self.keys[char] = word
                return char
        raise Exception("Cannot find a free free keybind for %r" % (word,))
