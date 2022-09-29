from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt, QObject, Signal


class StatusBarWidget(QWidget):
    background_opacity = 0.5

    def __init__(self, text=''):
        super().__init__()
        font = self.font()
        font.setPointSize(16)
        self.setFont(font)
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(0, 0, 0, int(255 * self.background_opacity)))
        self.setPalette(palette)

        self.setLayout(QHBoxLayout())
        self.label = QLabel()
        palette = self.label.palette()
        palette.setColor(QPalette.WindowText, Qt.white)
        self.label.setPalette(palette)
        self.set_text(text)
        self.layout().addWidget(self.label)

    def set_text(self, text):
        self.label.setText(text)


class StatusBar(QObject):
    text_update = Signal(str)

    def __init__(self):
        super().__init__()
        self.text = ''

    def set_text(self, text):
        self.text = text
        self.text_update.emit(text)

    def make_widget(self):
        bar = StatusBarWidget()
        self.text_update.connect(bar.set_text)
        return bar
