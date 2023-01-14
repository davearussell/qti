import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox
from PySide6.QtCore import Qt, Signal
from fields import FieldList, TextField, ReadOnlyField, SetField
from dialog import FieldDialog
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


class EditorDialog(QDialog):
    request_scroll = Signal(str, object)
    title = "Editor"

    def __init__(self, app, node):
        super().__init__(app.window)
        self.app = app
        self.setWindowTitle("Editor")
        self.setLayout(QVBoxLayout())

        self.field_list = FieldList()
        self.field_list.field_updated.connect(self.field_updated)
        self.layout().addWidget(self.field_list)

        roles = QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        self.buttons = QDialogButtonBox(roles)
        self.buttons.button(QDialogButtonBox.Apply).setEnabled(False)
        self.buttons.clicked.connect(self._clicked)
        for button in self.buttons.buttons():
            button.setFocusPolicy(Qt.NoFocus)
        self.layout().addWidget(self.buttons)

        self.load_node(node)

    def _clicked(self, button):
        role = self.buttons.buttonRole(button)
        if role == QDialogButtonBox.ApplyRole:
            self.commit()
            self.buttons.button(QDialogButtonBox.Apply).setEnabled(False)
        elif role == QDialogButtonBox.AcceptRole:
            self.commit()
            self.accept()
        else:
            self.reject()

    def load_node(self, node):
        self.node = node
        fields = choose_fields(node)
        self.field_list.init_fields(fields)
        self.field_list.setFocus()

    def scroll_node(self, node):
        self.commit()
        self.load_node(node)

    def dirty(self):
        return any(field.dirty() for field in self.field_list.fields.values())

    def field_updated(self):
        self.buttons.button(QDialogButtonBox.Apply).setEnabled(self.dirty())

    def commit(self):
        if self.dirty():
            self.node.library.refresh_images()
            for field in self.field_list.fields.values():
                if field.dirty():
                    field.update_node(field.get_value())
                    field.mark_clean()
            self.app.reload_tree()
            self.app.library.scan_keys()

    def accept(self):
        self.commit()
        super().accept()

    def keyPressEvent(self, event):
        action = keys.get_action(event)
        if action in keys.SCROLL_ACTIONS:
            self.request_scroll.emit(action, self.scroll_node)
        else:
            super().keyPressEvent(event)
