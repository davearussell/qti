import copy

SCROLL_ACTIONS = ['up', 'down', 'left', 'right', 'top', 'bottom', 'prev', 'next']


DEFAULT_KEYBINDS = {
    'up':    ['up',    'KP-5'],
    'down':  ['down',  'KP-2'],
    'left':  ['left',  'KP-1'],
    'right': ['right', 'KP-3'],

    'top':    ['home'],
    'bottom': ['end'],

    'swap_up':     ['CTRL-up'],
    'swap_down':   ['CTRL-down'],
    'swap_left':   ['CTRL-left'],
    'swap_right':  ['CTRL-right'],

    'prev':  ['pageup',   'KP-4'],
    'next':  ['pagedown', 'KP-6'],

    'select':   ['return',    'KP-enter'],
    'unselect': ['backspace', 'KP-0'],
    'mark':     ['space'],
    'cancel':   ['escape'],

    'toggle_hide':        ['h'],
    'quit':               ['q'],
    'edit':               ['e'],
    'bulk_edit':          ['b'],
    'filter_config':      ['v'],
    'delete':             ['d'],
    'edit_metadata':      ['m'],
    'app_settings':       ['a'],
    'edit_keybinds':      ['k'],
    'edit_macros':        ['f'],
    'edit_quick_actions': ['g'],
    'auto_scroll':        ['CTRL-a'],
    'search':             ['CTRL-f'],

    'reset_zoom': ['CTRL-r'],

    'save_snapshot':    ['s'],
    'restore_snapshot': ['r'],

    'add_new_images': ['n'],
}


class Keybinds:
    binds_per_action = 2

    def __init__(self, store):
        self.store = store
        self.actions = copy.deepcopy(DEFAULT_KEYBINDS)
        for action, bindings in self.actions.items():
            if len(bindings) < self.binds_per_action:
                bindings += [None] * (self.binds_per_action - len(bindings))
        self.bindings = self.load_bindings()

    def load_bindings(self):
        bindings = {}
        for action, action_bindings in self.actions.items():
            for idx in range(len(action_bindings)):
                k = 'keybind_%s_%d' % (action, idx)
                if self.store.contains(k):
                    action_bindings[idx] = self.store.get(k)
                bindings[action_bindings[idx]] = action
        return bindings

    def add_action(self, action):
        assert action not in self.actions, action
        self.actions[action] = [None] * self.binds_per_action
        for idx in range(self.binds_per_action):
            k = 'keybind_%s_%d' % (action, idx)
            binding = self.store.get(k)
            if binding in self.bindings:
                self.store.remove(k)
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

        qk = 'keybind_%s_%d' % (action, idx)
        if binding is None:
            self.store.remove(qk)
        else:
            self.store.set(qk, binding)

    def get_action(self, keystroke):
        return self.bindings.get(keystroke)

    def is_scroll(self, action):
        return action in SCROLL_ACTIONS
