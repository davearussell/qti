from .common import Dialog, DataDialog
from ..import ui


class KeyChooser(Dialog):
    title = 'Select keybind'
    ui_cls = ui.cls('key_chooser')

    def __init__(self, parent, keymap, action, idx, keybind, accept_cb):
        self.keymap = keymap
        self.action = action
        self.idx = idx
        self.keybind = keybind
        self.chosen_keybind = keybind
        self.accept_cb = accept_cb
        super().__init__(parent)

    @property
    def ui_args(self):
        return {
            'action': self.action,
            'keybind': self.keybind,
            'keystroke_cb': self.handle_keystroke,
        }

    def handle_keystroke(self, keystroke):
        self.chosen_keybind = keystroke
        if keystroke in self.keymap and keystroke != self.keybind:
            self.ui.set_warning("Already bound to '%s'" % (self.keymap[keystroke][0],))
        else:
            self.ui.set_warning("")

    def accept(self):
        if self.chosen_keybind != self.keybind:
            self.accept_cb(self.action, self.idx, self.chosen_keybind)
        super().accept()


class KeybindDialog(DataDialog):
    title = 'Key Bindings'
    ui_cls = ui.cls('key_config_dialog')

    def __init__(self, app):
        self.app = app
        self.updates = {}
        self.keymap = {} # keybind -> (action, idx)
        self.keybinds = {} # (action, idx) -> keybind
        self.grid = []
        for i, action in enumerate(app.keybinds.actions):
            label = action.replace('_', ' ').title()
            binds = [app.keybinds.get_keybind(action, idx) for idx in range(2)]
            for idx, keybind in enumerate(binds):
                if keybind:
                    self.keymap[keybind] = (action, idx)
                    self.keybinds[(action, idx)] = keybind
            self.grid.append((action, label, binds))
        super().__init__(app, app.window)

    @property
    def ui_args(self):
        return {
            'grid': self.grid,
            'click_cb': self.click_cb,
        }

    def click_cb(self, action, idx):
        KeyChooser(parent=self.ui,
                   keymap=self.keymap,
                   action=action,
                   idx=idx,
                   keybind=self.keybinds.get((action, idx)),
                   accept_cb=self.update_keybind).run()

    def update_keybind(self, action, idx, keybind):
        old_keybind = self.keybinds.pop((action, idx), None)
        if old_keybind:
            del self.keymap[old_keybind]

        if keybind is not None:
            if keybind in self.keymap:
                old_action, old_idx = self.keymap[keybind]
                self.update_keybind(old_action, old_idx, None)
            self.keybinds[(action, idx)] = keybind
            self.keymap[keybind] = (action, idx)

        self.updates[(action, idx)] = keybind
        self.ui.update_keybind(action, idx, keybind)
        self.data_updated()

    def dirty(self):
        return bool(self.updates)

    def commit(self):
        for (action, idx), bind in self.updates.items():
            self.app.keybinds.save_keybind(action, idx, bind)
        self.updates = {}
