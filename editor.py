import os
from PySide6.QtCore import Signal
from fields import TextField, ReadOnlyField, SetField
from dialog import FieldDialog
from tree import FilteredContainer
from zoom import ZoomField
from keys import KeyMap


# Helper class for querying and updating fields on multiple nodes at once.
# Note that it overrides just enough from its parent class to let us call .get_key()
class NodeGroup(FilteredContainer):
    def __init__(self, nodes):
        self.nodes = nodes
        if len(self.nodes) == 1:
            self.name = self.nodes[0].name

    @property
    def root(self):
        return self.nodes[0].root

    def images(self):
        for node in self.nodes:
            yield from node.images()

    def update(self, key, old_value, new_value):
        if new_value == '...':
            pass
        elif isinstance(new_value, list) and '...' in new_value:
            new_value.remove('...')
            to_add = [key for key in new_value if key not in old_value]
            to_remove = [key for key in old_value if key not in new_value]
            for node in self.nodes:
                node.update_set(key, to_add, to_remove)
        else:
            for node in self.nodes:
                node.update(key, new_value)


class EditorTextField(TextField):
    def __init__(self, library, nodes, key, **kwargs):
        self.library = library
        self.node_group = NodeGroup(nodes)
        super().__init__(key, self.node_group.get_key(key), **kwargs)

    def update_nodes(self, new_value):
        self.node_group.update(self.key, self.original_value, new_value)


class EditorSetField(EditorTextField, SetField):
    pass


def choose_fields(library, nodes, viewer):
    keymap = KeyMap()
    hierarchy = library.metadata.hierarchy()

    first_node = nodes[0]

    key_values = library.values_by_key()

    type_label = first_node.type_label.title()
    if len(nodes) > 1:
        type_label = '%s x %d' % (type_label, len(nodes))

    fields = [
        ReadOnlyField('type', type_label),
    ]
    if len(nodes) == 1:
        completions = [sibling.name for sibling in first_node.parent.children]
        if first_node.type == 'image':
            fields += [
                ReadOnlyField('filename', os.path.basename(first_node.spec['path'])),
                ReadOnlyField('resolution', '%d x %d' % tuple(first_node.spec['resolution'])),
            ]
        fields  += [
            EditorTextField(library, [first_node], 'name', keymap=keymap, completions=completions),
        ]

    if first_node.base_node: # nodes are in the hierarchy
        ancestors = {}
        for node in nodes:
            for ancestor in node.base_node.ancestors():
                ancestors.setdefault(ancestor.type, set()).add(ancestor)
        for ancestor_type in hierarchy:
            if ancestor_type == first_node.type:
                break
            ancestor_completions = [sibling.name
                                    for ancestor in ancestors[ancestor_type]
                                    for sibling in ancestor.parent.children]
            field = EditorTextField(library, nodes, ancestor_type, keymap=keymap,
                                    completions=ancestor_completions)
            fields.append(field)

    for key in library.metadata.keys:
        if key.name not in hierarchy and not key.builtin:
            if key.multi:
                fields.append(EditorSetField(library, nodes, key.name, keymap=keymap,
                                             completions=key_values[key.name]))
            else:
                fields.append(EditorTextField(library, nodes, key.name, keymap=keymap))

    if viewer:
        assert len(nodes) == 1
        fields.append(ZoomField(viewer, first_node))
    return fields


class EditorDialog(FieldDialog):
    title = "Editor"

    def __init__(self, app, browser):
        super().__init__(app)
        self.library = app.library
        self.browser = browser
        self.keybinds = self.app.keybinds
        self.setup_fields()

    def setup_fields(self):
        nodes = self.browser.marked_nodes()
        self.init_fields(choose_fields(self.library, nodes, self.app.viewer))

    def commit(self):
        super().commit()
        self.app.reload_tree()

    def apply_field_update(self, field, value):
        field.update_nodes(value)

    def keyPressEvent(self, event):
        action = self.keybinds.get_action(event)
        if self.keybinds.is_scroll(action):
            self.browser.scroll(action)
            if self.dirty():
                self.commit()
            self.setup_fields()
        else:
            super().keyPressEvent(event)
