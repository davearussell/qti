from PySide6.QtWidgets import QDialog, QWidget, QLabel, QPushButton, QDialogButtonBox
from PySide6.QtWidgets import QGridLayout, QVBoxLayout
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPalette

from dialog import DataDialog
from settings import KEYBINDS
import keys


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

def make_label(binding):
    if binding is None:
        return '(none)'
    key, modifier = binding
    keyname = key.name[len('Key_'):] if key else ''
    modifiers = [label for (mod, label) in MODIFIERS if modifier & mod]
    return '-'.join(modifiers + [keyname])


class KeyChooser(QDialog):
    result = Signal(object, object)

    def __init__(self, parent, keybind, keymap):
        super().__init__(parent)
        self.setWindowTitle("Select keybind")
        self.keybind = keybind
        self.keymap = keymap
        self.setLayout(QVBoxLayout())

        if keybind.binding:
            self.key, self.modifiers = keybind.binding
        else:
            self.key = None
            self.modifiers = Qt.KeyboardModifier(0)
        self.extra_modifiers = Qt.KeyboardModifier(0)
        self.count = 0

        self.header = QLabel("Select keybind for action '%s'" % (keybind.action,))
        self.header.setAlignment(Qt.AlignHCenter)
        self.layout().addWidget(self.header)

        self.label = Keybind(None, None, keybind.binding)
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
    def binding(self):
        if self.key:
            return (self.key, self.modifiers | self.extra_modifiers)
        return None

    def update_label(self):
        self.label.set_binding(self.binding)
        keybind = self.keymap.get(self.binding)
        if keybind not in (None, self.keybind):
            warning = "Already bound to '%s'" % (keybind.action,)
        else:
            warning = ''
        self.warning.setText(warning)

    def clear(self):
        self.key = None
        self.modifiers = Qt.KeyboardModifier(0)
        self.extra_modifiers = Qt.KeyboardModifier(0)
        self.update_label()

    def accept(self):
        self.result.emit(self.keybind, self.binding)
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


class Keybind(QLabel):
    clicked = Signal(object)

    def __init__(self, action, idx, binding):
        super().__init__()
        self.action = action
        self.idx = idx
        self.binding = binding
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(QPalette.Window, Qt.white)
        self.setAlignment(Qt.AlignCenter)
        self.setPalette(pal)
        self.set_binding(binding)

    def set_binding(self, binding):
        self.binding = binding
        self.setText(make_label(self.binding))

    def mousePressEvent(self, event):
        self.clicked.emit(self)


class KeybindDialog(DataDialog):
    title = 'Key Bindings'

    def __init__(self, app):
        super().__init__(app)
        self.setup_grid()
        self.add_buttons()

    def setup_grid(self):
        self.body = QWidget()
        layout = QGridLayout()
        layout.setVerticalSpacing(10)
        self.body.setLayout(layout)
        self.setLayout(layout)
        self.keymap = {}
        self.keybinds = []
        for i, action in enumerate(KEYBINDS):
            layout.addWidget(QLabel(action.replace('_', ' ').title()), i, 0)
            for idx in range(2):
                binding = keys.get_keybind(self.app.settings, action, idx)
                keybind = Keybind(action, idx, binding)
                self.keybinds.append(keybind)
                if binding:
                    self.keymap[binding] = keybind
                keybind.clicked.connect(self.clicked)
                layout.addWidget(keybind, i, idx + 1)
        self.layout().addWidget(self.body)
        self.orig_keymap = self.keymap.copy()

    def clicked(self, keybind):
        kc = KeyChooser(self, keybind, self.keymap)
        kc.result.connect(self.update_keybind)
        kc.exec()

    def update_keybind(self, keybind, binding):
        existing = self.keymap.get(binding)
        if existing is keybind:
            return
        self.keymap.pop(keybind.binding, None)
        if existing:
            existing.set_key(keybind.binding)
            if keybind.binding:
                self.keymap[keybind.binding] = existing
        keybind.set_binding(binding)
        if binding:
            self.keymap[binding] = keybind
        self.data_updated()

    def dirty(self):
        return self.keymap != self.orig_keymap

    def commit(self):
        for keybind in self.keybinds:
            keys.save_keybind(self.app.settings, keybind.action, keybind.idx, keybind.binding)
