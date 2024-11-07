from . import ui
from .cache import ensure_cached


class Cell:
    image_cls = None # subclasses must set these
    rect_cls = None

    def __init__(self, settings, image_path, size):
        self.settings = settings
        self.image_path = image_path
        self.size = size
        self._contents = None
        self.row = None
        self.col = None
        self.index = None
        self.border_rect = None
        self.contents_rect = None
        self.spacing_rect = None

    def contents(self):
        if self._contents is None:
            self._contents = self.render()
        return self._contents

    def render(self):
        image = self.image_cls(ensure_cached(self.image_path, self.size))
        return image.center(self.size, background_color=self.settings.background_color).image


def layout_cells(cells, grid_width, cell_size, spacing, border_width):
    cell_width, cell_height = cell_size
    col_width = cell_width + 2 * border_width + spacing
    row_height = cell_height + 2 * border_width + spacing
    n_cols = max(1, (grid_width - spacing) // col_width)

    grid = []
    for i, cell in enumerate(cells):
        cell.index = i
        cell.row, cell.col = divmod(i, n_cols)
        if cell.row >= len(grid):
            grid.append([])
        assert len(grid[cell.row]) == cell.col
        grid[cell.row].append(cell)
        cell_x = spacing + cell.col * col_width
        cell_y = spacing + cell.row * row_height
        cell.border_rect = cell.rect_cls(cell_x, cell_y,
                                         col_width - spacing, row_height - spacing)
        cell.contents_rect = cell.rect_cls(cell_x + border_width, cell_y + border_width,
                                           cell_width, cell_height)
        cell.spacing_rect = cell.rect_cls(cell_x - spacing, cell_y - spacing,
                                          col_width + spacing, row_height + spacing)

    return grid


class Grid:
    def __init__(self, app, scroll_cb=None, select_cb=None, unselect_cb=None, no_selection=False):
        self.scroll_cb = scroll_cb or (lambda x: None)
        self.select_cb = select_cb or (lambda x: None)
        self.unselect_cb = unselect_cb or (lambda: None)
        self.ui = ui.cls('grid')(app.ui, click_cb=self.handle_click)
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
        grid = self.ui.cell_grid()
        n_cols = len(grid[0])
        row, col = divmod(self.target_i, n_cols)
        cell = grid[row][col]
        if direction in ('left', 'right'):
            offset = (1 if direction == 'right' else -1)
            col = (col + offset) % len(grid[row])
        elif direction in ('up', 'down'):
            offset = (1 if direction == 'down' else -1)
            row = (row + offset) % len(grid)
            if col >= len(grid[row]):
                col = len(grid[row]) - 1
        elif direction in ('top', 'bottom'):
            row = col = (0 if direction == 'top' else -1)
        return grid[row][col].index

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
