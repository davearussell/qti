from .common import Dialog
from .. import ui


class InfoDialog(Dialog):
    actions = {'ok': None}
    ui_cls = ui.cls('label_dialog')

    def __init__(self, app, parent, text, **kwargs):
        self.ui_args = {'text': text} | kwargs
        super().__init__(app, parent)


class LineEditDialog(Dialog):
    actions = {'ok': None, 'cancel': None}
    ui_cls = ui.cls('line_edit_dialog')

    def __init__(self, app, parent, **kwargs):
        self.ui_args = {'update_cb': self.handle_update}
        super().__init__(app, parent, **kwargs)
        self.handle_update()

    def handle_update(self):
        self.ui.set_error(self.error())

    def error(self):
        return None

    def run(self):
        if super().run():
            return self.ui.get_value()
