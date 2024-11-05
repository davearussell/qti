from xui.widgets import Widget

class PathbarWidget(Widget):
    fixed_height = True
    height = 100

    def __init__(self, app, entry_clicked):
        super().__init__()
        self.app = app
        self.entry_clicked = entry_clicked

    def set_entries(self, entries):
        pass
