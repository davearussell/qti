import copy
from functools import partial

from xui.widgets import DataDialog, HBar, GridBox, HBox, LineEdit, Label, ComboBox
from xui.widgets import PushButton, IconButton, XButton, UpButton, DownButton

TYPES = ['hierarchy', 'single', 'multi']


def key_type(key):
    return ('builtin' if key.builtin
            else 'hierarchy' if key.in_hierarchy
            else 'multi' if key.multi
            else 'single')


class MetadataEditorDialog(DataDialog):
    title = 'Metadata Editor'

    def __init__(self):
        super().__init__()
        self.metadata = self.app.library.metadata
        self.tree = self.app.browser.node.root
        self.meta_edits = []
        self.data = [
            {'id': i,
             'name': key.name,
             'read_only': key.builtin,
             'type': key_type(key)}
            for i, key in enumerate(self.metadata.keys)
        ]
        self.orig_data = copy.deepcopy(self.data)
        self.by_id = {item['id']: item for item in self.data}
        self.next_id = max(self.by_id) + 1
        self.grid = GridBox(spacing=10)
        self.new_box = LineEdit(update_cb=self.check_new_valid, commit_cb=self.add_new)
        self.new_button = PushButton(' New ', click_cb=self.add_new, enabled=False)
        new_group = HBox([self.new_button, self.new_box], spacing=20, child_valign='center')
        self.body.children = [self.grid, HBar(height=50), new_group]
        self.setup_grid()

    def setup_grid(self):
        self.grid.rows = []
        can_up = False
        for i, item in enumerate(self.data):
            read_only = item['read_only']
            can_down = not read_only and i < len(self.data) - 1
            name = LineEdit(item['name'], enabled=(not read_only),
                            update_cb=partial(self.edit_cb, 'name', item['id']),
                            commit_cb=self.focus)
            if read_only:
                type_box = Label('(builtin)', enabled=False)
            else:
                type_box = ComboBox(TYPES, TYPES.index(item['type']),
                                    commit_cb=partial(self.edit_cb, 'type', item['id']))
            up = None if not can_up else UpButton(partial(self.edit_cb, 'up', item['id']))
            down = None if not can_down else DownButton(partial(self.edit_cb, 'down', item['id']))
            delete = None if read_only else XButton(partial(self.edit_cb, 'delete', item['id']))
            self.grid.rows.append([name, type_box, up, down, delete])
            if not read_only:
                can_up = True
        self.grid.rows_updated()

        label_height = self.grid.children[0].min_height()
        for child in self.grid.children:
            if isinstance(child, IconButton):
                child.width = child.height = label_height
        self.relayout()
        self.redraw()

    def check_new_valid(self, name):
        valid = bool(name.strip() and name not in [item['name'] for item in self.data])
        if valid != self.new_button.enabled:
            self.new_button.set_enabled(valid)

    def add_new(self):
        if not self.new_button.enabled:
            return
        item = {
            'name': self.new_box.get_value(),
            'type': 'single',
            'id': self.next_id,
            'read_only': False,
        }
        self.by_id[self.next_id] = item
        self.next_id += 1
        self.new_box.set_value('')
        self.data.append(item)
        self.data_updated()
        self.setup_grid()
        self.focus()

    def edit_cb(self, action, item_id, *args):
        item = self.by_id[item_id]
        row_i = self.data.index(item)
        name_box, type_box = self.grid.rows[row_i][:2]
        if action == 'name':
            item['name'] = name_box.get_value()
        elif action == 'type':
            item['type'] = type_box.choice
        elif action == 'up':
            self.data[row_i - 1], self.data[row_i] = self.data[row_i], self.data[row_i - 1]
        elif action == 'down':
            self.data[row_i + 1], self.data[row_i] = self.data[row_i], self.data[row_i + 1]
        elif action == 'delete':
            self.data.remove(item)
            del self.by_id[item_id]
        if action in ['delete', 'up', 'down']:
            self.setup_grid()
        self.data_updated()

    def is_dirty(self):
        return self.data != self.orig_data

    def get_error(self):
        names = {entry['name'] for entry in self.data}
        if len(names) < len(self.data):
            return 'Duplicate key names found'
        if not all(names):
            return 'Empty key names found'
        return None

    def commit(self):
        hierarchy = self.metadata.hierarchy()
        old_ids = {entry['id']: entry for entry in self.orig_data}
        new_ids = {entry['id']: entry for entry in self.data}

        for eid in old_ids | new_ids:
            old = old_ids.get(eid)
            new = new_ids.get(eid)
            if old and not new:
                self.metadata.delete_key(old['name'])
                self.tree.delete_key(old['name'])
            elif new and not old:
                multi = new['type'] == 'multi'
                in_hierarchy = new['type'] == 'hierarchy'
                self.metadata.add_key(new['name'], multi=multi, in_hierarchy=in_hierarchy)
                self.tree.add_key(new['name'], [] if multi else '')
            elif new != old:
                if new['name'] != old['name']:
                    self.metadata.rename_key(old['name'], new['name'])
                    self.app.filter_config.rename_key(old['name'], new['name'])
                    self.tree.rename_key(old['name'], new['name'])
                if new['type'] != old['type']:
                    is_multi = new['type'] == 'multi'
                    self.metadata.lut[new['name']].in_hierarchy = new['type'] == 'hierarchy'
                    if is_multi != (old['type'] == 'multi'):
                        self.metadata.lut[new['name']].multi = is_multi
                        self.tree.set_key_multi(new['name'], is_multi)
        self.metadata.keys = [self.metadata.lut[entry['name']] for entry in self.data]

        if self.metadata.hierarchy() != hierarchy:
            self.app.status_bar.set_text("WARNING: default grouping updated, app restart"
                                         " required to take effect",
                                         duration_s=10, priority=100)
        self.orig_data = copy.deepcopy(self.data)
