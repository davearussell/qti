from PySide6.QtWidgets import QLabel
from .common import DialogWidget


class LabelDialogWidget(DialogWidget):
    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.layout().addWidget(QLabel(text))
        self.add_action_buttons()
