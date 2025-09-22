from .common import Dialog
from ..ui.dialogs.simple import LabelDialogWidget


class InfoDialog(Dialog):
    actions = {'ok': None}
    ui_cls = LabelDialogWidget

    def __init__(self, app, parent, text, **kwargs):
        self.ui_args = {'text': text} | kwargs
        super().__init__(app, parent)
