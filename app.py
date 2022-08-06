#! /bin/python3
import argparse
from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtGui import QPalette, QImageReader, QFont
from PySide6.QtCore import Qt

import library
import browser
from editor import EditorDialog
from config import default_config, ConfigDialog

JSON_PATH = "/home/dar/files/downloads/test/pictures/flat.json"


class Window(QMainWindow):
    size = (1600, 1000)

    def __init__(self, app, json_file):
        super().__init__()
        self.app = app
        self.setGeometry(200, 0, *self.size)
        self.setFixedSize(*self.size)
        self.setFont(QFont("Liberation mono"))
        pal = self.palette()
        pal.setColor(QPalette.Window, Qt.black)
        self.setPalette(pal)
        self.library = library.Library(json_file)
        self.config = default_config(self.library)
        self.browser = browser.Browser()
        self.setCentralWidget(self.browser)
        self.reload_tree()

    def reload_tree(self):
        target = self.browser.target()
        tree = self.library.make_tree(self.config)

        if not target:
            self.browser.load_node(tree)
            return tree.children[0]

        path_from_root = []
        node = target
        while node.parent:
            path_elem = (node.type, node.name, node.parent.children.index(node))
            path_from_root.insert(0, path_elem)
            node = node.parent

        browser_mode = None
        node = None
        target = tree
        for node_type, name, idx in path_from_root:
            node = target
            targets = [child for child in node.children if child.name == name]
            if not targets:
                if idx >= len(node.children):
                    idx = len(node.children) - 1
                target = node.children[idx]
                browser_mode = 'grid'
                break
            target = targets[0]

        self.browser.load_node(node, target=target, mode=browser_mode)
        return target

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Q:
            self.app.quit()
        elif key == Qt.Key_E:
            EditorDialog(self, self.browser.target()).exec() # blocks until dialog closed
        elif key == Qt.Key_V:
            ConfigDialog(self, self.library, self.config).exec()
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
    window = Window(app, options.json_file)
    window.show()
    app.exec()


if __name__ == '__main__':
    main(parse_cmdline())
