#! /bin/python3
from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QStackedLayout
from PySide6.QtCore import Qt, Signal
import grid, viewer, thumbnail, pathbar
from library import Node


class BrowserWindow(QWidget):
    target_selected = Signal(Node)
    unselected = Signal(Node)

    def __init__(self, widget):
        super().__init__()
        self.pathbar = pathbar.Pathbar()
        self.widget = widget
        self.setLayout(self.make_layout(self.pathbar, self.widget))
        self.widget.target_updated.connect(self.target_cb)
        self.widget.target_selected.connect(self.select_cb)
        self.widget.unselected.connect(self.unselect_cb)
        self.node = None
        self.target = None

    def make_layout(self, pathbar, widget):
        """Put pathbar at the top of the window with widget below it."""
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(pathbar)
        layout.addWidget(widget)
        return layout

    def load(self, node, target):
        self.node = node
        self.target = target
        self.load_widget(node, target)
        self.pathbar.set_target(target)

    def load_widget(self, node, target):
        self.widget.load(node, target)

    def target_cb(self, target):
        self.target = target
        self.pathbar.set_target(target)

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
        self.pathbar.fade_target = True

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

    def pathbar_container(self, widget):
        """Since the pathbar's background is partially opaque, we want it to
        be minimally tall so as to avoid obscuring the entire window."""
        container = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        container.setLayout(layout)
        layout.addWidget(widget)
        layout.addStretch(1)
        return container

    def make_layout(self, pathbar, widget):
        """Allow widget to fill the window; overlay pathbar on top of it."""
        layout = QStackedLayout()
        layout.setStackingMode(QStackedLayout.StackAll)
        layout.addWidget(widget)
        layout.addWidget(self.pathbar_container(pathbar))
        return layout


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
