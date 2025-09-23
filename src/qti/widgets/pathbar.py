import pygame

from xui.widgets import Widget, ScrollArea


class PathbarBody(Widget):
    fixed_width = True
    fixed_height = True

    margin = 10
    spacing = 5
    sep_color = 'cyan'

    def __init__(self, click_cb):
        self.click_cb = click_cb
        self.nodes = []
        self.words = []
        self.mouse_rects = []
        self.fade_target = False
        super().__init__()
        self.render()

    def settings_updated(self):
        self.render()

    def set_target(self, node, fade):
        self.nodes = []
        self.fade_target = fade
        while node and node.parent:
            self.nodes.insert(0, node)
            node = node.parent
        self.render()

    def render(self):
        _, char_height = self.render_text(' ').get_size()

        self.words = []
        self.mouse_rects = []
        top_y = self.margin
        bottom_y = top_y + char_height + self.spacing
        mid_y = (top_y + bottom_y) // 2
        x = self.margin

        if not self.nodes:
            text = self.render_text("No images found")
            rect = text.get_rect()
            rect.topleft = (x, top_y)
            self.words.append((text, rect))
            self.width = rect.right + self.margin
            self.height = rect.bottom + self.margin
            self.redraw()
            self.relayout()
            return

        for i, node in enumerate(self.nodes):
            fade = self.fade_target and i == len(self.nodes) - 1
            color = pygame.Color(self.color).lerp('black', 0.5) if fade else self.color
            sep_color = pygame.Color(self.sep_color).lerp('black', 0.5) if fade else self.sep_color

            if i > 0:
                sep_text = self.render_text('>', color=sep_color)
                sep_rect = sep_text.get_rect()
                sep_rect.topleft = (x, mid_y)
                self.words.append((sep_text, sep_rect))
                x = sep_rect.right + self.spacing

            top_text = self.render_text(node.name, color=color)
            top_rect = top_text.get_rect()
            top_rect.topleft = (x, top_y)
            self.words.append((top_text, top_rect))

            bottom_text = self.render_text("[%d / %d]" % (node.parent.children.index(node) + 1,
                                                          len(node.parent.children)),
                                           color=color)
            bottom_rect = bottom_text.get_rect()
            bottom_rect.topleft = (x, bottom_y)
            self.words.append((bottom_text, bottom_rect))

            mouse_rect = top_rect.union(bottom_rect)
            self.mouse_rects.append(mouse_rect)
            x = mouse_rect.right + self.spacing

        self.width = self.height = self.margin
        if self.nodes:
            self.width += self.mouse_rects[-1].right
            self.height += self.mouse_rects[-1].bottom

        self.relayout()
        self.redraw()

    def handle_mouse_down(self, button, pos):
        if button == 'left':
            for rect, node in zip(self.mouse_rects, self.nodes):
                if rect.collidepoint(pos):
                    self.click_cb(node)

    def draw(self):
        super().draw()
        for surface, rect in self.words:
            self.surface.blit(surface, rect)


class Pathbar(ScrollArea):
    horizontal = True
    greedy_width = True

    def __init__(self, click_cb):
        super().__init__(PathbarBody(click_cb))

    def set_target(self, target, fade):
        self.body.set_target(target, fade)
