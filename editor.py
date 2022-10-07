import os
from PySide6.QtCore import Signal
from fields import TextField, ReadOnlyField, SetField
from dialog import FieldDialog
import keys


class NameField(TextField):
    def __init__(self, node, **kwargs):
        self.node = node
        self.original_value = node.name
        kwargs.setdefault('completions', [sibling.name for sibling in node.parent.children])
        super().__init__('name', self.original_value, **kwargs)

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
        self.node.name = new_value # required for reload_tree's path_from_root logic


class AncestorField(TextField):
    def __init__(self, node, ancestor, **kwargs):
        self.node = node
        self.ancestor = ancestor
        self.original_value = ancestor.name
        kwargs.setdefault('completions', [sibling.name for sibling in ancestor.parent.children])
        super().__init__(ancestor.type, self.original_value, **kwargs)

    def update_node(self, new_value):
        for leaf in self.node.leaves():
            leaf.spec[self.ancestor.type] = new_value
        self.ancestor.name = new_value # required for reload_tree's path_from_root logic


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
        self.original_value = values
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
        self.original_value = values.pop() if len(values) == 1 else '...'
        super().__init__(key, self.original_value, **kwargs)

    def update_node(self, new_value):
        if self.original_value == new_value == '...':
            return
        for leaf in self.node.leaves():
            leaf.spec[self.key] = new_value


def choose_fields(node):
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
    return fields


class EditorDialog(FieldDialog):
    request_scroll = Signal(str, object)
    title = "Editor"

    def __init__(self, app, node):
        super().__init__(app)
        self.load_node(node)

    def load_node(self, node):
        self.node = node
        self.init_fields(choose_fields(node))

    def field_committed(self, field, value):
        self.node.library.refresh_images()
        if field.original_value != value:
            field.update_node(value)
            self.need_reload = True
        super().field_committed(field, value)

    def reload(self):
        super().reload()
        self.app.library.scan_keys()

    def keyPressEvent(self, event):
        action = keys.get_action(event)
        if action in keys.SCROLL_ACTIONS:
            self.request_scroll.emit(action, self.load_node)
        else:
            super().keyPressEvent(event)
