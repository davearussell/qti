#! /bin/python3
from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout
from PySide6.QtCore import Qt, Signal
import grid, viewer, thumbnail
from library import Node


class BrowserWindow(QWidget):
    target_selected = Signal(Node)
    unselected = Signal(Node)

    def __init__(self, widget):
        super().__init__()
        self.widget = widget
        self.setLayout(self.make_layout(self.widget))
        self.widget.target_updated.connect(self.target_cb)
        self.widget.target_selected.connect(self.select_cb)
        self.widget.unselected.connect(self.unselect_cb)
        self.node = None
        self.target = None

    def make_layout(self, widget):
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widget)
        return layout

    def load(self, node, target):
        self.node = node
        self.target = target
        self.load_widget(node, target)

    def load_widget(self, node, target):
        self.widget.load(node, target)

    def target_cb(self, target):
        self.target = target

    def select_cb(self, target):
        self.target_selected.emit(target)

    def unselect_cb(self):
        self.unselected.emit(self.target)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.widget.setFocus()


class GridWindow(BrowserWindow):
    thumbnail_size = (200, 250)

    def __init__(self):
        super().__init__(grid.Grid())

    def load_widget(self, node, target):
        thumbnails = [thumbnail.Thumbnail(child, self.thumbnail_size) for child in node.children]
        self.widget.load(thumbnails, target=thumbnails[node.children.index(target)])

    def target_cb(self, thumbnail):
        super().target_cb(thumbnail.node)

    def select_cb(self, thumbnail):
        super().select_cb(thumbnail.node)

    def unselect_cb(self):
        self.unselected.emit(self.node)


class ViewerWindow(BrowserWindow):
    def __init__(self):
        super().__init__(viewer.Viewer())


class Browser(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.grid = GridWindow()
        self.addWidget(self.grid)
        self.grid.target_selected.connect(self.grid_select)
        self.grid.unselected.connect(self.unselect)
        self.viewer = ViewerWindow()
        self.addWidget(self.viewer)
        self.viewer.target_selected.connect(self.unselect)
        self.viewer.unselected.connect(self.unselect)

    def load_node(self, node):
        self.currentWidget().load(node, node.children[0])

    def grid_select(self, node):
        if node.children:
            self.grid.load(node, node.children[0])
        else:
            self.setCurrentWidget(self.viewer)
            self.viewer.load(node.parent, node)

    def unselect(self, node):
        if node.parent:
            self.setCurrentWidget(self.grid)
            self.grid.load(node.parent, node)

    def scroll_node(self, offset):
        window = self.currentWidget()
        node = window.node
        if not node.parent:
            return
        siblings = node.parent.children
        new_node = siblings[(siblings.index(node) + offset) % len(siblings)]
        window.load(new_node, new_node.children[0])

    def keyPressEvent(self, event):
        key = event.key()
        if key in [Qt.Key_Up, Qt.Key_Down, Qt.Key_PageUp, Qt.Key_PageDown]:
            self.scroll_node(1 if key in [Qt.Key_Down, Qt.Key_PageDown] else -1)
        else:
            event.ignore()
