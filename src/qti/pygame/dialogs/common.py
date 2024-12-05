from functools import partial
import pygame

from xui.widgets import VBox, HBox, Label, PushButton

BUTTON_ORDER = ['apply', 'cancel', 'ok', 'no', 'yes']


class DialogWidget(VBox):
    header_font_size = 20
    margin = 0
    child_halign = 'center'

    border_thickness = 3
    body_margin = 20
    body_spacing = 10

    bgcolor = (0, 0, 0, 224)

    def __init__(self, app, parent, title, actions, action_cb, keydown_cb):
        super().__init__()
        self.app = app
        self.title = title
        self.actions = actions
        self.action_keymap = {v: k for k, v in self.actions.items() if v}
        self.action_cb = action_cb
        self.keydown_cb = keydown_cb
        self.done_cb = None
        self.header = Label(self.title, margin=5, border_thickness=self.border_thickness,
                            font_size=self.header_font_size)
        self.body = VBox(margin=self.body_margin, spacing=self.body_spacing)
        self.buttons = HBox(margin=10, spacing=10, halign='right')
        for action in BUTTON_ORDER:
            if action in self.actions:
                button = PushButton(action.title(), click_cb=partial(action_cb, action))
                self.buttons.children.append(button)
        self.children = [self.header, self.body, self.buttons]

    def run(self, done_cb=None):
        self.done_cb = done_cb
        self.app.screen.children.append(self)
        self.app.screen.layout()
        self._old_focus = self.app.focus_widget
        assert self._old_focus
        self.focus()

    def handle_keydown(self, keystroke):
        if keystroke in self.action_keymap:
            self.action_cb(self.action_keymap[keystroke])
        elif self.keydown_cb(keystroke):
            return True
        elif keystroke == 'escape':
            self.action_cb('cancel')
        elif keystroke in ['return', 'KP-enter']:
            self.action_cb('ok')
        return True

    def handle_mouse_down(self, button, pos):
        super().handle_mouse_down(button, pos)
        # Always consume the click so that it doesn't go to whatever's behind us
        return True

    def exit(self, success):
        self.app.remove_window(self)
        self.screen.redraw()
        self._old_focus.focus()
        if self.done_cb:
            self.done_cb()

    def draw(self):
        super().draw()
        # Initially we will be laid out in the center of the screen.
        # Once our initial position is finalised, we fix it.
        # This means that if we need to grow later, it won't affect our position.
        self.halign = 'fixed'
        self.valign = 'fixed'


class DataDialogWidget(DialogWidget):
    error_color = 'red'
    dirty = False
    valid = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_label = Label(margin=10, color=self.error_color)
        self.children.insert(-1, self.error_label) # just above dialog buttons

    def refresh_buttons(self):
        for button in self.buttons.children:
            action = button.label.text.lower()
            if action == 'apply':
                button.set_enabled(self.valid and self.dirty)
            elif action == 'ok':
                button.set_enabled(self.valid)

    def set_error(self, error):
        self.valid = not error
        self.error_label.set_text(error or '')
        self.refresh_buttons()

    def set_dirty(self, dirty):
        self.dirty = dirty
        self.refresh_buttons()


class FieldDialogWidget(DataDialogWidget):
    def __init__(self, group, **kwargs):
        self._group = group
        super().__init__(**kwargs)
        self.body.children = [group]

    def focus(self):
        self._group.focus()
