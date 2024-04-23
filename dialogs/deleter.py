import os

from .common import Dialog
from qt.dialogs.choice import ChoiceDialogWidget


class DeleterDialog(Dialog):
    ui_cls = ChoiceDialogWidget
    actions = {
        'yes': 'y',
        'no': 'n',
    }

    def __init__(self, app, nodes):
        self.app = app
        self.nodes = nodes
        super().__init__(app.window)

    @property
    def ui_args(self):
        if len(self.nodes) == 1:
            desc = '%s %r' % (self.nodes[0].type_label, self.nodes[0].name)
        else:
            desc = 'these %ss (%d)' % (self.nodes[0].type_label, len(self.nodes))
        if self.nodes[0].type in self.app.library.metadata.multi_value_keys():
            choices = [
                ('set',     'e', 'Delete %s' % (desc,)),
                ('library', 'l', 'Delete images with %s' % (desc,)),
                ('disk',    'd', 'Also delete images from disk'),
            ]
        else:
            choices = [
                ('library', 'l', 'Delete %s' % (desc,)),
                ('disk',    'd', 'Also delete images from disk'),
            ]
        return {'choices': choices}

    def delete_node(self, node):
        delete_mode = self.ui.selected_choice()
        for image in list(node.images()):
            if delete_mode == 'set':
                image.spec[node.type].remove(node.name)
            else:
                if delete_mode == 'disk':
                    image.base_node.delete_file()
                image.base_node.delete()
                for alias in image.aliases:
                    alias.delete()
            image.delete()

    def accept(self):
        index = self.nodes[0].index
        ancestors = list(self.nodes[0].ancestors())
        parent = ancestors[1]
        grandparent = parent.parent
        root = ancestors[-1]

        for node in self.nodes:
            self.delete_node(node)

        # NOTE: here we rely on the fact that deleting a node from the tree
        # clears its parent attribute
        parent_was_deleted = parent.parent != grandparent
        if parent_was_deleted:
            target_node = root
            for ancestor in ancestors:
                if ancestor.parent:
                    target_node = ancestor
                    break
            self.app.browser.load_node(target_node, mode='grid')
        else:
            index = min(index, len(parent.children) - 1)
            target = None if index == -1 else parent.children[index]
            self.app.browser.load_node(parent, target=target)

        super().accept()
