#! /bin/python3
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedLayout
from PySide6.QtGui import QPainter, QFont, QPixmap, QColor
from PySide6.QtCore import Qt
from grid import Grid, Cell
from viewer import Viewer
from pathbar import Pathbar
from tree import TreeError

from qt.keys import event_keystroke
from qt.grid import ScaledRenderer



class NodeRenderer(ScaledRenderer):
    def __init__(self, settings, image, label, count):
        super().__init__(image.abspath, settings.thumbnail_size, settings.background_color)
        self.settings = settings
        self.label = label
        self.count = count

    def render(self):
        pixmap = super().render()
        p = QPainter(pixmap)
        p.setPen(self.settings.get('text_color'))

        if self.label:
            p.setFont(QFont(self.settings.font, self.settings.thumbnail_name_font_size))
            r = p.fontMetrics().tightBoundingRect(self.label)
            r.adjust(0, 0, 10, 10)
            r.moveTop(0)
            r.moveLeft(pixmap.width() / 2 - r.width() / 2)
            p.fillRect(r, QColor(0, 0, 0, 128))
            p.drawText(r, Qt.AlignCenter, self.label)

        if self.count:
            p.setFont(QFont(self.settings.font, self.settings.thumbnail_count_font_size))
            r = p.fontMetrics().tightBoundingRect(str(self.count))
            # If we render using the rect returned by tightBoundingRect, it cuts off the
            # top of the text and leaves empty space at the bottom. Account for this by
            # increasing rect size and moving its bottom outside the bounds of the pixmap
            r.adjust(0, 0, 10, 12)
            r.moveBottom(self.height + 7)
            r.moveRight(self.width)
            p.fillRect(r, QColor(0, 0, 0, 128))
            p.drawText(r, Qt.AlignCenter, str(self.count))

        return pixmap


class NodeCell(Cell):
    def __init__(self, node, settings):
        self.node = node
        count = len(node.children)
        image = next(node.images()) if count else node
        label = node.name if count else None
        renderer = NodeRenderer(settings, image, label, count)
        super().__init__(renderer, label)


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
        self.status_bar = app.status_bar.ui
        self.hide_bars = False
        self.setup_layout()

    def make_grid(self):
        grid = Grid(scroll_cb=self._target_updated, select_cb=self.select, unselect_cb=self.unselect)
        return grid

    def setup_layout(self):
        self.pathbar = Pathbar(click_cb=self.unselect)
        self.grid = self.make_grid()
        self.viewer = Viewer(self.app, scroll_cb=self._target_updated, close_cb=self.unselect)

        top_container = QWidget()
        top_layout = QVBoxLayout()
        top_layout.setSpacing(0)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_container.setLayout(top_layout)
        top_layout.addWidget(self.pathbar.ui)
        top_layout.addWidget(self.grid.ui)

        # When the grid is visible it should take up all available space;
        # when it is hidden the addStretch(0) prevents the other widgets
        # from expanding to filli the gap
        top_layout.setStretchFactor(self.grid.ui, 1)
        top_layout.addStretch(0)
        top_layout.addWidget(self.status_bar)

        base_layout = QStackedLayout()
        base_layout.setStackingMode(QStackedLayout.StackAll)
        self.setLayout(base_layout)
        base_layout.addWidget(top_container)
        base_layout.addWidget(self.viewer.ui)
        self.setLayout(base_layout)

    def _target_updated(self, target):
        if isinstance(target, NodeCell):
            target = target.node
        self.pathbar.set_target(target)
        self.target = target

    def set_mode(self, mode):
        if mode is None:
            mode = self.mode or 'grid'
        if mode != self.mode:
            active = self.grid.ui if mode == 'grid' else self.viewer.ui
            inactive = self.viewer.ui if mode == 'grid' else self.grid.ui
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
            thumbs = [NodeCell(child, self.app.settings) for child in self.node.children]
            tthumb = thumbs[self.node.children.index(self.target)] if self.target else None
            self.grid.load(thumbs, target=tthumb)
        else:
            self.pathbar.fade_target = False
            self.viewer.load(self.node, self.target)

    def reload_node(self):
        if self.node:
            self.load_node(self.node, self.target, self.mode)

    def select(self, widget):
        assert isinstance(widget, NodeCell), widget
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
        if direction in ['left', 'right']:
            i = (self.target.index + (1 if direction == 'right' else -1)) % len(cells)
            other = cells[i]
        elif self.mode == 'grid':
            other = self.grid.neighbour(self.grid.target, direction).node
        else:
            return # Cannot swap verticaly when in viewer mode

        try:
            self.target.swap_with(other)
            self.load_node(self.node, self.target)
        except TreeError as e:
            self.app.status_bar.set_text("Cannot swap (%s)" % e, duration_s=5)

    def marked_nodes(self):
        if self.mode == 'grid':
            return [cell.node for cell in self.grid.marked_cells()]
        return [self.target]

    def set_bar_visibility(self, hidden):
        self.hide_bars = hidden
        for bar in [self.pathbar.ui, self.status_bar]:
            if hidden:
                bar.hide()
            else:
                bar.show()

    def keyPressEvent(self, event):
        keystroke = event_keystroke(event)
        action = self.keybinds.get_action(keystroke)
        widget = self.viewer if self.mode == 'viewer' else self.grid
        if widget.handle_action(action):
            pass
        elif action in ['prev', 'next', 'up', 'down']:
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
            pos = event.position().toTuple()
            direction = 1 if event.angleDelta().y() > 0 else -1
            self.viewer.zoom(pos, direction)
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        if self.mode == 'viewer':
            self.viewer.start_panning(event.position().toTuple())
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # NOTE: QT will only call this while a mouse button is pressed
        if self.mode == 'viewer':
            self.viewer.pan(event.position().toTuple())
        else:
            super().mouseMoveEvent(event)
