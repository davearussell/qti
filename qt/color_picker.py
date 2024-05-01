from PySide6.QtWidgets import QLabel, QColorDialog
from PySide6.QtGui import QPalette, QColor

from color import Color


class ColorPicker(QLabel):
    def __init__(self, update_cb, commit_cb):
        super().__init__()
        self.setContentsMargins(5, 5, 5, 5)
        self.setAutoFillBackground(True)
        self.update_cb = update_cb
        self.commit_cb = commit_cb

    def set_value(self, color):
        self.color = color
        self.setText("Click to edit [%s]" % color)
        self.apply_palette()

    def get_value(self):
        return self.color

    def apply_palette(self):
        pal = self.palette()
        pal.setColor(QPalette.Window, self.color)
        pal.setColor(QPalette.WindowText, self.color.contrasting())
        self.setPalette(pal)

    def pick_new_color(self):
        qcolor = QColorDialog.getColor(self.color)
        if qcolor.isValid():
            self.set_value(Color(qcolor.name()))
            self.update_cb()
            self.commit_cb()

    def mousePressEvent(self, event):
        self.pick_new_color()
