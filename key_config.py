from PySide6.QtWidgets import QDialog, QWidget, QLabel, QPushButton, QDialogButtonBox
from PySide6.QtWidgets import QGridLayout, QVBoxLayout
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPalette

from dialog import DataDialog


MODIFIERS = [
    (Qt.ControlModifier, 'CTRL'),
    (Qt.AltModifier, 'ALT'),
    (Qt.ShiftModifier, 'SHIFT'),
    (Qt.KeypadModifier, 'KP'),
]

MODIFIER_KEYS = [
    Qt.Key_Control,
    Qt.Key_Alt,
    Qt.Key_Shift,
]

def make_label(keybind):
    if keybind is None:
        return '(none)'
    key, modifier = keybind
    keyname = key.name[len('Key_'):] if key else ''
    modifiers = [label for (mod, label) in MODIFIERS if modifier & mod]
    return '-'.join(modifiers + [keyname])


class KeyChooser(QDialog):
    result = Signal(object, object)

    def __init__(self, parent, setter, keymap):
        super().__init__(parent)
        self.setWindowTitle("Select keybind")
        self.setter = setter
        self.keymap = keymap
        self.setLayout(QVBoxLayout())

        if setter.keybind:
            self.key, self.modifiers = setter.keybind
        else:
            self.key = None
            self.modifiers = Qt.KeyboardModifier(0)
        self.extra_modifiers = Qt.KeyboardModifier(0)
        self.count = 0

        self.header = QLabel("Select keybind for action '%s'" % (setter.action,))
        self.header.setAlignment(Qt.AlignHCenter)
        self.layout().addWidget(self.header)

        self.label = KeybindSetter(None, None, setter.keybind)
        self.label.setProperty("qtiFont", "keypicker")
        self.layout().addWidget(self.label)

        unbind = QPushButton("Unbind")
        unbind.clicked.connect(self.clear)
        self.layout().addWidget(unbind)

        self.warning = QLabel()
        self.warning.setProperty("valid", False)
        self.layout().addWidget(self.warning)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        for button in [unbind] + self.buttons.buttons(): # Ensure buttons don't swallow any keystrokes
            button.setText(button.text().replace('&', ''))
            button.setFocusPolicy(Qt.NoFocus)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout().addWidget(self.buttons)

    @property
    def keybind(self):
        if self.key:
            return (self.key, self.modifiers | self.extra_modifiers)
        return None

    def update_label(self):
        self.label.set_keybind(self.keybind)
        setter = self.keymap.get(self.keybind)
        if setter not in (None, self.setter):
            warning = "Already bound to '%s'" % (setter.action,)
        else:
            warning = ''
        self.warning.setText(warning)

    def clear(self):
        self.key = None
        self.modifiers = Qt.KeyboardModifier(0)
        self.extra_modifiers = Qt.KeyboardModifier(0)
        self.update_label()

    def accept(self):
        self.result.emit(self.setter, self.keybind)
        super().accept()

    def keyPressEvent(self, event):
        if not self.count:
            self.clear()
        if event.key() in MODIFIER_KEYS:
            self.extra_modifiers |= event.modifiers()
        else:
            self.key = Qt.Key(event.key())
            self.modifiers = event.modifiers()
        self.count += 1
        self.update_label()

    def keyReleaseEvent(self, event):
        self.count -= 1


class KeybindSetter(QLabel):
    clicked = Signal(object)

    def __init__(self, action, idx, keybind):
        super().__init__()
        self.action = action
        self.idx = idx
        self.keybind = keybind
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(QPalette.Window, Qt.white)
        self.setAlignment(Qt.AlignCenter)
        self.setPalette(pal)
        self.set_keybind(keybind)

    def set_keybind(self, keybind):
        self.keybind = keybind
        self.setText(make_label(self.keybind))

    def mousePressEvent(self, event):
        self.clicked.emit(self)


class KeybindDialog(DataDialog):
    title = 'Key Bindings'

    def __init__(self, app):
        super().__init__(app)
        self.keybinds = app.keybinds
        self.setup_grid()
        self.add_buttons()

    def setup_grid(self):
        self.body = QWidget()
        layout = QGridLayout()
        layout.setVerticalSpacing(10)
        self.body.setLayout(layout)
        self.setLayout(layout)
        self.keymap = {}
        self.setters = []
        for i, action in enumerate(self.keybinds.actions):
            layout.addWidget(QLabel(action.replace('_', ' ').title()), i, 0)
            for idx in range(2):
                keybind = self.keybinds.get_keybind(action, idx)
                setter = KeybindSetter(action, idx, keybind)
                self.setters.append(setter)
                if keybind:
                    self.keymap[keybind] = setter
                setter.clicked.connect(self.clicked)
                layout.addWidget(setter, i, idx + 1)
        self.layout().addWidget(self.body)
        self.orig_keymap = self.keymap.copy()

    def clicked(self, setter):
        kc = KeyChooser(self, setter, self.keymap)
        kc.result.connect(self.update_keybind)
        kc.exec()

    def update_keybind(self, setter, keybind):
        existing = self.keymap.get(keybind)
        if existing is setter:
            return
        self.keymap.pop(setter.keybind, None)
        if existing:
            existing.set_keybind(setter.keybind)
            if setter.keybind:
                self.keymap[setter.keybind] = existing
        setter.set_keybind(keybind)
        if keybind:
            self.keymap[keybind] = setter
        self.data_updated()

    def dirty(self):
        return self.keymap != self.orig_keymap

    def commit(self):
        for setter in self.setters:
            self.keybinds.save_keybind(setter.action, setter.idx, setter.keybind)
