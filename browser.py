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
        self.mode = None
        self.grid = None
        self.node = None
        self.target = None
        self.pathbar = None
        self.status_bar = None
        self.status_text = ''
        self.hide_bars = False
        self.setup_layout()

    def set_status_text(self, text):
        self.status_text = text
        self.status_bar.set_text(text)

    def make_pathbar(self):
        pathbar = Pathbar()
        pathbar.clicked.connect(self.unselect)
        return pathbar

    def make_status_bar(self):
        return StatusBar()

    def make_grid(self):
        grid = NodeGrid(self.thumbnail_size)
        grid.target_updated.connect(self._target_updated)
        grid.target_selected.connect(self.select)
        grid.unselected.connect(self.unselect)
        return grid

    def make_viewer(self):
        viewer = Viewer(self.size())
        viewer.target_updated.connect(self._target_updated)
        viewer.target_selected.connect(self.unselect)
        viewer.unselected.connect(self.unselect)
        return viewer

    def setup_layout(self):
        self.pathbar = self.make_pathbar()
        self.grid = self.make_grid()
        self.status_bar = self.make_status_bar()
        self.viewer = self.make_viewer()

        top_container = QWidget()
        top_layout = QVBoxLayout()
        top_layout.setSpacing(0)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_container.setLayout(top_layout)
        top_layout.addWidget(self.pathbar)
        top_layout.addWidget(self.grid)

        # When the grid is visible it should take up all available space;
        # when it is hidden the addStretch(0) prevents the other widgets
        # from expanding to filli the gap
        top_layout.setStretchFactor(self.grid, 1)
        top_layout.addStretch(0)
        top_layout.addWidget(self.status_bar)

        base_layout = QStackedLayout()
        base_layout.setStackingMode(QStackedLayout.StackAll)
        self.setLayout(base_layout)
        base_layout.addWidget(top_container)
        base_layout.addWidget(self.viewer)
        self.setLayout(base_layout)

    def _target_updated(self, target):
        self.pathbar.set_target(target)
        self.target = target

    def set_mode(self, mode):
        if mode is None:
            mode = self.mode or 'grid'
        if mode != self.mode:
            active = self.grid if mode == 'grid' else self.viewer
            inactive = self.viewer if mode == 'grid' else self.grid
            inactive.hide()
            active.show()
            active.setFocus()
            self.mode = mode

    def load_node(self, node, target=None, mode=None):
        self.node = node
        self.target = target or node.children[0]
        self.set_mode(mode)
        widget = self.grid if self.mode == 'grid' else self.viewer
        widget.load(self.node, self.target)

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
