import os
from PySide6.QtCore import Signal
from fields import TextField, ReadOnlyField, SetField
from dialog import FieldDialog
from zoom import ZoomField
from keys import KeyMap


class EditorSetField(SetField):
    def __init__(self, library, node, key, **kwargs):
        self.library = library
        self.node = node
        values = node.get_key(key)
        super().__init__(key, values, **kwargs)

    def update_node(self, new_value):
        if '...' in new_value:
            new_value.remove('...')
            to_add = [key for key in new_value if key not in self.original_value]
            to_remove = [key for key in self.original_value if key not in new_value]
            self.node.update_set(self.key, to_add, to_remove)
        else:
            self.node.update(self.key, new_value)


class EditorTextField(TextField):
    def __init__(self, library, node, key, **kwargs):
        self.library = library
        self.node = node
        value = node.get_key(key)
        super().__init__(key, value, **kwargs)

    def update_node(self, new_value):
        self.node.update(self.key, new_value)


def choose_fields(library, node, viewer):
    keymap = KeyMap()
    hierarchy = library.metadata.hierarchy()

    key_values = library.values_by_key()
    name_completions = [sibling.name for sibling in node.parent.children]

    fields = [
        ReadOnlyField('type', node.type_label.title()),
    ]
    if node.type == 'image':
        fields += [
            ReadOnlyField('filename', os.path.basename(node.spec['path'])),
            ReadOnlyField('resolution', '%d x %d' % tuple(node.spec['resolution'])),
        ]

    fields  += [
        EditorTextField(library, node, 'name', keymap=keymap, completions=name_completions),
    ]

    if node.base_node: # node is in the hierarchy
        ancestors = {a.type: a for a in node.base_node.ancestors()}
        for ancestor_type in hierarchy:
            if ancestor_type == node.type:
                break
            ancestor = ancestors[ancestor_type]
            ancestor_completions = [sibling.name for sibling in ancestor.parent.children]
            field = EditorTextField(library, node, ancestor_type, keymap=keymap,
                                    completions=ancestor_completions)
            fields.append(field)

    for key in library.metadata.keys:
        if key.name not in hierarchy and not key.builtin:
            if key.multi:
                fields.append(EditorSetField(library, node, key.name, keymap=keymap,
                                             completions=key_values[key.name]))
            else:
                fields.append(EditorTextField(library, node, key.name, keymap=keymap))

    if viewer:
        fields.append(ZoomField(viewer, node))
    return fields


class EditorDialog(FieldDialog):
    title = "Editor"

    def __init__(self, app, browser):
        super().__init__(app)
        self.library = app.library
        self.browser = browser
        self.keybinds = self.app.keybinds
        self.setup_fields()

    @property
    def node(self):
        return self.browser.target

    def setup_fields(self):
        self.init_fields(choose_fields(self.library, self.node, self.app.viewer))

    def commit(self):
        super().commit()
        self.app.reload_tree()

    def apply_field_update(self, field, value):
        field.update_node(value)

    def keyPressEvent(self, event):
        action = self.keybinds.get_action(event)
        if self.keybinds.is_scroll(action):
            self.browser.scroll(action)
            if self.dirty():
                self.commit()
            self.setup_fields()
        else:
            super().keyPressEvent(event)
