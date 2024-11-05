from xui.widgets import Widget

class StatusBarWidget(Widget):
    fixed_height = True
    height = 50

    def __init__(self, app):
        super().__init__()
        self.app = app

    def set_text(self, text):
        print("Status: %r" % (text,))
