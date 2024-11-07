import time

import pygame

from xui.widgets import Widget

from ..cache import ensure_cached
from .image import Image


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
        cell.border_rect = pygame.Rect(cell_x, cell_y,
                                       col_width - spacing, row_height - spacing)
        cell.contents_rect = pygame.Rect(cell_x + border_width, cell_y + border_width,
                                         cell_width, cell_height)
        cell.spacing_rect = pygame.Rect(cell_x - spacing, cell_y - spacing,
                                        col_width + spacing, row_height + spacing)

    return grid


class Cell:
    def __init__(self, grid, ctx, image_path):
        self.grid = grid
        self.image_path = image_path
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
        size = self.grid.cell_size
        image = Image(ensure_cached(self.image_path, size))
        return image.center(size).image


class GridWidget(Widget):
    renderer = Cell
    spacing = 10
    cell_border_thickness = 2
    supports_viewport = True
    fixed_height = True
    greedy_width = True

    cell_size = (100, 100)
    select_color = 'yellow'
    mark_color = 'orange'

    double_click_period = 0.5

    def __init__(self, app, click_cb):
        super().__init__()
        self.renderer_ctx = None
        self.app = app
        self.click_cb = click_cb
        self.cells = []
        self.grid = []
        self.target_i = None
        self.mark_i = None
        self.yoff = 0
        self.last_click = (0, None) # (timestamp, cell_i)

    def set_renderer(self, cls, ctx=None):
        self.renderer = cls
        if ctx is not None:
            self.renderer_ctx = ctx

    def set_mark_i(self, mark_i):
        self.mark_i = mark_i
        self.redraw()

    def set_target_i(self, target_i, ensure_visible=False):
        self.target_i = target_i
        if self.viewport and ensure_visible and target_i is not None:
            self.parent.ensure_visible(self.cells[target_i].spacing_rect)
        self.redraw()

    def width_updated(self):
        self.setup_grid()
        self.set_target_i(self.target_i, ensure_visible=True)

    def setup_grid(self):
        self.grid = layout_cells(self.cells, self.width, self.cell_size,
                                 self.spacing, self.cell_border_thickness)
        self.height = self.cells[-1].spacing_rect.bottom if self.cells else 0

    def cell_grid(self):
        return self.grid

    def load(self, cell_dicts):
        self.mark_i = None
        self.cells = [self.renderer(self, self.renderer_ctx, **cell_dict)
                      for cell_dict in cell_dicts]
        self.setup_grid()
        self.redraw()

    def handle_mouse_down(self, button, pos):
        if button != 'left' or not self.cells:
            return
        x, y = pos
        col_width = self.cell_size[0] + 2 * self.cell_border_thickness + self.spacing
        row_height = self.cell_size[1] + 2 * self.cell_border_thickness + self.spacing
        row, yrem = divmod(y, row_height)
        col, xrem = divmod(x, col_width)
        if xrem < self.spacing or yrem < self.spacing:
            return # Ignore clicks in space between cells
        cell_i = row * len(self.grid[0]) + col
        if cell_i < len(self.cells):
            last_time, last_i = self.last_click
            now = time.time()
            is_double = last_i == cell_i and now - last_time < self.double_click_period
            self.click_cb(cell_i, is_double=is_double)
            self.last_click = (0 if is_double else now, cell_i)

    def draw(self):
        super().draw()
        if self.viewport:
            top = self.viewport.top
            bottom = self.viewport.bottom
        else:
            top = 0
            bottom = self.height

        if self.mark_i is None:
            mark_lo = mark_hi = self.target_i
        else:
            mark_lo, mark_hi = min(self.mark_i, self.target_i), max(self.mark_i, self.target_i)

        for cell in self.cells:
            if cell.border_rect.bottom < top:
                continue
            if cell.border_rect.top >= bottom:
                break
            self.surface.blit(cell.contents(), cell.contents_rect.move(0, -top))
            if mark_lo <= cell.index <= mark_hi:
                color = self.select_color if cell.index == self.target_i else self.mark_color
                pygame.draw.rect(self.surface, color, cell.border_rect.move(0, -top),
                                 self.cell_border_thickness)
