from PySide6.QtWidgets import QDialog, QWidget
from PySide6.QtWidgets import QGridLayout
from PySide6.QtCore import Qt


from fields import TextField, ReadOnlyField


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
        ReadOnlyField('type', node.type.title()),
        TextField('name', node.name, keybind='N', commit_cb=update_name)
    ]
    if node.type == 'image':
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

    return fields


def update_name(node, _, new_value):
    if node.children:
        for leaf in node.leaves():
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


class EditorDialog(QDialog):
    def __init__(self, main_window, node):
        super().__init__(main_window)
        self.setWindowTitle("Editor")
        self.main_window = main_window
        self.layout = None
        self.need_reload = False
        self.load_node(node)

    def load_node(self, node):
        self.node = node
        if self.layout:
            QWidget().setLayout(self.layout) # purge existing layout and fields
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.keybinds = {}
        self.fields = {}

        for row_i, field in enumerate(choose_fields(node)):
            self.fields[field.key] = field
            if field.keybind:
                self.keybinds[Qt.Key.values['Key_' + field.keybind]] = field.box
            self.layout.addWidget(field.label, row_i, 0)
            self.layout.addWidget(field.box, row_i, 1)
            if field.editable:
                field.box.commit.connect(self.field_committed)
        self.layout.setRowStretch(row_i + 1, 1)
        self.setFocus()

    def field_committed(self, key, value):
        field = self.fields[key]
        if field.value != value:
            field.commit_cb(self.node, field, value)
            # We can't reload here as reloading would delete the field whose
            # commit signal we're curently being called from
            self.need_reload = True
        self.setFocus()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        if self.need_reload:
            self.need_reload = False
            target = self.main_window.reload_tree()
            self.load_node(target)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Return:
            self.accept()
        elif key in self.keybinds:
            self.keybinds[key].setFocus()
        else:
            event.ignore()
