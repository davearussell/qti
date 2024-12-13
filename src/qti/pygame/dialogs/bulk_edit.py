import pygame

from xui.widgets import Widget, HBox, ScrollArea, ComboBox, LineEdit

from .common import DataDialogWidget


class Table(Widget):
    fixed_height = True
    supports_viewport = True

    margin = 10
    spacing = 10
    font = 'Liberation Mono'
    font_size = 16
    grid_color = (128, 128, 128)

    def __init__(self, rows, keys):
        self.rows = rows
        self.keys = keys
        self.refresh()
        super().__init__()
        self.resolve_size()

    def make_table(self):
        rows = [[key.title() for key in self.keys]]
        for row in self.rows:
            rows.append([str(row[key]) for key in self.keys])
        return rows

    def refresh(self):
        self.table = self.make_table()
        self.col_widths = [max(len(row[i]) for row in self.table)
                           for i in range(len(self.table[0]))]

    def max_width(self):
        n_cols = len(self.keys)
        max_chars = sum(self.col_widths)
        return 2 * self.margin + n_cols * self.spacing + max_chars * self.char_width + 1

    def resolve_size(self):
        self.font = pygame.font.SysFont(self.font, self.font_size)
        self.char_width, self.char_height = self.font.render(' ', True, self.color).get_size()
        n_rows = len(self.table)
        self.height = 2 * self.margin + n_rows * (self.spacing + self.char_height) + 1

    def draw(self):
        super().draw()

        top = self.viewport.top if self.viewport else 0
        bottom = self.viewport.bottom if self.viewport else self.height

        body = pygame.Rect(0, 0, *self.size).inflate(-self.margin * 2, -self.margin * 2)
        body = body.move(0, -top)
        pygame.draw.rect(self.surface, self.grid_color, body, 1)

        x = self.margin
        for col_width in self.col_widths[:-1]:
            x += col_width * self.char_width + self.spacing
            pygame.draw.line(self.surface, self.grid_color, (x, body.top), (x, body.bottom - 1))

        y = self.margin
        for _ in self.table[:-1]:
            y += self.char_height + self.spacing
            if y > bottom:
                break
            if y >= top:
                pygame.draw.line(self.surface, self.grid_color,
                                 (body.left, y - top), (body.right - 1, y - top))

        y = self.margin + self.spacing // 2
        for row in self.table:
            if y > bottom:
                break
            if y + self.char_height >= top:
                x = self.margin + self.spacing // 2
                for col_i, col_width in enumerate(self.col_widths):
                    self.surface.blit(self.font.render(row[col_i], True, self.color), (x, y - top))
                    x += self.spacing + self.char_width * col_width
            y += self.spacing + self.char_height


class BulkEditDialogWidget(DataDialogWidget):
    def __init__(self, keys, table, update_cb, **kwargs):
        super().__init__(**kwargs)
        self.keys = keys
        self.table = table
        self.update_cb = update_cb # (key, value)

        self.key_box = ComboBox(keys)
        self.line_edit = LineEdit(num_chars=20, commit_cb=self.handle_update)
        self.editor = HBox([self.key_box, self.line_edit],
                           child_valign='center', spacing=10)
        self.table = Table(self.table, self.keys)

        self.body.children = [
            self.editor,
            ScrollArea(self.table, right_bar=True),
        ]

    def handle_update(self):
        self.update_cb(self.key_box.choice, self.line_edit.get_value())
        self.focus()

    def refresh(self):
        self.table.refresh()

    def handle_keydown(self, keystroke):
        if keystroke == 'up':
            if self.key_box.choice_i > 0:
                self.key_box.set_choice_i(self.key_box.choice_i - 1)
        elif keystroke == 'down':
            if self.key_box.choice_i < len(self.key_box.choices) - 1:
                self.key_box.set_choice_i(self.key_box.choice_i + 1)
        elif keystroke == 'e':
            self.line_edit.focus()
            self.redraw()
        else:
            return super().handle_keydown(keystroke)
        return True
