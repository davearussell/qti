from xui.widgets import HBox, HSpacer, Label

class StatusBarWidget(HBox):
    margin = 10

    def __init__(self, app):
        self.label = Label('')
        super().__init__([self.label, HSpacer()])

    def set_text(self, text):
        self.label.set_text(text)

    def apply_child_settings(self, settings):
        self.label.apply_settings(settings | {'font_size': self.font_size})
