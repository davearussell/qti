from PySide6.QtWidgets import QLabel
from ..line_edit import LineEdit
from .common import DialogWidget, DataDialogWidget


class LabelDialogWidget(DialogWidget):
    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.layout().addWidget(QLabel(text))
        self.add_action_buttons()


class LineEditDialogWidget(DataDialogWidget):
    def __init__(self, update_cb, **kwargs):
        super().__init__(**kwargs)
        self.line_edit = LineEdit(update_cb=update_cb, commit_cb=self.accept)
        self.layout().addWidget(self.line_edit)
        self.add_action_buttons()

    def get_value(self):
        return self.line_edit.get_value()
