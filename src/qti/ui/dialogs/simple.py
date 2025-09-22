from xui.widgets import Label

from .common import DialogWidget


class LabelDialogWidget(DialogWidget):
    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.body.children = [Label(text)]
