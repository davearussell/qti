from ..import ui


def assign_keybind(keys, word):
    for char in word.lower():
        if char not in keys:
            keys.add(char)
            return char


class FieldGroup:
    def __init__(self, fields, update_cb=None, commit_cb=None, auto_keybinds=True):
        super().__init__()
        self.update_cb = update_cb
        self.commit_cb = commit_cb
        self.auto_keybinds = auto_keybinds
        self.fields = []
        self.keybinds = {}
        self.ui = ui.cls('field_group')(keystroke_cb=self.handle_keystroke)
        self.init_fields(fields)

    def init_fields(self, fields):
        if self.auto_keybinds:
            keys = set()
            for field in fields:
                if not field.read_only:
                    field.set_keybind(assign_keybind(keys, field.key))
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
    ui_cls = ui.cls('field')
    ui_args = {}
    read_only = False

    def __init__(self, key, value, keybind=None, commit_cb=None, update_cb=None):
        self.key = key
        self.original_value = value
        self.valid = True
        self.commit_cb = commit_cb
        self.update_cb = update_cb
        self.ui = self.make_ui()
        self.set_keybind(keybind.lower() if keybind else None)
        self.set_value(self.original_value)

    def set_keybind(self, keybind):
        self.keybind = keybind
        self.ui.set_keybind(keybind)

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
    ui_cls = ui.cls('text_field')

    def __init__(self, key, value, completions=None, **kwargs):
        self.ui_args = {'completions': completions, 'read_only': self.read_only}
        super().__init__(key, value, **kwargs)


class ReadOnlyField(TextField):
    read_only = True


class SetField(TextField):
    ui_cls = ui.cls('set_field')


class ValidatedTextField(Field):
    ui_cls = ui.cls('validated_text_field')

    def __init__(self, key, value, validator, **kwargs):
        self.validator = validator
        super().__init__(key, value, **kwargs)
        self.handle_update()

    def is_valid(self):
        return self.validator(self.ui.get_value())

    def handle_update(self):
        if self.valid != self.is_valid():
            self.valid = not self.valid
            self.ui.set_valid(self.valid)
        super().handle_update()


class TypedField(ValidatedTextField):
    def __init__(self, key, value, parser=None, **kwargs):
        self.parser = type(value) if parser is None else parser
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

    def handle_commit(self):
        if self.valid:
            self.set_value(self.get_value())
        super().handle_commit()


class ColorField(TypedField):
    ui_cls = ui.cls('color_field')


class EnumField(Field):
    ui_cls = ui.cls('enum_field')

    def __init__(self, key, value, values, **kwargs):
        self.ui_args = {'values': values}
        super().__init__(key, value, **kwargs)
