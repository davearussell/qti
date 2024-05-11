from PySide6.QtWidgets import QLabel
from qt.line_edit import LineEdit
from .common import DialogWidget


class SearchDialogWidget(DialogWidget):
    def __init__(self, update_cb, commit_cb, **kwargs):
        super().__init__(**kwargs)
        self.label = QLabel()
        self.box = LineEdit(update_cb=update_cb, commit_cb=commit_cb)
        self.layout().addWidget(self.label)
        self.layout().addWidget(self.box)
        self.add_action_buttons()

    def focusInEvent(self, event):
        self.box.setFocus()

    def get_value(self):
        return self.box.get_value()

    def set_label(self, text):
        self.label.setText(text)
