from xui.widgets import LineEdit, Label

from .common import DialogWidget


class SearchDialogWidget(DialogWidget):
    def __init__(self, update_cb, commit_cb, **kwargs):
        super().__init__(**kwargs)
        self.label = Label('')
        self.edit = LineEdit(update_cb=update_cb, commit_cb=commit_cb)
        self.body.children = [self.label, self.edit]

    def focus(self):
        self.edit.focus()

    def get_value(self):
        return self.edit.get_value()

    def set_status(self, match_name, match_i, n_matches):
        if match_name:
            text = 'Match %d / %d: %s' % (match_i + 1, n_matches, match_name)
        else:
            text = 'No matches'
        self.label.set_text(text)
