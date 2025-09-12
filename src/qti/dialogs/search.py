from xui.widgets import Dialog, Label, LineEdit


class SearchDialog(Dialog):
    title = "Search"
    actions = ['done']
    action_keybinds = {
        'escape': 'done',
        'CTRL-return': 'done',
    }

    def __init__(self):
        super().__init__()
        self.matches = []
        self.match_i = None
        self.nodes = self.app.browser.node.children
        self.label = Label('')
        self.edit = LineEdit(update_cb=self.search_text_changed, commit_cb=self.find_next)
        self.body.children = [self.label, self.edit]

    def do_action(self, action):
        self.exit()

    def focus(self):
        self.edit.focus()

    def update_label(self):
        if self.matches:
            node = self.nodes[self.matches[self.match_i]]
            self.app.browser.set_target(node)
            self.label.set_text('Match %d / %d: %s' % (
                self.match_i + 1, len(self.matches), node.name))
        else:
            self.label.set_text('No matches')

    def find_next(self):
        if self.matches:
            self.match_i = (self.match_i + 1) % len(self.matches)
            self.update_label()

    def search_text_changed(self, text):
        self.matches = [i for i, node in enumerate(self.nodes) if text and text in node.name]
        if self.matches:
            self.match_i = 0
            target_i = self.nodes.index(self.app.browser.get_target())
            for match_i, node_i in enumerate(self.matches):
                if node_i >= target_i:
                    self.match_i = match_i
                    break
        self.update_label()
