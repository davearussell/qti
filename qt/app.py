from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtGui import QImageReader

from . import keys


class Window(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app

    def keyPressEvent(self, event):
        self.app.keydown_hook(keys.event_keystroke(event))


class QTApp(QApplication):
    def __init__(self, keydown_hook, exit_hook):
        self.keydown_hook = keydown_hook
        self.exit_hook = exit_hook
        super().__init__([])
        QImageReader.setAllocationLimit(0)
        self.size = self.primaryScreen().size()
        self.window = Window(self)

    def set_main_widget(self, widget):
        self.window.setCentralWidget(widget)

    def run(self):
        self.window.setFixedSize(self.size)
        self.window.showFullScreen()
        self.exec()
        self.exit_hook()
