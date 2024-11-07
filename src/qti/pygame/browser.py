import pygame

from xui.widgets import VBox, ScrollArea

from .grid import Cell


class BrowserCell(Cell):
    def __init__(self, grid, ctx, label, count, **kwargs):
        super().__init__(grid, ctx, **kwargs)
        self.browser = ctx
        self.label = label
        self.count = count

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
        self.grid.set_renderer(BrowserCell, ctx=self)

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
