import copy

from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtGui import QImageReader, QPalette, QFont
from PySide6.QtCore import Qt, Signal

import library
import browser
from editor import EditorDialog
from config import default_config, ConfigDialog
from deleter import DeleterDialog
from importer import ImporterDialog
from cache import background_cacher
import keys


class Window(QMainWindow):
    def __init__(self, app, json_file, size):
        super().__init__()
        self.setFixedSize(size)
        self.app = app
        self.setFont(QFont("Liberation mono"))
        pal = self.palette()
        pal.setColor(QPalette.Window, Qt.black)
        self.setPalette(pal)
        self.library = library.Library(json_file)
        self.app.quitting.connect(self.library.save)
        self.config = default_config(self.library)
        self.browser = browser.Browser(size)
        self.setCentralWidget(self.browser)
        self.cacher = background_cacher(
            self.app, self.library.root_dir, self.library.images,
            [self.size(), self.browser.thumbnail_size],
            self.browser.set_status_text,
        )
        self.reload_tree()
        self.snapshots = []

    def reload_tree(self):
        target = self.browser.target
        tree = self.library.make_tree(self.config)

        if not target:
            self.browser.load_node(tree, mode='grid')
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
                if target.type != 'image':
                    browser_mode = 'grid'
                break
            target = targets[0]

        self.browser.load_node(node, target=target, mode=browser_mode)
        return node, target

    def save_snapshot(self):
        snapshot = (self.browser.node, self.browser.target, self.browser.mode,
                    copy.deepcopy(self.config))
        self.snapshots.append(snapshot)

    def restore_snapshot(self):
        if self.snapshots:
            node, target, mode, self.config = self.snapshots.pop()
            self.browser.load_node(node, target=target, mode=mode)

    def jump_to_subject(self):
        # TODO generalize this via a dialog
        mode = self.browser.mode
        target = self.browser.target
        image = next(target.leaves())
        subjects = image.spec['subjects']
        if not subjects:
            return
        self.save_snapshot()
        self.config.group_by = ['subjects']
        self.config.clear_filters()
        self.config.include_tags = subjects
        _node, target = self.reload_tree()
        node = [x for x in _node.root.children if x.name in subjects][0]
        self.browser.load_node(node, mode=mode)

    def keyPressEvent(self, event):
        action = keys.get_action(event)
        if action == 'quit':
            self.app.quit()
        elif action == 'edit':
            EditorDialog(self, self.browser.target).exec() # blocks until dialog closed
        elif action == 'config':
            ConfigDialog(self, self.library, self.config).exec()
        elif action == 'delete':
            DeleterDialog(self, self.browser.target).exec()
        elif action == 'save_snapshot':
            self.save_snapshot()
        elif action == 'restore_snapshot':
            self.restore_snapshot()
        elif action == 'jump_to_subject':
            self.jump_to_subject()
        elif action == 'add_new_images':
            ImporterDialog(self, self.browser.node).exec()
        else:
            event.ignore()


class Application(QApplication):
    quitting = Signal()

    def __init__(self, json_file):
        super().__init__([])
        QImageReader.setAllocationLimit(0)
        self.window = Window(self, json_file, self.primaryScreen().size())

    def exec(self):
        self.window.showFullScreen()
        super().exec()
        self.quitting.emit()
