from xui.widgets import HBox, ScrollArea

from .common import DataDialogWidget


class ImporterDialogWidget(DataDialogWidget):
    def __init__(self, fields, grid, **kwargs):
        super().__init__(**kwargs)
        self.fields = fields
        self.grid = grid
        self.body.children = [HBox([self.fields, ScrollArea(grid, right_bar=True)])]

    def focus(self):
        self.fields.focus()
