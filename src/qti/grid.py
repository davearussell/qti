from .qt.grid import GridWidget


class Grid:
    def __init__(self, settings, scroll_cb=None, select_cb=None, unselect_cb=None, no_selection=False):
        self.scroll_cb = scroll_cb or (lambda x: None)
        self.select_cb = select_cb or (lambda x: None)
        self.unselect_cb = unselect_cb or (lambda: None)
        self.ui = GridWidget(settings, click_cb=self.handle_click)
        self.target_i = None
        self.mark_i = None
        self.no_selection = no_selection
        self.action_map = {
            'up': self.scroll,
            'down': self.scroll,
            'left': self.scroll,
            'right': self.scroll,
            'top': self.scroll,
            'bottom': self.scroll,
            }
        if not self.no_selection:
            self.action_map.update({
                'select': self.select_current_target,
                'unselect': self.unselect,
                'mark': self.set_mark,
                'cancel': self.clear_mark,
            })

    def set_mark(self, _action=None):
        self.mark_i = self.target_i
        self.ui.set_mark_i(self.mark_i)

    def clear_mark(self, _action=None):
        self.mark_i = None
        self.ui.set_mark_i(None)

    def handle_click(self, cell_i, is_double):
        if is_double and not self.no_selection:
            self.select_cb(cell_i)
        else:
            self.set_target_index(cell_i, ensure_visible=False)

    def target_index(self):
        return self.target_i

    def marked_range(self):
        mark = self.mark_i if self.mark_i is not None else self.target_i
        if mark is None:
            return []
        lo, hi = sorted([mark, self.target_i])
        return range(lo, hi + 1)

    def load(self, cells, target_i=None):
        self.clear_mark()
        if cells and target_i is None:
            target_i = 0
        self.ui.load(cells)
        self.set_target_index(target_i)

    def set_target_index(self, target_i, ensure_visible=True):
        self.target_i = target_i
        self.ui.set_target_i(self.target_i, ensure_visible=ensure_visible)
        self.scroll_cb(self.target_i)

    def unselect(self, _action=None):
        self.unselect_cb()

    def select_current_target(self, _action=None):
        if self.target_i is not None:
            self.select_cb(self.target_i)

    def neighbour(self, direction):
        return self.ui.neighbour(self.target_i, direction)

    def scroll(self, direction):
        if self.target_i is not None:
            self.set_target_index(self.neighbour(direction))

    def handle_action(self, action):
        if action in self.action_map:
            self.action_map[action](action)
            return True
        return False

    def handle_mouse(self, *args):
        return False # Any relevent mouse events will be caught by self.ui and handled there
