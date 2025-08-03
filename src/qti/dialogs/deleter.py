import os

from .common import Dialog
from ..ui.dialogs.choice import ChoiceDialogWidget


class DeleterDialog(Dialog):
    title = 'Delete'
    ui_cls = ChoiceDialogWidget
    actions = {
        'yes': 'y',
        'no': 'n',
    }

    def __init__(self, app, nodes):
        self.app = app
        self.nodes = nodes
        super().__init__(app, app.window)

    @property
    def ui_args(self):
        if len(self.nodes) == 1:
            desc = '%s %r' % (self.nodes[0].type_label, self.nodes[0].name)
        else:
            desc = 'these %ss (%d)' % (self.nodes[0].type_label, len(self.nodes))
        if self.nodes[0].type in self.app.library.metadata.multi_value_keys():
            choices = [
                ('tree',    'e', 'Delete %s' % (desc,)),
                ('library', 'l', 'Delete images with %s' % (desc,)),
                ('disk',    'd', 'Also delete images from disk'),
            ]
        else:
            choices = [
                ('library', 'l', 'Delete %s' % (desc,)),
                ('disk',    'd', 'Also delete images from disk'),
            ]
        return {'choices': choices}

    def accept(self):
        delete_mode = self.ui.selected_choice()
        self.app.browser.delete_nodes(self.nodes, propagate=delete_mode)
        super().accept()
