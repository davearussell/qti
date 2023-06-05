#! /bin/python3
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedLayout
from PySide6.QtGui import QPainter, QFont, QPixmap, QColor
from PySide6.QtCore import Qt
from grid import Grid, Cell
from viewer import Viewer
from pathbar import Pathbar
import cache


class Thumbnail(Cell):
    def __init__(self, settings, node):
        super().__init__(settings.thumbnail_size)
        self.settings = settings
        self.node = node
        if node.children:
            self.image = next(node.leaves())
            self.count = str(len(node.children))
            self.name = node.name
        else:
            self.image = node
            self.count = None
            self.name = None

    def load_pixmap(self):
        pixmap = super().load_pixmap()
        image = cache.load_pixmap(self.image.root_dir, self.image.relpath, self.size)
        iw, ih = image.size().toTuple()
        p = QPainter(pixmap)
        p.setPen(self.settings.get('text_color'))
        p.fillRect(0, 0, self.width, self.height, self.settings.get('background_color'))
        p.drawPixmap((self.width - iw) // 2, (self.height - ih) // 2, image)

        if self.name:
            p.setFont(QFont(self.settings.font, self.settings.thumbnail_name_font_size))
            r = p.fontMetrics().tightBoundingRect(self.name)
            r.adjust(0, 0, 10, 10)
            r.moveTop(0)
            r.moveLeft(pixmap.width() / 2 - r.width() / 2)
            p.fillRect(r, QColor(0, 0, 0, 128))
            p.drawText(r, Qt.AlignCenter, self.name)

        if self.count:
            p.setFont(QFont(self.settings.font, self.settings.thumbnail_count_font_size))
            r = p.fontMetrics().tightBoundingRect(self.count)
            # If we render using the rect returned by tightBoundingRect, it cuts off the
            # top of the text and leaves empty space at the bottom. Account for this by
            # increasing rect size and moving its bottom outside the bounds of the pixmap
            r.adjust(0, 0, 10, 12)
            r.moveBottom(self.height + 7)
            r.moveRight(self.width)
            p.fillRect(r, QColor(0, 0, 0, 128))
            p.drawText(r, Qt.AlignCenter, self.count)

        return pixmap


class Browser(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.library = self.app.library
        self.keybinds = app.keybinds
        self.mode = None
        self.grid = None
        self.node = None
        self.target = None
        self.pathbar = None
        self.status_bar = None
        self.hide_bars = False
        self.setup_layout()

    def make_pathbar(self):
        pathbar = Pathbar()
        pathbar.clicked.connect(self.unselect)
        return pathbar

    def make_status_bar(self):
        return self.app.status_bar.make_widget()

    def make_grid(self):
        grid = Grid(self.app.settings, self.keybinds)
        grid.target_updated.connect(self._target_updated)
        grid.target_selected.connect(self.select)
        grid.unselected.connect(self.unselect)
        return grid

    def make_viewer(self):
        viewer = Viewer(self.app)
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
        if isinstance(target, Thumbnail):
            target = target.node
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
        self.target = target or (node.children[0] if node.children else None)
        self.set_mode(mode)
        if self.mode == 'grid':
            self.pathbar.fade_target = True
            thumbs = [Thumbnail(self.app.settings, child) for child in self.node.children]
            tthumb = thumbs[self.node.children.index(self.target)] if self.target else None
            self.grid.load(thumbs, target=tthumb)
        else:
            self.pathbar.fade_target = False
            self.viewer.load(self.node, self.target)

    def select(self, widget):
        assert isinstance(widget, Thumbnail), widget
        target = widget.node
        if target.children:
            self.load_node(target, mode='grid')
        else:
            self.load_node(target.parent, target=target, mode='viewer')

    def unselect(self, node=None):
        if node is None:
            node = self.node
        if node.parent:
            self.load_node(node.parent, target=node, mode='grid')

    def scroll_node(self, action):
        if not self.node.parent:
            return
        siblings = self.node.parent.children
        offset = {'up': -1, 'prev': -1, 'down': 1, 'next': 1}[action]
        new_node = siblings[(siblings.index(self.node) + offset) % len(siblings)]
        self.load_node(new_node)

    def scroll(self, action):
        widget = self.grid if self.mode == 'grid' else self.viewer
        if action in widget.action_map:
            widget.action_map[action](action)
        else:
            self.scroll_node(action)

    def swap_cells(self, direction):
        cells = self.node.children
        i1 = cells.index(self.target)
        if direction in ['left', 'right']:
            i2 = (i1 + (1 if direction == 'right' else -1)) % len(cells)
        elif self.mode == 'grid':
            i2 = cells.index(self.grid.neighbour(self.grid.target, direction).node)
        else:
            return # Cannot swap verticaly when in viewer mode
        cells[i1], cells[i2] = cells[i2], cells[i1]
        self.load_node(self.node, self.target)

    def set_bar_visibility(self, hidden):
        self.hide_bars = hidden
        for bar in [self.pathbar, self.status_bar]:
            if hidden:
                bar.hide()
            else:
                bar.show()

    def keyPressEvent(self, event):
        action = self.keybinds.get_action(event)
        if action in ['prev', 'next', 'up', 'down']:
            # NOTE: up/down here is only reachable in viewer mode; in grid
            # mode the grid class consumes them to scroll with in the grid
            self.scroll_node(action)
        elif action in ['swap_up', 'swap_down', 'swap_left', 'swap_right']:
            self.swap_cells(action[len('swap_'):])
        elif action == 'toggle_hide':
            self.set_bar_visibility(not self.hide_bars)
        else:
            event.ignore()

    def wheelEvent(self, event):
        # Our stacked layout means the viewer never can never get mouse events
        # directly so we catch them here and pass them on
        if self.mode == 'viewer':
            self.viewer.handle_mousewheel(event)
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        if self.mode == 'viewer':
            self.viewer.handle_mousedown(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.mode == 'viewer':
            self.viewer.handle_mousemove(event)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.mode == 'viewer':
            self.viewer.handle_mouseup(event)
        else:
            super().mouseReleaseEvent(event)
