from PySide6.QtCore import Qt

ACTIONS = {
    'up':    [Qt.Key_Up,    (Qt.Key_5, Qt.KeypadModifier)],
    'down':  [Qt.Key_Down,  (Qt.Key_2, Qt.KeypadModifier)],
    'left':  [Qt.Key_Left,  (Qt.Key_1, Qt.KeypadModifier)],
    'right': [Qt.Key_Right, (Qt.Key_3, Qt.KeypadModifier)],

    'prev':  [Qt.Key_PageUp,   (Qt.Key_4, Qt.KeypadModifier)],
    'next':  [Qt.Key_PageDown, (Qt.Key_6, Qt.KeypadModifier)],

    'select':   [Qt.Key_Return,    (Qt.Key_Enter, Qt.KeypadModifier)],
    'unselect': [Qt.Key_Backspace, (Qt.Key_0, Qt.KeypadModifier)],

    'toggle_hide': [Qt.Key_H],
    'quit':        [Qt.Key_Q],
    'edit':        [Qt.Key_E],
    'config':      [Qt.Key_V],
    'delete':      [Qt.Key_D],
}


KEYS = {} # KEY -> action
for action, keys in ACTIONS.items():
    for key in keys:
        if isinstance(key, tuple): # (keycode, modifier)
            key = (key[0], int(key[1]))
        else:
            key = (key, 0)
        if key in KEYS:
            raise Exception("Duplicate  keybind %s  (%s, %s)" % (key, KEYS[key], action))
        KEYS[key] = action


def get_action(event):
    k = (event.key(), int(event.modifiers()))
    return KEYS.get(k)
