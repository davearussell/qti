import pygame

from xui.widgets import Widget, HBox, LineEdit


class Sample(Widget):
    fixed_width = True
    fixed_height = True
    side_length = 10

    @property
    def width(self):
        return self.side_length

    @property
    def height(self):
        return self.side_length

    def set_value(self, value):
        try:
            self.color = pygame.Color(value)
        except (AttributeError, ValueError):
            self.color = 'black'

    def draw(self):
        super().draw()
        self.surface.fill(self.color)


class ColorPicker(HBox):
    spacing = 5

    def __init__(self, update_cb, commit_cb):
        self.update_cb = update_cb
        self.box = LineEdit(update_cb=self.color_update, commit_cb=commit_cb,
                            num_chars=LineEdit.num_chars - 2)
        self.sample = Sample(side_length=self.box.max_height())
        super().__init__([self.sample, self.box])

    def focus(self):
        self.box.focus()

    def color_update(self, value):
        self.sample.set_value(value)
        self.update_cb(value)

    def get_value(self):
        return self.box.get_value()

    def set_value(self, value):
        self.box.set_value(value)
        self.sample.set_value(value)

    def draw(self):
        self.box.color = self.color
        super().draw()
