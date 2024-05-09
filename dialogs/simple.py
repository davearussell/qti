from .common import Dialog
from qt.dialogs.simple import LabelDialogWidget


class InfoDialog(Dialog):
    actions = {'accept': None}
    ui_cls = LabelDialogWidget

    def __init__(self, parent, text, **kwargs):
        self.ui_args = {'text': text} | kwargs
        super().__init__(parent)
