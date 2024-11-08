from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtCore import Qt

from ..keys import event_keystroke

ACTION_NAMES = {
    QDialogButtonBox.AcceptRole: 'accept',
    QDialogButtonBox.YesRole: 'accept',
    QDialogButtonBox.RejectRole: 'cancel',
    QDialogButtonBox.NoRole: 'cancel',
    QDialogButtonBox.ApplyRole: 'apply',
}

BUTTON_TYPES = {
    'accept': QDialogButtonBox.Ok,
    'cancel': QDialogButtonBox.Cancel,
    'apply': QDialogButtonBox.Apply,
    'yes': QDialogButtonBox.Yes,
    'no': QDialogButtonBox.No,
}


class DialogWidget(QDialog):
    def __init__(self, parent, title, actions, action_cb, keydown_cb):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setLayout(QVBoxLayout())
        self.actions = actions
        self.action_cb = action_cb
        self.keydown_cb = keydown_cb

    def add_action_buttons(self):
        roles = QDialogButtonBox.StandardButton()
        for action in self.actions:
            roles |= BUTTON_TYPES[action]
        self.action_buttons = QDialogButtonBox(roles)
        self.action_buttons.clicked.connect(self._clicked)
        for action, shortcut in self.actions.items():
            button = self.action_button(action)
            button.setFocusPolicy(Qt.NoFocus)
            if shortcut:
                # XXX should we add &s?
                button.setShortcut(shortcut)
            else:
                # XXX is this enough?
                button.setText(button.text().replace('&', ''))
        self.layout().addWidget(self.action_buttons)

    def action_button(self, action):
        return self.action_buttons.button(BUTTON_TYPES[action])

    def _clicked(self, button):
        self.action_cb(ACTION_NAMES[self.action_buttons.buttonRole(button)])

    def accept(self, from_app=False):
        if from_app:
            super().accept()
        else:
            self.action_cb('accept')

    def reject(self, from_app=False):
        if from_app:
            super().reject()
        else:
            self.action_cb('cancel')

    def keyPressEvent(self, event):
        if not self.keydown_cb(event_keystroke(event)):
            super().keyPressEvent(event)

    def run(self):
        self.exec()


class DataDialogWidget(DialogWidget):
    dirty = False
    valid = True

    def add_action_buttons(self):
        self.error_box = QLabel()
        self.error_box.setProperty("valid", False)
        self.error_box.setAlignment(Qt.AlignRight)
        self.layout().addWidget(self.error_box)
        super().add_action_buttons()
        self.refresh_buttons()

    def refresh_buttons(self):
        if 'apply' in self.actions:
            self.action_button('apply').setEnabled(self.valid and self.dirty)
        if 'accept' in self.actions:
            self.action_button('accept').setEnabled(self.valid)

    def set_error(self, error):
        self.valid = not error
        self.error_box.setText(error or '')
        self.refresh_buttons()

    def accept(self, from_app=False):
        if self.valid:
            super().accept(from_app)

    def set_dirty(self, dirty):
        self.dirty = dirty
        self.refresh_buttons()

class FieldDialogWidget(DataDialogWidget):
    def __init__(self, group, **kwargs):
        self._group = group
        super().__init__(**kwargs)
        self.layout().addWidget(group)
        self.add_action_buttons()

    def focusInEvent(self, event):
        self._group.setFocus()
