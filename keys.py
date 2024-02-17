import copy
from PySide6.QtCore import Qt

SCROLL_ACTIONS = ['up', 'down', 'left', 'right', 'top', 'bottom', 'prev', 'next']


DEFAULT_KEYBINDS = {
    #Action   First bind     Second bind(key, modifier)
    'up':    [Qt.Key_Up,    (Qt.Key_5, Qt.KeypadModifier)],
    'down':  [Qt.Key_Down,  (Qt.Key_2, Qt.KeypadModifier)],
    'left':  [Qt.Key_Left,  (Qt.Key_1, Qt.KeypadModifier)],
    'right': [Qt.Key_Right, (Qt.Key_3, Qt.KeypadModifier)],

    'top':    [Qt.Key_Home],
    'bottom': [Qt.Key_End],

    'swap_up':  [(Qt.Key_Up, Qt.ControlModifier)],
    'swap_down':  [(Qt.Key_Down, Qt.ControlModifier)],
    'swap_left':  [(Qt.Key_Left, Qt.ControlModifier)],
    'swap_right':  [(Qt.Key_Right, Qt.ControlModifier)],

    'prev':  [Qt.Key_PageUp,   (Qt.Key_4, Qt.KeypadModifier)],
    'next':  [Qt.Key_PageDown, (Qt.Key_6, Qt.KeypadModifier)],

    'select':   [Qt.Key_Return,    (Qt.Key_Enter, Qt.KeypadModifier)],
    'unselect': [Qt.Key_Backspace, (Qt.Key_0, Qt.KeypadModifier)],
    'mark':     [Qt.Key_Space],
    'cancel':   [Qt.Key_Escape],

    'toggle_hide':   [Qt.Key_H],
    'quit':          [Qt.Key_Q],
    'edit':          [Qt.Key_E],
    'bulk_edit':     [Qt.Key_B],
    'filter_config': [Qt.Key_V],
    'delete':        [Qt.Key_D],
    'edit_metadata': [Qt.Key_M],
    'app_settings':  [Qt.Key_A],
    'edit_keybinds': [Qt.Key_K],
    'edit_quick_filters': [Qt.Key_F],
    'edit_quick_actions': [Qt.Key_G],
    'auto_scroll': [(Qt.Key_A, Qt.ControlModifier)],

    'reset_zoom':    [(Qt.Key_R, Qt.ControlModifier)],

    'save_snapshot':    [Qt.Key_S],
    'restore_snapshot': [Qt.Key_R],

    'add_new_images':   [Qt.Key_N],
}


class Keybinds:
    binds_per_action = 2

    def __init__(self, qsettings):
        self.q = qsettings
        self.actions = copy.deepcopy(DEFAULT_KEYBINDS)
        for action, bindings in self.actions.items():
            if len(bindings) < self.binds_per_action:
                bindings += [None] * (self.binds_per_action - len(bindings))
            for i in range(len(bindings)):
                if not isinstance(bindings[i], (tuple, type(None))):
                    bindings[i] = (bindings[i], Qt.KeyboardModifier(0))
        self.bindings = self.load_bindings()

    def load_bindings(self):
        bindings = {}
        for action, action_bindings in self.actions.items():
            for idx in range(len(action_bindings)):
                k = 'keybind_%s_%d' % (action, idx)
                if self.q.contains(k):
                    action_bindings[idx] = self.q.value(k)
                bindings[action_bindings[idx]] = action
        return bindings

    def add_action(self, action):
        assert action not in self.actions, action
        self.actions[action] = [None] * self.binds_per_action
        for idx in range(self.binds_per_action):
            k = 'keybind_%s_%d' % (action, idx)
            binding = self.q.value(k)
            if binding in self.bindings:
                self.q.setValue(k, None)
            else:
                self.actions[action][idx] = binding
                self.bindings[binding] = action

    def delete_action(self, action):
        assert action in self.actions, action
        for binding in self.actions[action]:
            if binding in self.bindings:
                del self.bindings[binding]
        del self.actions[action]

    def get_keybind(self, action, idx):
        return self.actions[action][idx]

    def save_keybind(self, action, idx, binding):
        old_binding = self.actions[action][idx]
        if old_binding == binding:
            return
        self.actions[action][idx] = binding
        self.bindings[binding] = action
        if old_binding:
            assert self.bindings.pop(old_binding) == action
        self.q.setValue('keybind_%s_%d' % (action, idx), binding)

    def get_action(self, event):
        binding = (event.key(), event.modifiers())
        return self.bindings.get(binding)

    def is_scroll(self, action):
        return action in SCROLL_ACTIONS


class KeyMap:
    def __init__(self):
        self.keys = {}

    def assign_keybind(self, word):
        for char in word.upper():
            if char not in self.keys:
                self.keys[char] = word
                return char
        raise Exception("Cannot find a free free keybind for %r" % (word,))
