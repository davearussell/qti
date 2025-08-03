from .common import Dialog
from ..ui.dialogs.simple import LabelDialogWidget, LineEditDialogWidget


class InfoDialog(Dialog):
    actions = {'ok': None}
    ui_cls = LabelDialogWidget

    def __init__(self, app, parent, text, **kwargs):
        self.ui_args = {'text': text} | kwargs
        super().__init__(app, parent)


class LineEditDialog(Dialog):
    actions = {'ok': None, 'cancel': None}
    ui_cls = LineEditDialogWidget

    def __init__(self, app, parent, **kwargs):
        self.ui_args = {'update_cb': self.handle_update}
        super().__init__(app, parent, **kwargs)
        self.handle_update()

    def handle_update(self):
        self.ui.set_error(self.error())

    def error(self):
        return None

    def result(self):
        return self.ui.get_value() if self.accepted else None
