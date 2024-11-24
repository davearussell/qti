from xui.widgets import HBox, Label, CheckBox, RadioButtonGroup

from .common import DialogWidget


class LabelledCheckBox(HBox):
    spacing = 2
    child_valign = 'center'

    def __init__(self, text, keybind=None):
        super().__init__()
        self.label = Label(text, keybind=keybind)
        self.button = CheckBox()
        self.children = [self.button, self.label]


class ChoiceDialogWidget(DialogWidget):
    def __init__(self, choices, **kwargs):
        super().__init__(**kwargs)
        self.choices = [choice for choice, _, _ in choices]
        self.keybinds = {keybind: i for (i, (_, keybind, _)) in enumerate(choices)}
        self.body.children = [LabelledCheckBox(text, keybind=bind) for (_, bind, text) in choices]
        self.group = RadioButtonGroup([child.button for child in self.body.children])
        self.group.select_button(0)

    def selected_choice(self):
        return self.choices[self.group.selected]

    def handle_keydown(self, keystroke):
        if keystroke in self.keybinds:
            self.group.select_button(self.keybinds[keystroke])
            return True
        return super().handle_keydown(keystroke)
