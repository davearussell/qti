import os
from PySide6.QtCore import Signal
from fields import TextField, ReadOnlyField, SetField
from dialog import FieldDialog
from zoom import ZoomField
import keys


class NameField(TextField):
    def __init__(self, node, **kwargs):
        self.node = node
        kwargs.setdefault('completions', [sibling.name for sibling in node.parent.children])
        super().__init__('name', node.name, **kwargs)

    def update_node(self, new_value):
        if self.node.children:
            for leaf in self.node.leaves():
                value = leaf.spec[self.node.type]
                if isinstance(value, list):
                    # We hit this when node is representing an element in a set
                    value[value.index(self.original_value)] = new_value
                else:
                    leaf.spec[self.node.type] = new_value
        else:
            self.node.spec['name'] = new_value


class AncestorField(TextField):
    def __init__(self, node, ancestor, **kwargs):
        self.node = node
        self.ancestor = ancestor
        kwargs.setdefault('completions', [sibling.name for sibling in ancestor.parent.children])
        super().__init__(ancestor.type, ancestor.name, **kwargs)

    def update_node(self, new_value):
        for leaf in self.node.leaves():
            leaf.spec[self.ancestor.type] = new_value


class EditorSetField(SetField):
    def __init__(self, node, key, **kwargs):
        self.node = node
        completions = node.library.sets[key]
        values = None
        varying = False
        for leaf in node.leaves():
            if values is None:
                values = leaf.spec[key].copy()
            elif sorted(values) != sorted(leaf.spec[key]):
                varying = True
                values = [value for value in values if value in leaf.spec[key]]
        if varying:
            values.insert(0, '...')
        super().__init__(key, values, completions=completions, **kwargs)

    def update_node(self, new_value):
        if '...' in new_value:
            new_value.remove('...')
            to_add = [key for key in new_value if key not in self.original_value]
            to_remove = [key for key in self.original_value if key not in new_value]
            for leaf in self.node.leaves():
                old_value = leaf.spec[self.key]
                leaf.spec[self.key] = [x for x in old_value if x not in to_remove + to_add] + to_add
        else:
            for leaf in self.node.leaves():
                leaf.spec[self.key] = new_value


class EditorTextField(TextField):
    def __init__(self, node, key, **kwargs):
        self.node = node
        values = {leaf.spec[key] for leaf in node.leaves()}
        value = values.pop() if len(values) == 1 else '...'
        super().__init__(key, value, **kwargs)

    def update_node(self, new_value):
        for leaf in self.node.leaves():
            leaf.spec[self.key] = new_value


def choose_fields(node, viewer):
    keymap = keys.KeyMap()

    fields = [
        ReadOnlyField('type', node.type_label.title()),
        NameField(node, keymap=keymap)
    ]
    if node.type == 'image':
        fields.append(ReadOnlyField('filename', os.path.basename(node.spec['path'])))
        fields.append(ReadOnlyField('resolution', '%d x %d' % tuple(node.spec['resolution'])))
    if node.type in node.library.hierarchy + ['image']:
        ancestors = {ancestor.type: ancestor for ancestor in node.ancestors()}
        for ancestor_type in node.library.hierarchy:
            if ancestor_type == node.type:
                break
            if ancestor_type in ancestors:
                field = AncestorField(node, ancestors[ancestor_type], keymap=keymap)
            else:
                value = next(node.leaves()).spec[ancestor_type]
                field = ReadOnlyField(ancestor_type, value)
            fields.append(field)
        for key in node.library.metadata_keys():
            if key['name'] not in node.library.hierarchy and not key.get('builtin'):
                cls = EditorSetField if key.get('multi') else EditorTextField
                fields.append(cls(node, key['name'], keymap=keymap))
    if viewer:
        fields.append(ZoomField(viewer, node))
    return fields


class EditorDialog(FieldDialog):
    request_scroll = Signal(str, object)
    title = "Editor"

    def __init__(self, app, node):
        super().__init__(app)
        self.load_node(node)

    def load_node(self, node):
        self.node = node
        self.init_fields(choose_fields(node, self.app.viewer))

    def scroll_node(self, node):
        if self.dirty():
            self.commit()
        self.load_node(node)

    def commit(self):
        self.node.library.refresh_images()
        super().commit()
        self.app.reload_tree()
        self.app.library.scan_keys()

    def apply_field_update(self, field, value):
        field.update_node(value)

    def keyPressEvent(self, event):
        action = keys.get_action(event)
        if action in keys.SCROLL_ACTIONS:
            self.request_scroll.emit(action, self.scroll_node)
        else:
            super().keyPressEvent(event)
