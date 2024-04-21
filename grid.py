from qt.grid import GridWidget


class Cell:
    def __init__(self, ui, label=None):
        self.ui = ui
        self.label = label


class Grid:
    def __init__(self, scroll_cb=None, select_cb=None, unselect_cb=None):
        self.scroll_cb = scroll_cb or (lambda x: None)
        self.select_cb = select_cb or (lambda x: None)
        self.unselect_cb = unselect_cb or (lambda: None)
        self.ui = GridWidget(click_cb=self.handle_click)
        self.cells = []
        self.target_i = None
        self.mark_i = None
        self.action_map = {
            'up': self.scroll,
            'down': self.scroll,
            'left': self.scroll,
            'right': self.scroll,
            'top': self.scroll,
            'bottom': self.scroll,
            'select': self.select_current_target,
            'unselect': self.unselect,
            'mark': self.set_mark,
            'cancel': self.clear_mark,
        }

    def set_mark(self, _action=None):
        self.mark_i = self.target_i
        self.ui.set_mark_i(self.mark_i)

    def clear_mark(self, _action=None):
        self.mark_i = None
        self.ui.set_mark_i(None)

    def handle_click(self, cell_i, is_double):
        cell = self.cells[cell_i]
        if is_double:
            self.select_target(cell)
        else:
            self.set_target(cell, ensure_visible=False)

    @property
    def target(self):
        return self.cells[self.target_i]

    def target_index(self):
        return self.target_i

    def marked_cells(self):
        mark = self.mark_i if self.mark_i is not None else self.target_i
        if mark is None:
            return []
        lo, hi = sorted([mark, self.target_i])
        return self.cells[lo : hi + 1]

    def load(self, cells, target):
        self.cells = cells
        self.ui.load([cell.ui for cell in cells])
        self.set_target(target)

    def cell_labels(self):
        return [cell.label for cell in self.cells]

    def set_target(self, cell, ensure_visible=True):
        self.target_i = None if cell is None else self.cells.index(cell)
        self.ui.set_target_i(self.target_i, ensure_visible=ensure_visible)
        self.scroll_cb(cell)

    def set_target_index(self, index):
        self.set_target(self.cells[index])

    def unselect(self, _action=None):
        self.unselect_cb()

    def select_target(self, cell):
        self.select_cb(cell)

    def select_current_target(self, _action=None):
        if self.target:
            self.select_target(self.target)

    def scroll(self, direction):
        if self.target:
            self.set_target_index(self.ui.neighbour(self.target_i, direction))

    def handle_action(self, action):
        if action in self.action_map:
            self.action_map[action](action)
            return True
        return False
