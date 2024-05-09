from qt.dialogs.fields import FieldGroupWidget, FieldWidget, TextFieldWidget, SetFieldWidget
from qt.dialogs.fields import ValidatedTextFieldWidget, ColorFieldWidget


class FieldGroup:
    def __init__(self, fields, update_cb=None, commit_cb=None):
        super().__init__()
        self.update_cb = update_cb
        self.commit_cb = commit_cb
        self.fields = []
        self.keybinds = {}
        self.ui = FieldGroupWidget(keystroke_cb=self.handle_keystroke)
        self.init_fields(fields)

    def init_fields(self, fields):
        self.ui.set_fields([field.ui for field in fields])
        self.fields = fields
        self.keybinds = {field.keybind: field for field in self.fields if field.keybind}
        for field in self.fields:
            field.commit_cb = self.handle_commit
            field.update_cb = self.handle_update

    def handle_commit(self, field):
        self.ui.focus()
        if self.commit_cb:
            self.commit_cb(field)

    def handle_update(self, field):
        if self.update_cb:
            self.update_cb(field)

    def handle_keystroke(self, keystroke):
        field = self.keybinds.get(keystroke)
        if field is not None:
            field.focus()
        else:
            return False


class Field:
    ui_cls = FieldWidget
    ui_args = {}

    def __init__(self, key, value, keybind=None, keymap=None, commit_cb=None, update_cb=None):
        self.key = key
        self.original_value = value
        self.valid = True
        self.commit_cb = commit_cb
        self.update_cb = update_cb
        if keymap:
            assert keybind is None, (keybind, keymap)
            self.keybind = keymap.assign_keybind(self.key)
        else:
            self.keybind = keybind.lower() if keybind else None
        self.ui = self.make_ui()
        self.set_value(self.original_value)

    def focus(self):
        self.ui.focus()

    def dirty(self):
        return self.get_value() != self.original_value

    def mark_clean(self):
        self.original_value = self.get_value()

    @property
    def common_ui_args(self):
        return {
            'key': self.key,
            'keybind': self.keybind,
            'update_cb': self.handle_update,
            'commit_cb': self.handle_commit,
        }

    def handle_commit(self):
        if self.commit_cb:
            self.commit_cb(self)

    def handle_update(self):
        if self.update_cb:
            self.update_cb(self)

    def post_commit_cb(self):
        self.ui.post_commit_cb()

    def make_ui(self):
        return self.ui_cls(**self.ui_args, **self.common_ui_args)

    def get_value(self):
        return self.ui.get_value()

    def set_value(self, value):
        self.ui.set_value(value)


class TextField(Field):
    ui_cls = TextFieldWidget

    def __init__(self, key, value, completions=None, read_only=False, **kwargs):
        self.ui_args = {'completions': completions, 'read_only': read_only}
        super().__init__(key, value, **kwargs)


class ReadOnlyField(TextField):
    def __init__(self, key, value, **kwargs):
        super().__init__(key, value, read_only=True, **kwargs)


class SetField(TextField):
    ui_cls = SetFieldWidget


class ValidatedTextField(Field):
    ui_cls = ValidatedTextFieldWidget

    def __init__(self, key, value, validator, **kwargs):
        self.validator = validator
        super().__init__(key, value, **kwargs)

    def is_valid(self):
        return self.validator(self.ui.get_value())

    def handle_update(self):
        if self.valid != self.is_valid():
            self.valid = not self.valid
            self.ui.set_valid(self.valid)
        super().handle_update()


class TypedField(ValidatedTextField):
    def __init__(self, key, value, **kwargs):
        self.parser = type(value)
        def validator(_value):
            try:
                self.parser(_value)
                return True
            except:
                return False
        super().__init__(key, value, validator, **kwargs)

    def set_value(self, value):
        super().set_value(str(value))

    def get_value(self):
        return self.parser(super().get_value()) if self.valid else self.original_value


class ColorField(TypedField):
    ui_cls = ColorFieldWidget
