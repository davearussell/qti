import os
from PySide6.QtCore import Signal
from fields import TextField, ReadOnlyField, SetField
from dialog import FieldDialog
from zoom import ZoomField
from keys import KeyMap


class NameField(TextField):
    def __init__(self, library, node, **kwargs):
        self.library = library
        self.node = node
        kwargs.setdefault('completions', [sibling.name for sibling in node.parent.children])
        super().__init__('name', node.name, **kwargs)

    def update_node(self, new_value):
        self.node.update('name', new_value)


class AncestorField(TextField):
    def __init__(self, library, node, ancestor, **kwargs):
        self.library = library
        self.node = node
        self.ancestor = ancestor
        kwargs.setdefault('completions', [sibling.name for sibling in ancestor.parent.children])
        super().__init__(ancestor.type, ancestor.name, **kwargs)

    def update_node(self, new_value):
        self.node.update(self.ancestor.type, new_value)


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

    sets = library.scan_sets()

    fields = [
        ReadOnlyField('type', node.type_label.title()),
        NameField(library, node, keymap=keymap)
    ]
    if node.type == 'image':
        fields.append(ReadOnlyField('filename', os.path.basename(node.spec['path'])))
        fields.append(ReadOnlyField('resolution', '%d x %d' % tuple(node.spec['resolution'])))
    if node.type in hierarchy + ['image']:
        ancestors = {ancestor.type: ancestor for ancestor in node.ancestors()}
        for ancestor_type in hierarchy:
            if ancestor_type == node.type:
                break
            if ancestor_type in ancestors:
                field = AncestorField(library, node, ancestors[ancestor_type], keymap=keymap)
            else:
                value = next(node.leaves()).spec[ancestor_type]
                field = ReadOnlyField(ancestor_type, value)
            fields.append(field)
        for key in library.metadata.keys:
            if key.name not in hierarchy and not key.builtin:
                if key.multi:
                    fields.append(EditorSetField(library, node, key.name, keymap=keymap,
                                                 completions=sets[key.name]))
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
