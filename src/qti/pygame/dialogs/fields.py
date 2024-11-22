import pygame

from xui.widgets import HBox, VBox, Label, LineEdit

from ...color import Color


class FieldGroupWidget(VBox):
    spacing = 10

    def __init__(self, keystroke_cb):
        super().__init__()
        self.keystroke_cb = keystroke_cb
        self.fields = []
        self.keybinds = {}

    def set_fields(self, fields):
        self.fields = fields
        self.children = fields
        titles = [field.label.text for field in fields]
        title_len = max(map(len, titles))
        for field, title in zip(fields, titles):
            title = (title_len - len(title)) * ' ' + title
            field.label.set_text(title)
            field.highlight_keybind(self.has_focus)

    def handle_keydown(self, keystroke):
        return self.keystroke_cb(keystroke)

    def focus_gained(self):
        for field in self.fields:
            field.highlight_keybind(True)

    def focus_lost(self):
        for field in self.fields:
            field.highlight_keybind(False)


class FieldWidget(HBox):
    spacing = 10
    child_valign = 'center'

    def __init__(self, key, update_cb, commit_cb, **kwargs):
        super().__init__(**kwargs)
        self.key = key
        self.update_cb = update_cb
        self.commit_cb = commit_cb
        self.label = Label(key.replace('_', ' ').title())
        self.keybind = None
        self.body = self.make_body()
        self.children = [self.label, self.body]

    def set_keybind(self, keybind):
        self.keybind = keybind

    def highlight_keybind(self, enabled):
        self.label.set_keybind(self.keybind if enabled else None)

    def focus(self):
        self.body.focus()

    def make_body(self):
        raise NotImplementedError()

    def get_value(self):
        return self.body.get_value()

    def set_value(self, value):
        self.body.set_value(value)

    def post_commit_cb(self):
        pass


class TextFieldWidget(FieldWidget):
    halign = 'fill'
    color = 'white'
    completions = None
    read_only = False

    def make_body(self):
        return LineEdit(update_cb=self.update_cb, commit_cb=self.commit_cb,
                        enabled=not self.read_only, completions=self.completions)


class SetFieldWidget(TextFieldWidget):
    def get_value(self):
        return super().get_value().split()

    def set_value(self, value):
        super().set_value(' '.join(value))


class ValidatedTextFieldWidget(TextFieldWidget):
    error_color = 'red'
    valid = True

    def set_valid(self, valid):
        if valid != self.valid:
            self.valid = valid
            self.body.color = self.color if self.valid else self.error_color
            self.redraw()


class ColorFieldWidget(ValidatedTextFieldWidget):
    pass
