#! /bin/python3
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedLayout
from PySide6.QtCore import Qt, Signal, QSize
from grid import Grid
from viewer import Viewer
from thumbnail import Thumbnail
from pathbar import Pathbar
from status_bar import StatusBar
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
        self.grid = None
        self.node = None
        self.target = None
        self.pathbar = None
        self.status_bar = None
        self.status_text = ''
        self.hide_bars = False

    def set_status_text(self, text):
        self.status_text = text
        self.status_bar.set_text(text)

    def make_grid(self, node, target):
        self.pathbar = Pathbar()
        self.pathbar.clicked.connect(self.unselect)
        self.pathbar.fade_target = True

        self.grid = NodeGrid(self.thumbnail_size)
        self.grid.target_updated.connect(self._target_updated)
        self.grid.target_selected.connect(self.select)
        self.grid.unselected.connect(self.unselect)
        self.grid.load(node, target=target)
        self.status_bar = StatusBar(self.status_text)

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.pathbar)
        layout.addWidget(self.grid)
        layout.addWidget(self.status_bar)
        self.grid.setFocus()

    def wrap_widget(self, widget, align='top'):
        wrapper = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        wrapper.setLayout(layout)
        if align == 'bottom':
            layout.addStretch(1)
        layout.addWidget(widget)
        if align == 'top':
            layout.addStretch(1)
        return wrapper

    def make_viewer(self, node, target):
        self.pathbar = Pathbar()
        self.pathbar.clicked.connect(self.unselect)
        self.status_bar = StatusBar(self.status_text)
        pathbar_wrapper = self.wrap_widget(self.pathbar, 'top')
        status_bar_wrapper = self.wrap_widget(self.status_bar, 'bottom')

        viewer = Viewer(self.size())
        viewer.target_updated.connect(self._target_updated)
        viewer.target_selected.connect(self.unselect)
        viewer.unselected.connect(self.unselect)
        viewer.load(node, target)

        layout = QStackedLayout()
        self.setLayout(layout)
        layout.setStackingMode(QStackedLayout.StackAll)
        layout.addWidget(pathbar_wrapper)
        layout.addWidget(status_bar_wrapper)
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
        self.set_bar_visibility(self.hide_bars)

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

    def swap_cells(self, direction):
        cells = self.node.children
        i1 = cells.index(self.target)
        if self.mode == 'grid':
            i2 = cells.index(self.grid.neighbour(self.target, direction))
        else:
            if direction in ['up', 'down']:
                return # It only makes sense to swap horizontally when in viewer mode
            i2 = (i1 + (1 if direction == 'right' else -1)) % len(cells)
        cells[i1], cells[i2] = cells[i2], cells[i1]
        self.node.root.dirty = True
        self.load_node(self.node, self.target)

    def set_bar_visibility(self, hidden):
        self.hide_bars = hidden
        for bar in [self.pathbar, self.status_bar]:
            if hidden:
                bar.hide()
            else:
                bar.show()

    def keyPressEvent(self, event):
        action = keys.get_action(event)
        if action in ['prev', 'next', 'up', 'down']:
            # NOTE: up/down here is only reachable in viewer mode; in grid
            # mode the grid class consumes them to scroll with in the grid
            self.scroll_node(1 if action in ['next', 'down'] else -1)
        elif action in ['swap_up', 'swap_down', 'swap_left', 'swap_right']:
            self.swap_cells(action[len('swap_'):])
        elif action == 'toggle_hide':
            self.set_bar_visibility(not self.hide_bars)
        else:
            event.ignore()
