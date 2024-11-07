import pygame

from xui.widgets import Widget

from ..color import Color

class PathbarWidget(Widget):
    fixed_width = True
    fixed_height = True

    margin = 10
    spacing = 5
    sep_color = 'cyan'

    def __init__(self, app, entry_clicked):
        self._entries = []
        super().__init__()
        self.app = app
        self.entry_clicked = entry_clicked
        self.settings_updated()

    def resolve_size(self):
        self.height = 2 * self.margin + self.spacing + 2 * self.char_height
        self.width = 2 * self.margin + self.spacing * (2 * len(self._entries) - 2)
        for top, bottom, n_chars, _ in self._entries:
            self.width += self.char_width * (n_chars + 1)
        self.redraw()
        self.relayout()

    def settings_updated(self):
        self.char_width, self.char_height = self.render_text(' ').get_size()
        self.fade_color = Color(self.color).fade()
        self.fade_sep_color = Color(self.sep_color).fade()
        self.resolve_size()
        self.top_y = self.margin
        self.bottom_y = self.top_y + self.char_height + self.spacing
        self.sep_y = (self.top_y + self.bottom_y) // 2

    def set_entries(self, entries):
        self.entries = entries
        self._entries = []
        for entry in entries:
            counts = "[%d / %d]" % (entry.index + 1, entry.total)
            n_chars = max(len(entry.name), len(counts))
            self._entries.append((entry.name, counts, n_chars, entry.fade))
        self.resolve_size()

    def handle_mouse_down(self, button, pos):
        if button == 'left':
            for i, r in enumerate(self.entry_rects):
                if r.collidepoint(pos):
                    self.entry_clicked(self.entries[i])
            return True

    def draw(self):
        super().draw()
        self.entry_rects = []
        x = self.margin
        for i, (top, bottom, n_chars, fade) in enumerate(self._entries):
            if i:
                color = self.fade_sep_color if fade else self.sep_color
                self.surface.blit(self.render_text('>', color=color), (x, self.sep_y))
                x += self.char_width + self.spacing
            color = self.fade_color if fade else self.color
            self.surface.blit(self.render_text(top, color=color), (x, self.top_y))
            self.surface.blit(self.render_text(bottom, color=color), (x, self.bottom_y))
            r = pygame.Rect(x, self.top_y, n_chars * self.char_width, self.height - 2 * self.margin)
            self.entry_rects.append(r)
            x += n_chars * self.char_width + self.spacing
