import copy

import pygame

from xui.widgets import DataDialog, HBox, ComboBox, LineEdit, DataTable

from .. import template


class BulkEditDialog(DataDialog):
    def __init__(self):
        super().__init__()
        self.node = self.app.browser.node
        self.edit_type = self.node.children[0].type
        self.set_title("Bulk %s edit" % (self.edit_type,))
        self.keys = self.choose_keys()
        self.data = [{key: child.get_key(key) for key in self.keys} for child in self.node.children]
        self.orig_data = copy.deepcopy(self.data)
        self.key_box = ComboBox(self.keys)
        self.line_edit = LineEdit(num_chars=20, commit_cb=self.do_update)
        self.editor = HBox([self.key_box, self.line_edit],
                           child_valign='center', spacing=10)
        self.table = DataTable(self.data, self.keys)
        self.body.children = [
            self.editor,
            self.table,
        ]

    def choose_keys(self):
        hierarchy = self.app.library.metadata.hierarchy()
        if self.edit_type == 'image':
            parents = hierarchy
        elif self.edit_type in hierarchy:
            i = hierarchy.index(self.edit_type)
            parents = hierarchy[:i]
        else:
            parents = []
        keys = ['name']
        for key in self.app.library.metadata.keys:
            if key.builtin or key.multi:
                continue
            if key.in_hierarchy and key.name not in parents:
                continue
            keys.append(key.name)
        return keys

    def template_spec(self, node):
        spec = {
            'i': node.index,
            'name': node.name,
        }
        if node.type == 'image':
            spec['dir'] = os.path.basename(os.path.dirname(node.abspath))
            spec['file'] = os.path.splitext(os.path.basename(node.abspath))[0]
        for key in self.app.library.metadata.keys:
            spec[key.name] = node.get_key(key.name)
        return spec

    def do_update(self):
        key = self.key_box.choice
        value = self.line_edit.get_value()
        for i, node in enumerate(self.node.children):
            self.data[i][key] = template.apply(self.template_spec(node), value)
        self.table.refresh()
        self.focus()
        self.data_updated()

    def is_dirty(self):
        return self.data != self.orig_data

    def commit(self):
        for node, row in zip(self.node.children, self.data):
            for key in self.keys:
                node.update(key, row[key])
        self.app.reload_tree()

    def handle_keydown(self, keystroke):
        if keystroke == 'up':
            if self.key_box.choice_i > 0:
                self.key_box.set_choice_i(self.key_box.choice_i - 1)
        elif keystroke == 'down':
            if self.key_box.choice_i < len(self.key_box.choices) - 1:
                self.key_box.set_choice_i(self.key_box.choice_i + 1)
        elif keystroke == 'e':
            self.line_edit.focus()
        else:
            return super().handle_keydown(keystroke)
        return True
