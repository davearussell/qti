from PySide6.QtWidgets import QDialog, QWidget, QLabel, QPushButton, QDialogButtonBox
from PySide6.QtWidgets import QGridLayout, QVBoxLayout
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPalette

from ..keys import event_keystroke, is_modifier
from .common import DialogWidget, DataDialogWidget


class KeyChooserWidget(DialogWidget):
    def __init__(self, action, keybind, keystroke_cb, **kwargs):
        super().__init__(**kwargs)
        self.keystroke_cb = keystroke_cb

        self.action = action
        self.keybind = keybind
        self.count = 0

        self.header = QLabel("Select keybind for action '%s'" % (self.action,))
        self.header.setAlignment(Qt.AlignHCenter)
        self.layout().addWidget(self.header)

        self.label = KeybindLabel(None, None, self.keybind)
        self.label.setProperty("qtiFont", "keypicker")
        self.layout().addWidget(self.label)

        unbind = QPushButton("Unbind")
        unbind.clicked.connect(self.clear)
        unbind.setFocusPolicy(Qt.NoFocus)
        self.layout().addWidget(unbind)

        self.warning = QLabel()
        self.warning.setProperty("valid", False)
        self.layout().addWidget(self.warning)

        self.add_action_buttons()

    def set_warning(self, text):
        self.warning.setText(text)

    def set_keybind(self, keybind):
        self.keybind = keybind
        self.label.setText(keybind)
        self.keystroke_cb(keybind)

    def clear(self):
        self.set_keybind(None)

    def keyPressEvent(self, event):
        if not self.count:
            self.clear()
        keystroke = event_keystroke(event)
        if self.keybind is None and not is_modifier(keystroke):
            self.set_keybind(keystroke)
        self.count += 1

    def keyReleaseEvent(self, event):
        self.count -= 1


class KeybindLabel(QLabel):
    clicked = Signal(object)

    def __init__(self, action, idx, keybind):
        super().__init__()
        self.action = action
        self.idx = idx
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(QPalette.Window, Qt.white)
        self.setAlignment(Qt.AlignCenter)
        self.setPalette(pal)
        self.setText(keybind)

    def mousePressEvent(self, event):
        self.clicked.emit(self)


class KeybindDialogWidget(DataDialogWidget):
    def __init__(self, grid, click_cb, **kwargs):
        super().__init__(**kwargs)
        self.click_cb = click_cb
        self.setup_grid(grid)
        self.add_action_buttons()

    def setup_grid(self, grid):
        self.body = QWidget()
        layout = QGridLayout()
        layout.setVerticalSpacing(10)
        self.body.setLayout(layout)
        self.labels = {} # (action, idx) -> KeybindLabel
        for row, (action, label, binds) in enumerate(grid):
            layout.addWidget(QLabel(label), row, 0)
            for idx, keybind in enumerate(binds):
                label = KeybindLabel(action, idx, keybind)
                self.labels[(action, idx)] = label
                label.clicked.connect(self.clicked)
                layout.addWidget(label, row, idx + 1)
        self.layout().addWidget(self.body)

    def update_keybind(self, action, idx, keybind):
        self.labels[(action, idx)].setText(keybind)

    def clicked(self, label):
        self.click_cb(label.action, label.idx)
