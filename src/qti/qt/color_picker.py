from PySide6.QtWidgets import QWidget, QLabel, QColorDialog, QHBoxLayout
from PySide6.QtGui import QPalette, QColor

from ..color import Color
from .line_edit import LineEdit


class ColorClicker(QLabel):
    def __init__(self, update_cb, commit_cb):
        super().__init__()
        self.setAutoFillBackground(True)
        self.setText("[click]")
        self.update_cb = update_cb
        self.commit_cb = commit_cb

    def set_value(self, color):
        try:
            self.color = Color(color)
        except:
            pass
        self.apply_palette()

    def get_value(self):
        return self.color

    def apply_palette(self):
        pal = self.palette()
        pal.setColor(QPalette.Window, str(self.color))
        pal.setColor(QPalette.WindowText, str(self.color.contrasting()))
        self.setPalette(pal)

    def pick_new_color(self):
        qcolor = QColorDialog.getColor(str(self.color))
        if qcolor.isValid():
            self.set_value(Color(qcolor.name()))
            self.update_cb()
            self.commit_cb()

    def mousePressEvent(self, event):
        self.pick_new_color()


class ColorPicker(QWidget):
    def __init__(self, update_cb, commit_cb):
        super().__init__()
        self.update_cb = update_cb
        self.commit_cb = commit_cb
        self.setLayout(QHBoxLayout())
        self.clicker = ColorClicker(update_cb=self.update_cb, commit_cb=self.clicker_commit)
        self.box = LineEdit(update_cb=self.update_cb, commit_cb=self.box_commit)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(self.clicker)
        self.layout().addWidget(self.box)

    def box_commit(self):
        try:
            self.clicker.set_value(self.box.get_value())
        except ValueError:
            pass
        self.commit_cb()

    def clicker_commit(self):
        self.box.set_value(str(self.clicker.get_value()))
        self.update_cb()

    def focusInEvent(self, event):
        self.box.setFocus()

    def set_value(self, value):
        self.box.set_value(value)
        self.clicker.set_value(value)

    def get_value(self):
        return self.box.get_value()

    def set_property(self, key, value):
        self.box.set_property(key, value)

    def apply_palette(self):
        self.clicker.apply_palette()
