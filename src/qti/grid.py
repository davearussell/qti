import pygame

from xui.widgets import Image, Grid

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
