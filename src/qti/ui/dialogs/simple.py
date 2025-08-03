from xui.widgets import Label, LineEdit

from .common import DialogWidget, DataDialogWidget


class LabelDialogWidget(DialogWidget):
    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.body.children = [Label(text)]


class LineEditDialogWidget(DataDialogWidget):
    def __init__(self, update_cb, **kwargs):
        super().__init__(**kwargs)
        self.update_cb = update_cb
        self.line_edit = LineEdit(update_cb=self.text_update, commit_cb=self.text_commit)
        self.body.children = [self.line_edit]

    def focus(self):
        self.line_edit.focus()

    def text_update(self, _):
        self.update_cb()

    def text_commit(self):
        if self.valid:
            self.action_cb('ok')

    def get_value(self):
        return self.line_edit.get_value()
