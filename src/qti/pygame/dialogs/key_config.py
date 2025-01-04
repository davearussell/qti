from functools import partial

from xui.widgets import GridBox, Label, PushButton, ScrollArea

from .common import DialogWidget, DataDialogWidget


class KeyChooserWidget(DialogWidget):
    bind_font_size = 20
    bind_bgcolor = (32, 32, 32)

    def __init__(self, action, keybind, keystroke_cb, **kwargs):
        super().__init__(**kwargs)
        self.keystroke_cb = keystroke_cb
        self.warning = Label(color='red')
        self.keybind = Label(keybind or '(none)', halign='fill', margin=20,
                             bgcolor=self.bind_bgcolor, font_size=self.bind_font_size)
        self.body.children = [
            Label("Select keybind for %r" % (action,)),
            self.keybind,
            PushButton("Unbind", click_cb=self.unbind),
            self.warning,
        ]

    def set_keybind(self, keystroke):
        self.keybind.set_text(keystroke or '(none)')
        self.keystroke_cb(keystroke)

    def handle_keydown(self, keystroke):
        self.set_keybind(str(keystroke))
        return True

    def unbind(self):
        self.set_keybind(None)

    def set_warning(self, message):
        self.warning.set_text(message)


class KeybindLabel(Label):
    bgcolor = (32, 32, 32)
    halign = 'fill'

    def __init__(self, keystroke, click_cb, **kwargs):
        super().__init__(keystroke, **kwargs)
        self.click_cb = click_cb

    def handle_mouse_down(self, button, pos):
        if button == 'left':
            self.click_cb()


class KeybindDialogWidget(DataDialogWidget):
    def __init__(self, grid, click_cb, **kwargs):
        super().__init__(**kwargs)
        self.labels = {}
        rows = []
        for action, action_name, keystrokes in grid:
            row = [Label(action_name)]
            for idx, keystroke in enumerate(keystrokes):
                label = KeybindLabel(keystroke or '', partial(click_cb, action, idx))
                self.labels[(action, idx)] = label
                row.append(label)
            rows.append(row)
        self.grid = ScrollArea(GridBox(rows, spacing=10), right_bar=True)
        self.body.children = [self.grid]

    def update_keybind(self, action, idx, keystroke):
        self.labels[(action, idx)].set_text(keystroke or '(none)')
