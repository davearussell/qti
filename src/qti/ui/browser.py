import pygame

from xui.widgets import VBox, VSpacer, ScrollArea

from .grid import Cell
from ..color import Color

CELL_CACHE_LIMIT = 5000
CELL_CACHE = {} # (image_path, label, count) -> surface

class BrowserCell(Cell):
    def __init__(self, grid, ctx, label, count, **kwargs):
        super().__init__(grid, ctx, **kwargs)
        self.browser = ctx
        self.label = label
        self.count = count
        self._contents = CELL_CACHE.get((self.image_path, label, count))

    def render(self):
        surface = super().render()
        fade_color = (*self.grid.screen.bgcolor.rgb, 128)

        if self.label:
            font = pygame.font.SysFont(self.browser.font, self.browser.name_size)
            text = font.render(self.label, True, self.browser.color)
            text_rect = text.get_rect()
            text_rect.midtop = surface.get_rect().midtop
            if text_rect.left < 0:
                text_rect.left = 0 # truncate overlength names on the right
            fade = pygame.Surface(text_rect.size, pygame.SRCALPHA)
            fade.fill(fade_color)
            fade.blit(text, (0, 0))
            surface.blit(fade, text_rect)

        if self.count:
            font = pygame.font.SysFont(self.browser.font, self.browser.count_size)
            text = font.render(str(self.count), True, self.browser.color)
            text_rect = text.get_rect()
            text_rect.bottomright = surface.get_rect().bottomright
            fade = pygame.Surface(text_rect.size, pygame.SRCALPHA)
            fade.fill(fade_color)
            fade.blit(text, (0, 0))
            surface.blit(fade, text_rect)

        if len(CELL_CACHE) < CELL_CACHE_LIMIT:
            CELL_CACHE[(self.image_path, self.label, self.count)] = surface
        return surface


class BrowserWidget(VBox):
    name_size = 14
    count_size = 30

    def __init__(self, app, grid, viewer, status_bar, pathbar, keydown_cb):
        self.mode = None
        super().__init__()
        self.app = app
        self.keydown_cb = keydown_cb
        self.grid = grid
        self.scroll = ScrollArea(self.grid, right_bar=True, greedy_height=True)
        self.viewer = viewer
        self.pathbar = ScrollArea(pathbar, horizontal=True, greedy_width=True)
        self.status_bar = status_bar
        self.overlay = VBox([self.pathbar, VSpacer(), self.status_bar], bgcolor=(0, 0, 0, 0))
        self.show_bars = True
        self.grid.set_renderer(BrowserCell, ctx=self)

    def set_mode(self, mode):
        self.mode = mode
        overlay_on = self.overlay in self.screen.children
        want_overlay = mode == 'viewer' and self.show_bars
        if overlay_on != want_overlay:
            if want_overlay:
                i = self.screen.children.index(self)
                self.screen.children.insert(i + 1, self.overlay)
            else:
                self.screen.children.remove(self.overlay)

        if mode == 'grid':
            self.pathbar.bgcolor = self.status_bar.bgcolor = Color(self.screen.bgcolor).fade()
            if self.show_bars:
                self.children = [self.pathbar, self.scroll, self.status_bar]
            else:
                self.children = [self.scroll]
        else:
            self.pathbar.bgcolor = self.status_bar.bgcolor = (0, 0, 0, 128)
            self.children = [self.viewer]
        self.relayout()
        self.redraw()

    def apply_child_settings(self, settings):
        self.pathbar.apply_settings(settings)
        self.status_bar.apply_settings(settings)
        self.scroll.apply_settings(settings)
        self.viewer.apply_settings(settings)
        self.set_mode(self.mode)

    def set_bar_visibility(self, hidden):
        self.show_bars = not hidden
        self.set_mode(self.mode)

    def handle_keydown(self, keystroke):
        return self.keydown_cb(keystroke)

    def prefetch(self, cell):
        BrowserCell(self.grid, self, **cell).contents()
