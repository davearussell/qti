SCROLL_ACTIONS = ['up', 'down', 'left', 'right', 'prev', 'next']


KEYS = {} # KEY -> action
def load_keybinds(settings):
    global KEYS
    for key, binding in settings.to_dict().items():
        if key.startswith('keybind') and binding is not None:
            action = '_'.join(key.split('_')[1:-1]) # 'keybind_<action>_<idx>'
            if binding in KEYS:
                raise Exception("Duplicate keybind %s (%s, %s)" % (binding, KEYS[binding], action))
            KEYS[binding] = action


def get_keybind(settings, action, idx):
    k = 'keybind_%s_%d' % (action, idx)
    return settings.get(k)


def save_keybind(settings, action, idx, binding):
    k = 'keybind_%s_%d' % (action, idx)
    settings.set(k, binding)


def get_action(event):
    k = (event.key(), event.modifiers())
    return KEYS.get(k)


class KeyMap:
    def __init__(self):
        self.keys = {}

    def assign_keybind(self, word):
        for char in word.upper():
            if char not in self.keys:
                self.keys[char] = word
                return char
        raise Exception("Cannot find a free free keybind for %r" % (word,))
