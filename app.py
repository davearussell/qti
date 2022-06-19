#! /bin/python3
import argparse
from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtGui import QPalette, QImageReader, QFont
from PySide6.QtCore import Qt

import library
import browser

JSON_PATH = "/home/dar/files/downloads/test/pictures/flat.json"


class Window(QMainWindow):
    size = (1600, 1000)

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setGeometry(200, 0, *self.size)
        self.setFixedSize(*self.size)
        self.setFont(QFont("Liberation mono"))
        pal = self.palette()
        pal.setColor(QPalette.Window, Qt.black)
        self.setPalette(pal)
        self.browser = browser.Browser()
        self.setCentralWidget(self.browser)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Q:
            self.app.quit()
        else:
            event.ignore()


def parse_cmdline():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--json-file', default=JSON_PATH,
                        help="JSON image file to load")
    return parser.parse_args()


def main(options):
    QImageReader.setAllocationLimit(0)
    app = QApplication([])
    window = Window(app)
    tree = library.Library(options.json_file).make_tree()
    window.browser.load_node(tree)
    window.show()
    app.exec()


if __name__ == '__main__':
    main(parse_cmdline())
