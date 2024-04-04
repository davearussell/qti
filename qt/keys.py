from PySide6.QtCore import Qt

MOD_LABELS = [
    ('control', 'CTRL'),
    ('alt', 'ALT'),
    ('shift', 'SHIFT'),
    ('keypad', 'KP'),
]

def event_keystroke(event):
    key = Qt.Key(event.key())
    name = key.name[len('Key_'):].lower()
    modifiers = set()
    for mod in Qt.KeyboardModifier:
        if mod is Qt.KeyboardModifierMask:
            continue
        assert mod.name.endswith('Modifier')
        if event.modifiers() & mod:
            modifiers.add(mod.name[:-len('Modifier')].lower())
    return '-'.join([label for (mod_name, label) in MOD_LABELS if mod_name in modifiers] + [name])


def is_modifier(keystroke):
    return keystroke.split('-')[-1] in ['control', 'alt', 'shift', 'meta']
