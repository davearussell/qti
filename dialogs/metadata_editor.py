import copy

from dialogs.common import DataDialog
from qt.dialogs.metadata_editor import MetadataEditorDialogWidget


def key_type(key):
    return ('builtin' if key.builtin
            else 'hierarchy' if key.in_hierarchy
            else 'multi' if key.multi
            else 'single')


class MetadataEditorDialog(DataDialog):
    title = 'Metadata Editor'
    ui_cls = MetadataEditorDialogWidget

    def __init__(self, app):
        self.app = app
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
        super().__init__(app.window)

    @property
    def ui_args(self):
        return {
            'data': self.data,
            'update_cb': self.handle_update,
        }

    def handle_update(self, data):
        self.data = data
        self.data_updated()

    def dirty(self):
        return self.data != self.orig_data

    def error(self):
        names = {entry['name'] for entry in self.data}
        valid = len(names) == len(self.data)
        return None if valid else 'Duplicate key names found'

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
                    self.metadata.lut[name].in_hierarchy = new['type'] == 'hierarchy'
                    if is_multi != (old['type'] == 'multi'):
                        self.metadata.lut[name].multi = is_multi
                        self.tree.set_key_multi(name, is_multi)
        self.metadata.keys = [self.metadata.lut[entry['name']] for entry in self.data]

        if self.metadata.hierarchy() != hierarchy:
            self.app.status_bar.set_text("WARNING: default grouping updated, app restart"
                                         " required to take effect",
                                         duration_s=10, priority=100)
        self.orig_data = copy.deepcopy(self.data)
