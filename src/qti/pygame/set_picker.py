import os

from xui.widgets import HBox, Label, LineEdit


class SetItem(Label):
    bgcolor = '#404040'
    margin = 3



class SetLineEdit(LineEdit):
    def __init__(self, push_cb, pop_cb, **kwargs):
        super().__init__(**kwargs)
        self.push_cb = push_cb
        self.pop_cb = pop_cb

    def handle_keydown(self, keystroke):
        if keystroke == 'space':
            value = self.get_value()
            if value:
                self.push_cb(value)
        elif keystroke == 'tab' and self.dropdown.active and len(self.dropdown.choices) == 1:
            self.push_cb(self.dropdown.choices[0])
        elif keystroke in ['backspace', 'CTRL-backspace'] and not self.get_value():
            self.pop_cb(keystroke == 'CTRL-backspace')
        else:
            return super().handle_keydown(keystroke)
        return True

    def focus_lost(self):
        super().focus_lost()
        value = self.get_value()
        if value:
            self.push_cb(value)


class SetPicker(HBox):
    halign = 'fill'
    spacing = 10

    def __init__(self, update_cb, commit_cb, completions, **kwargs):
        self.line_edit = SetLineEdit(update_cb=update_cb, commit_cb=commit_cb,
                                     push_cb=self.push_cb, pop_cb=self.pop_cb,
                                     completions=completions, **kwargs)
        self.items = []
        super().__init__([self.line_edit], **kwargs)

    def refresh(self):
        self.children = self.items + [self.line_edit]
        self.relayout()

    def push_cb(self, value):
        self.line_edit.set_value('')
        self.items.append(SetItem(value))
        self.refresh()

    def pop_cb(self, ctrl_mod):
        if self.items:
            value = self.items.pop().text
            self.line_edit.set_value('' if ctrl_mod else value)
            self.refresh()

    def focus(self):
        self.line_edit.focus()

    def get_value(self):
        items = [item.text for item in self.items]
        value = self.line_edit.get_value()
        if value:
            items.append(value)
        return items

    def set_value(self, value):
        self.items = [SetItem(item) for item in value]
        self.line_edit.set_value('')
        self.refresh()
