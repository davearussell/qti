from xui.widgets import VBox, ScrollArea

from .grid import Cell


class BrowserCell(Cell):
    def __init__(self, grid, label, count, **kwargs):
        super().__init__(grid, **kwargs)
        self.label = label
        self.count = count


class BrowserWidget(VBox):
    def __init__(self, app, grid, viewer, status_bar, pathbar, keydown_cb):
        self.mode = None
        super().__init__()
        self.app = app
        self.keydown_cb = keydown_cb
        self.grid = grid
        self.scroll = ScrollArea(self.grid, right_bar=True, greedy_height=True)
        self.viewer = viewer
        self.pathbar = pathbar
        self.status_bar = status_bar
        self.grid.set_renderer(BrowserCell)

    def set_mode(self, mode):
        if mode == 'grid':
            self.children = [self.scroll]
        else:
            self.children = [self.viewer]
        self.relayout()
        self.redraw()

    def apply_child_settings(self, settings):
        self.pathbar.apply_settings(settings)
        self.status_bar.apply_settings(settings)
        self.scroll.apply_settings(settings)
        self.viewer.apply_settings(settings)

    def set_bar_visibility(self, hidden):
        pass

    def handle_keydown(self, keystroke):
        return self.keydown_cb(keystroke)
