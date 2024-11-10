import copy
import os
from .fields import TextField, ReadOnlyField, SetField
from .common import FieldDialog
from ..tree import FilteredContainer


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
                node.update_set(key, add=to_add, remove=to_remove)
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


def choose_fields(library, nodes):
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
            EditorTextField(library, [first_node], 'name', completions=completions),
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
            field = EditorTextField(library, nodes, ancestor_type,
                                    completions=ancestor_completions)
            fields.append(field)

    for key in library.metadata.keys:
        if key.name not in hierarchy and not key.builtin:
            if key.multi:
                fields.append(EditorSetField(library, nodes, key.name,
                                             completions=key_values[key.name]))
            else:
                fields.append(EditorTextField(library, nodes, key.name))

    return fields


class EditorDialog(FieldDialog):
    title = "Editor"

    def __init__(self, app):
        self.app = app
        self.library = app.library
        self.browser = app.browser
        self.keybinds = self.app.keybinds
        super().__init__(app, app.window, self.choose_fields())

    def choose_fields(self):
        return choose_fields(self.library, self.browser.marked_nodes())

    def new_target_path(self):
        target = self.browser.target
        expr = target.root.filter_config.filter
        old_path = {node.type: node.key for node in target.ancestors()}

        if expr and not any(expr.matches(image.base_node.all_tags()) for image in target.images()):
            # This edit has caused our target to be removed from the current view.
            parent = target.parent
            n = len(parent.children)
            if n == 1: # No siblings, reload_tree will select closest surviving ancestor
                return old_path
            i = parent.children.index(target)
            is_last = (i == n - 1)
            # Prefer the sibling that will occupy the same grid slot that target previously
            # sat in. If this was the final child we can't, so select the new final child.
            target = parent.children[i + (-1 if is_last else 1)]

        # We need an image to construct lut keys. All of our images are guaranteed to
        # have the same value for any field we're grouped by, so any image will do.
        representative_image = next(target.images()).base_node
        hierarchy = representative_image.root.metadata.hierarchy()

        new_path = copy.deepcopy(old_path)
        for field in self.fields:
            key = field.key
            if field.key == 'name' and target.type != 'image':
                key = target.type
            if key in new_path:
                value = field.get_value()
                if isinstance(value, list):
                    # Multi-value keys need special treatment: a copy of the node exists for
                    # each value the key has. Removing the value corresponding to this node
                    # is equivalent to deleting the node, so we treat it the same as the
                    # no-longer-in-view case above
                    if new_path[key] not in value:
                        return old_path
                else:
                    new_path[key] = representative_image.make_lut_key(key)

        return new_path

    def commit(self):
        super().commit()
        self.app.reload_tree(target_path=self.new_target_path())

    def apply_field_update(self, field, value):
        field.update_nodes(value)

    def keydown_cb(self, keystroke):
        action = self.keybinds.get_action(keystroke)
        if self.keybinds.is_scroll(action):
            self.browser.scroll(action)
            if self.dirty():
                self.commit()
            self.init_fields(self.choose_fields())
            return True
        return False
