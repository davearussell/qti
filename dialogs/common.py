class Dialog:
    ui_cls = None
    ui_args = {}
    title = 'Dialog'
    actions = {
        'accept': None,
        'cancel': None,
    }

    def __init__(self, parent):
        self.parent = parent
        self.action_cbs = {
            'accept': self.accept,
            'cancel': self.cancel,
            'apply': self.apply,
        }
        self.ui = self.make_ui()

    @property
    def common_ui_args(self):
        return {
            'parent': self.parent,
            'title': self.title,
            'actions': self.actions,
            'action_cb': self._action_cb,
            'keydown_cb': self.keydown_cb,
        }

    def make_ui(self):
        return self.ui_cls(**(self.common_ui_args | self.ui_args))

    def _action_cb(self, action):
        self.action_cbs[action]()

    def keydown_cb(self, keystroke):
        return False

    def run(self):
        self.ui.run()

    def accept(self):
        self.ui.accept(from_app=True)

    def cancel(self):
        self.ui.reject(from_app=True)

    def apply(self):
        raise NotImplementedError()
