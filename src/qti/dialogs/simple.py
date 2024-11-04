from .common import Dialog
from ..qt.dialogs.simple import LabelDialogWidget, LineEditDialogWidget


class InfoDialog(Dialog):
    actions = {'accept': None}
    ui_cls = LabelDialogWidget

    def __init__(self, parent, text, **kwargs):
        self.ui_args = {'text': text} | kwargs
        super().__init__(parent)


class LineEditDialog(Dialog):
    actions = {'accept': None, 'cancel': None}
    ui_cls = LineEditDialogWidget

    def __init__(self, parent, **kwargs):
        self.ui_args = {'update_cb': self.handle_update}
        super().__init__(parent, **kwargs)
        self.handle_update()

    def handle_update(self):
        self.ui.set_error(self.error())

    def error(self):
        return None

    def run(self):
        if super().run():
            return self.ui.get_value()
