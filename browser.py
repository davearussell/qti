#! /bin/python3
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedLayout
from PySide6.QtCore import Qt, Signal, QSize
from grid import Grid
from viewer import Viewer
from thumbnail import Thumbnail
from pathbar import Pathbar
import keys


class NodeGrid(Grid):
    def __init__(self, thumbnail_size):
        super().__init__()
        self.thumbnail_size = thumbnail_size

    def _cell_to_userobj(self, cell):
        return cell.widget.node

    def load(self, node, target=None):
        thumbnails = [Thumbnail(child, self.thumbnail_size) for child in node.children]
        target_thumbnail = thumbnails[node.children.index(target)] if target else None
        super().load(thumbnails, target=target_thumbnail)


class Browser(QWidget):
    thumbnail_size = QSize(200, 250)

    def __init__(self, size):
        super().__init__()
        self.setFixedSize(size)
        self.mode = 'grid'
        self.node = None
        self.target = None
        self.pathbar = None

    def make_grid(self, node, target):
        self.pathbar = Pathbar()
        self.pathbar.clicked.connect(self.unselect)
        self.pathbar.fade_target = True

        grid = NodeGrid(self.thumbnail_size)
        grid.target_updated.connect(self._target_updated)
        grid.target_selected.connect(self.select)
        grid.unselected.connect(self.unselect)
        grid.load(node, target=target)

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.pathbar)
        layout.addWidget(grid)
        grid.setFocus()

    def make_viewer(self, node, target):
        self.pathbar = Pathbar()
        self.pathbar.clicked.connect(self.unselect)

        pathbar_wrapper = QWidget()
        wr_layout = QVBoxLayout()
        wr_layout.setSpacing(0)
        wr_layout.setContentsMargins(0, 0, 0, 0)
        pathbar_wrapper.setLayout(wr_layout)
        wr_layout.addWidget(self.pathbar)
        wr_layout.addStretch(1)

        viewer = Viewer(self.size())
        viewer.target_updated.connect(self._target_updated)
        viewer.target_selected.connect(self.unselect)
        viewer.unselected.connect(self.unselect)
        viewer.load(node, target)

        layout = QStackedLayout()
        self.setLayout(layout)
        layout.setStackingMode(QStackedLayout.StackAll)
        layout.addWidget(pathbar_wrapper)
        layout.addWidget(viewer)
        viewer.setFocus()

    def _target_updated(self, target):
        self.pathbar.set_target(target)
        self.target = target

    def load_node(self, node, target=None, mode=None):
        if self.layout():
            QWidget().setLayout(self.layout()) # purge existing window contents
        self.node = node
        self.target = target or node.children[0]
        if mode is not None:
            self.mode = mode
        if self.mode == 'grid':
            self.make_grid(self.node, self.target)
        elif self.mode == 'viewer':
            self.make_viewer(self.node, self.target)
        else:
            assert 0, self.mode

    def select(self, target):
        if target.children:
            self.load_node(target, mode='grid')
        else:
            self.load_node(target.parent, target=target, mode='viewer')

    def unselect(self, node=None):
        if node is None:
            node = self.node
        if node.parent:
            self.load_node(node.parent, target=node, mode='grid')

    def scroll_node(self, offset):
        if not self.node.parent:
            return
        siblings = self.node.parent.children
        new_node = siblings[(siblings.index(self.node) + offset) % len(siblings)]
        self.load_node(new_node)

    def toggle_pathbar(self):
        if self.pathbar.isHidden():
            self.pathbar.show()
        else:
            self.pathbar.hide()

    def keyPressEvent(self, event):
        action = keys.get_action(event)
        if action in ['prev', 'next', 'up', 'down']:
            # NOTE: up/down here is only reachable in viewer mode; in grid
            # mode the grid class consumes them to scroll with in the grid
            self.scroll_node(1 if action in ['next', 'down'] else -1)
        elif action == 'toggle_hide':
            self.toggle_pathbar()
        else:
            event.ignore()
