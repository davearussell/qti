import pygame

from xui.widgets import Widget

from ..cache import ensure_cached

class Viewer(Widget):
    greedy_width = True
    greedy_height = True

    def load(self, path):
        self.path = path
        self.redraw()

    def draw(self):
        super().draw()
        img_surface = pygame.image.load(ensure_cached(self.path, self.size))
        img_width, img_height = img_surface.get_size()
        xoff = (self.width - img_width) // 2
        yoff = (self.height - img_height) // 2
        self.surface.blit(img_surface, (xoff, yoff))
