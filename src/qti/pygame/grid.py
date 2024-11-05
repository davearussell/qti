from xui.widgets import Widget

class GridWidget(Widget):
    def __init__(self, app, click_cb):
        super().__init__()
        self.app = app
        self.click_cb = click_cb

    def set_mark_i(self, mark_i):
        pass

    def set_target_i(self, target_i, ensure_visible=False):
        pass

    def neighbour(self, target_i, direction):
        pass

    def load(self, cells):
        pass
