import pygame

from .. import image

class Image(image.Image):
    def load(self, path):
        try:
            return pygame.image.load(path)
        except:
            s = pygame.Surface(self.size, pygame.SRCALPHA)
            diameter = min(self.size)
            radius = diameter // 2
            center = (radius, radius)
            diag = ((2 ** .5) - 1) * radius
            offset = (diag * diag / 2) ** .5 + 4
            pygame.draw.circle(s, 'red', center, radius, 8)
            pygame.draw.line(s, 'red', (offset, offset), (diameter - offset, diameter - offset), 10)
            return s

    def get_size(self):
        return self.image.get_size()

    def scale(self, size):
        image_size = self.size
        ratio = min(size[0] / image_size[0], size[1] / image_size[1])
        scaled_size = (int(image_size[0] * ratio), int(image_size[1] * ratio))
        scaled_image = pygame.transform.smoothscale(self.image, scaled_size)
        return type(self)(scaled_image)

    def crop_and_pan(self, size, x, y, background_color=None):
        viewport = pygame.Surface(size, pygame.SRCALPHA)
        if background_color:
            viewport.fill(background_color)
        viewport.blit(self.image, (x, y))
        return type(self)(viewport)
