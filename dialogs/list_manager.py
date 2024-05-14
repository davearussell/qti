import copy

from .common import DataDialog, FieldDialog
from qt.dialogs.list_manager import ListManagerDialogWidget
from .fields import ValidatedTextField


class ListItemEditDialog(FieldDialog):
    def __init__(self, parent, item, fields):
        self.item = item
        super().__init__(parent.ui, fields)

    def apply_field_update(self, field, value):
        self.item[field.key] = value


class ListItemAddDialog(ListItemEditDialog):
    actions = {'accept': True, 'cancel': True}


class ListManagerDialog(DataDialog):
    ui_cls = ListManagerDialogWidget

    def __init__(self, app, items):
        self.app = app
        self.orig_items = items
        self.items = copy.deepcopy(items)
        super().__init__(app.window)

    @property
    def ui_args(self):
        return {
            'item_names': self.items.keys(),
            'new_cb': self.new_item,
            'edit_cb': self.edit_item,
            'delete_cb': self.delete_item,
        }

    def refresh(self):
        self.data_updated()
        self.ui.load_items()

    def item_defaults(self):
        raise NotImplementedError()

    def field_types(self):
        raise NotImplementedError()

    def item_fields(self, item):
        name_valid = lambda name: name and name not in (set(self.items) - {item['name']})
        fields = [ValidatedTextField('name', item['name'], name_valid)]
        for key, cls, args in self.field_types():
            fields.append(cls(key, item[key], **args))
        return fields

    def new_item(self):
        item =  {'name': ''} | self.item_defaults()
        if ListItemAddDialog(self, item, self.item_fields(item)).run():
            self.items[item['name']] = item
            self.refresh()

    def edit_item(self, item_name):
        item = self.items[item_name]
        if ListItemEditDialog(self, item, self.item_fields(item)).run():
            if item['name'] != item_name:
                self.items[item['name']] = self.items.pop(item_name)
            self.refresh()

    def delete_item(self, item_name):
        del self.items[item_name]
        self.refresh()

    def dirty(self):
        return self.items != self.orig_items

    def commit(self):
        raise NotImplementedError()
