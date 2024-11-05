from xui.widgets import Widget

class ViewerWidget(Widget):
    def __init__(self, app, mouse_cb):
        super().__init__()
        self.app = app
        self.mouse_cb = mouse_cb

    def load(self, image):
        pass
