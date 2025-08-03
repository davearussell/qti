from functools import partial

from xui.widgets import HBar, GridBox, HBox, LineEdit, Label, ComboBox
from xui.widgets import PushButton, IconButton, XButton, UpButton, DownButton

from .common import DataDialogWidget

TYPES = ['hierarchy', 'single', 'multi']


class MetadataEditorDialogWidget(DataDialogWidget):
    def __init__(self, data, update_cb, **kwargs):
        super().__init__(**kwargs)
        self.data = data # [ {id, name, read_only, type}, ... ]
        self.by_id = {item['id']: item for item in data}
        self.next_id = max(self.by_id) + 1
        self.update_cb = update_cb
        self.grid = GridBox(spacing=10)
        self.new_box = LineEdit(update_cb=self.check_new, commit_cb=self.add_new)
        self.new_button = PushButton(' New ', click_cb=self.add_new, enabled=False)
        new_group = HBox([self.new_button, self.new_box], spacing=20, child_valign='center')
        self.body.children = [self.grid, HBar(height=50), new_group]
        self.setup_grid()

    def check_new(self, name):
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
        self.update_cb(self.data)
        self.setup_grid()
        self.focus()

    def setup_grid(self):
        self.grid.rows = []
        can_up = False
        for i, item in enumerate(self.data):
            read_only = item['read_only']
            can_down = not read_only and i < len(self.data) - 1
            name = LineEdit(item['name'], enabled=(not read_only),
                            update_cb=partial(self.cb, 'name', item['id']),
                            commit_cb=self.focus)
            if read_only:
                type_box = Label('(builtin)', enabled=False)
            else:
                type_box = ComboBox(TYPES, TYPES.index(item['type']),
                                    commit_cb=partial(self.cb, 'type', item['id']))
            up = None if not can_up else UpButton(partial(self.cb, 'up', item['id']))
            down = None if not can_down else DownButton(partial(self.cb, 'down', item['id']))
            delete = None if read_only else XButton(partial(self.cb, 'delete', item['id']))
            self.grid.rows.append([name, type_box, up, down, delete])
            if not read_only:
                can_up = True
        self.grid.rows_updated()
        self.size_buttons()
        self.relayout()
        self.redraw()

    def size_buttons(self):
        label_height = self.grid.children[0].min_height()
        for child in self.grid.children:
            if isinstance(child, IconButton):
                child.width = child.height = label_height

    def cb(self, action, item_id, *args):
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
        self.update_cb(self.data)
