from functools import partial

from xui.widgets import GridBox, Label, PushButton, ScrollArea, Dialog, DataDialog


class KeyChooser(Dialog):
    title = 'Select keybind'
    actions = ['cancel', 'ok']

    bind_font_size = 20
    bind_bgcolor = (32, 32, 32)

    def __init__(self, keymap, action, idx, keybind, accept_cb):
        super().__init__()
        self.keymap = keymap
        self.action = action
        self.idx = idx
        self.keybind = keybind
        self.chosen_keybind = keybind
        self.accept_cb = accept_cb
        self.keybind_label = Label(self.keybind or '(none)', halign='fill', margin=20,
                                   bgcolor=self.bind_bgcolor, font_size=self.bind_font_size)
        self.warning = Label(color='red')
        self.body.children = [
            Label("Select keybind for %r" % (self.action,)),
            self.keybind_label,
            PushButton("Unbind", click_cb=partial(self.set_keybind, None)),
            self.warning,
        ]

    def do_action(self, action):
        if action == 'ok' and self.chosen_keybind != self.keybind:
            self.accept_cb(self.action, self.idx, self.chosen_keybind)
        self.exit()

    def set_keybind(self, keystroke):
        self.keybind_label.set_text(keystroke or '(none)')
        self.chosen_keybind = keystroke
        if keystroke in self.keymap and keystroke != self.keybind:
            self.warning.set_text("Already bound to '%s'" % (self.keymap[keystroke][0],))
        else:
            self.warning.set_text("")

    def handle_keydown(self, keystroke):
        self.set_keybind(str(keystroke))
        return True


class KeybindLabel(Label):
    bgcolor = (32, 32, 32)
    halign = 'fill'

    def __init__(self, keystroke, click_cb):
        super().__init__(keystroke)
        self.click_cb = click_cb

    def handle_mouse_down(self, button, pos):
        if button == 'left':
            self.click_cb()


class KeybindDialog(DataDialog):
    title = 'Key Bindings'

    def __init__(self):
        super().__init__()
        self.keymap = {} # keybind -> (action, idx)
        self.keybinds = {} # (action, idx) -> keybind
        self.labels = {} # (action, idx) -> KeybindLabel
        self.updates = {}
        grid_rows = []
        for action in self.app.keybinds.actions:
            key_label = Label(action.replace('_', ' ').title())
            binds = [self.app.keybinds.get_keybind(action, idx) for idx in range(2)]
            row = [key_label]
            for idx, keystroke in enumerate(binds):
                if keystroke:
                    self.keymap[keystroke] = (action, idx)
                    self.keybinds[(action, idx)] = keystroke
                bind_label = KeybindLabel(keystroke or '', partial(self.click_cb, action, idx))
                self.labels[(action, idx)] = bind_label
                row.append(bind_label)
            grid_rows.append(row)
        self.body.children = [ScrollArea(GridBox(grid_rows, spacing=10), right_bar=True)]

    def click_cb(self, action, idx):
        chooser = KeyChooser(keymap=self.keymap,
                             action=action,
                             idx=idx,
                             keybind=self.keybinds.get((action, idx)),
                             accept_cb=self.update_keybind)
        chooser.run()

    def update_keybind(self, action, idx, keystroke):
        old_keystroke = self.keybinds.pop((action, idx), None)
        if old_keystroke:
            del self.keymap[old_keystroke]

        if keystroke is not None:
            if keystroke in self.keymap:
                old_action, old_idx = self.keymap[keystroke]
                self.update_keybind(old_action, old_idx, None)
            self.keybinds[(action, idx)] = keystroke
            self.keymap[keystroke] = (action, idx)

        self.updates[(action, idx)] = keystroke
        self.labels[(action, idx)].set_text(keystroke or '')
        self.data_updated()

    def is_dirty(self):
        return bool(self.updates)

    def commit(self):
        for (action, idx), bind in self.updates.items():
            self.app.keybinds.save_keybind(action, idx, bind)
        self.updates = {}
