from xui.widgets import VBox

class BrowserWidget(VBox):
    def __init__(self, app, grid, viewer, status_bar, pathbar, keydown_cb):
        super().__init__([pathbar, grid, status_bar])
        self.app = app
        self.keydown_cb = keydown_cb
        self.grid = grid
        self.viewer = viewer
        self.pathbar = pathbar
        self.status_bar = status_bar

    def set_mode(self, mode):
        pass

    def set_bar_visibility(self, hidden):
        pass

    def handle_keydown(self, keystroke):
        return self.keydown_cb(keystroke)
