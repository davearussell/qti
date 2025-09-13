from functools import partial

from xui.widgets import Dialog, HBox, Label, CheckBox


class DeleterDialog(Dialog):
    title = 'Delete'
    actions = ['no', 'yes']
    action_keybinds = {action[0]: action for action in actions}

    def __init__(self):
        super().__init__()
        self.nodes = self.app.browser.marked_nodes()
        if len(self.nodes) == 1:
            desc = '%s %r' % (self.nodes[0].type_label, self.nodes[0].name)
        else:
            desc = 'these %ss (%d)' % (self.nodes[0].type_label, len(self.nodes))
        if self.nodes[0].type in self.app.library.metadata.multi_value_keys():
            self.choices = [
                ('tree',    'e', 'Delete %s' % (desc,)),
                ('library', 'l', 'Delete images with %s' % (desc,)),
                ('disk',    'd', 'Also delete images from disk'),
            ]
        else:
            self.choices = [
                ('library', 'l', 'Delete %s' % (desc,)),
                ('disk',    'd', 'Also delete images from disk'),
            ]
        self.mode_keybinds = {keybind: i for i, (_, keybind, _) in enumerate(self.choices)}
        self.choice_i = 0
        self.buttons = []

        for i, (choice, keybind, text) in enumerate(self.choices):
            label = Label(text, keybind=keybind)
            button = CheckBox(click_cb=partial(self.select_mode, i), checked=(i == 0))
            row = HBox([button, label], spacing=2, child_valign='center')
            self.body.children.append(row)
            self.buttons.append(button)

    def select_mode(self, choice_i):
        self.choice_i = choice_i
        for i, button in enumerate(self.buttons):
            button.set_checked(i == choice_i)

    def do_action(self, action):
        if action == 'yes':
            delete_mode = self.choices[self.choice_i][0]
            self.app.browser.delete_nodes(self.nodes, propagate=delete_mode)
        self.exit()

    def handle_keydown(self, keystroke):
        if keystroke in self.mode_keybinds:
            self.select_mode(self.mode_keybinds[keystroke])
            return True
        return super().handle_keydown(keystroke)
