import os
from PySide6.QtCore import Signal
from fields import FieldDialog, TextField, ReadOnlyField, SetField
import keys


def get_ancestors(node):
    nodes = []
    for ancestor in node.ancestors():
        if ancestor is node or ancestor.type == 'root':
            continue
        nodes.insert(0, ancestor)
    return nodes


def find_keybind(word, taken):
    for char in word.upper():
        if char not in taken:
            taken.add(char)
            return char
    raise Exception("Cannot find keybind for", word)


def choose_fields(node):
    keybinds = set()

    fields = [
        ReadOnlyField('type', node.type_label.title()),
        TextField('name', node.name, keybind='N', commit_cb=update_name)
    ]
    if node.type == 'image':
        fields.append(ReadOnlyField('filename', os.path.basename(node.spec['path'])))
        fields.append(ReadOnlyField('resolution', '%d x %d' % tuple(node.spec['resolution'])))
    if node.type in node.library.default_group_by + ['image']:
        ancestors = {node.type: node for node in get_ancestors(node)}
        for ancestor_type in node.library.default_group_by:
            if ancestor_type == node.type:
                break
            if ancestor_type in ancestors:
                field = TextField(ancestor_type, ancestors[ancestor_type].name,
                                  keybind=find_keybind(ancestor_type, keybinds),
                                  commit_cb=update_ancestor)
            else:
                value = next(node.leaves()).spec[ancestor_type]
                field = ReadOnlyField(ancestor_type, value)
            fields.append(field)
        for key in node.library.sets:
            all_values = node.library.sets[key]
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
            fields.append(SetField(key, values, all_values, keybind=find_keybind(key, keybinds),
                                   commit_cb=update_set))

    return fields


def update_name(node, field, new_value):
    if node.children:
        for leaf in node.leaves():
            value = leaf.spec[node.type]
            if isinstance(value, list):
                value[value.index(field.value)] = new_value
            else:
                leaf.spec[node.type] = new_value
    else:
        node.spec['name'] = new_value
    node.name = new_value # required for reload_tree's path_from_root logic


def update_ancestor(node, field, new_value):
    ancestor_type = field.key
    for leaf in node.leaves():
        leaf.spec[ancestor_type] = new_value
    while node.parent:
        # required for reload_tree's path_from_root logic
        node = node.parent
        if node.type == ancestor_type:
            node.name = new_value
            break

        
def update_set(node, field, new_value):
    if '...' in new_value:
        new_value.remove('...')
        to_add = [key for key in new_value if key not in field.value]
        to_remove = [key for key in field.value if key not in new_value]
        for leaf in node.leaves():
            old_value = leaf.spec[field.key]
            leaf.spec[field.key] = [x for x in old_value if x not in to_remove + to_add] + to_add
    else:
        for leaf in node.leaves():
            leaf.spec[field.key] = new_value


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
        if field.value != value:
            field.commit_cb(self.node, field, value)
            # We can't reload here as reloading would delete the field whose
            # commit signal we're curently being called from
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
