from .fields import FieldGroup
from qt.dialogs.common import FieldDialogWidget


class Dialog:
    ui_cls = None
    ui_args = {}
    title = 'Dialog'
    actions = {
        'accept': None,
        'cancel': None,
    }

    def __init__(self, parent):
        self.parent = parent
        self.action_cbs = {
            'accept': self.accept,
            'cancel': self.cancel,
            'apply': self.apply,
        }
        self.ui = self.make_ui()

    @property
    def common_ui_args(self):
        return {
            'parent': self.parent,
            'title': self.title,
            'actions': self.actions,
            'action_cb': self._action_cb,
            'keydown_cb': self.keydown_cb,
        }

    def make_ui(self):
        return self.ui_cls(**(self.common_ui_args | self.ui_args))

    def _action_cb(self, action):
        self.action_cbs[action]()

    def keydown_cb(self, keystroke):
        return False

    def run(self):
        self.ui.run()

    def accept(self):
        self.ui.accept(from_app=True)

    def cancel(self):
        self.ui.reject(from_app=True)

    def apply(self):
        raise NotImplementedError()


class DataDialog(Dialog):
    actions = {
        'accept': None,
        'apply': None,
        'cancel': None,
    }

    def accept(self):
        if self.dirty():
            self.commit()
        super().accept()

    def data_updated(self):
        self.ui.set_error(self.error())
        self.ui.set_dirty(self.dirty())

    def apply(self):
        self.commit()
        self.ui.set_dirty(False)

    def error(self):
        return None

    def dirty(self):
        raise NotImplementedError()

    def commit(self):
        raise NotImplementedError()


class FieldDialog(DataDialog):
    ui_cls = FieldDialogWidget

    def __init__(self, parent, fields):
        self._group = FieldGroup(fields, update_cb=self.handle_update)
        super().__init__(parent)

    def init_fields(self, fields):
        self._group.init_fields(fields)

    @property
    def ui_args(self):
        return {
            'group': self._group.ui,
        }

    @property
    def fields(self):
        return self._group.fields

    def handle_update(self, field):
        self.data_updated()

    def dirty(self):
        return any(field.dirty() for field in self.fields)

    def error(self):
        bad_fields = [field.key for field in self.fields if not field.valid]
        return 'Invalid field(s): ' + ', '.join(bad_fields) if bad_fields else None

    def commit(self):
        for field in self.fields:
            if field.dirty():
                self.apply_field_update(field, field.get_value())
                field.mark_clean()
        self.post_commit_cb()

    def post_commit_cb(self):
        for field in self.fields:
            field.post_commit_cb()

    def apply_field_update(self, field, value):
        raise NotImplementedError()
