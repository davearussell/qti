import pygame

from xui.widgets import Image, grid

from .cache import ensure_cached


class Thumbnail(Image):
    def __init__(self, browser, node):
        self.browser = browser
        self.node = node
        if node.children:
            self._path = next(node.images()).abspath
            self.name = node.name
            self.count = str(len(node.children))
        else:
            self._path = node.abspath
            self.name = self.count = None
        super().__init__(None, browser.app.settings.thumbnail_size)

    def draw(self):
        self.path = ensure_cached(self._path, self.size)
        super().draw()

        fade_color = (*pygame.Color(self.browser.app.settings.background_color).rgb, 128)

        if self.name:
            text = self.browser.render_text(self.name, size=self.browser.name_size)
            rect = text.get_rect()
            rect.midtop = self.surface.get_rect().midtop
            rect.left = max(rect.left, 0) # truncate long names on the right
            fade = pygame.Surface(rect.size, pygame.SRCALPHA)
            fade.fill(fade_color)
            fade.blit(text, (0, 0))
            self.surface.blit(fade, rect)

        if self.count:
            text = self.browser.render_text(self.count, size=self.browser.count_size)
            rect = text.get_rect()
            rect.bottomright = self.surface.get_rect().bottomright
            fade = pygame.Surface(rect.size, pygame.SRCALPHA)
            fade.fill(fade_color)
            fade.blit(text, (0, 0))
            self.surface.blit(fade, rect)


class Grid(grid.Grid):
    mark_i = None
    mark_color = 'orange'

    def set_mark(self):
        self.mark_i = self.target_i
        self.redraw()

    def clear_mark(self):
        self.mark_i = None
        self.redraw()

    def marked_range(self):
        mark = self.mark_i if self.mark_i is not None else self.target_i
        if mark is None:
            return []
        lo, hi = sorted([mark, self.target_i])
        return range(lo, hi + 1)

    def load_cells(self, cells):
        self.clear_mark()
        super().load_cells(cells)

    def draw_cell(self, cell):
        cell_rect = super().draw_cell(cell)
        if self.mark_i is not None and cell.i != self.target_i:
            lo, hi = sorted([self.mark_i, self.target_i])
            if lo <= cell.i <= hi:
                self.draw_border(cell_rect, self.mark_color)
        return cell_rect
