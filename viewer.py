from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, Signal, QEvent, QSize
from PySide6.QtGui import QPixmap, QPainter
from library import Node

import keys
from cache import load_pixmap


class Viewer(QLabel):
    target_selected = Signal(Node)
    unselected = Signal(Node)
    target_updated = Signal(Node)

    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.node = None
        self.target = None
        self.action_map = {
            'left': self.scroll,
            'right': self.scroll,
            'select': self.select,
            'unselect': self.unselect,
        }

    def load(self, node, target):
        self.node = node
        self.target = target
        self.base_pixmap = load_pixmap(self.target.abspath, self.size())
        self.raw_pixmap = None
        self.base_zoom = None
        self.zoom_level = 0
        sw, sh = self.size().toTuple()
        iw, ih = self.base_pixmap.size().toTuple()
        self.xoff = self.yoff = None
        self.setPixmap(self.base_pixmap)
        self.target_updated.emit(target)

    def scroll(self, action):
        images = self.node.children
        index = images.index(self.target)
        offset = {'right': 1, 'left': -1}[action]
        target = images[(index + offset) % (len(images))]
        self.load(self.node, target)
        self.target_updated.emit(target)

    def select(self, _action=None):
        self.target_selected.emit(self.target)

    def unselect(self, _action=None):
        self.unselected.emit(self.target)

    def keyPressEvent(self, event):
        action = keys.get_action(event)
        if action in self.action_map:
            self.action_map[action](action)
        else:
            event.ignore()

    def redraw_image(self):
        viewport = QPixmap(QSize(self.view_width, self.view_height))
        viewport.fill(Qt.black)
        p = QPainter(viewport)
        p.drawPixmap(-self.xoff, -self.yoff, self.raw_pixmap)
        p.end()
        self.scaled = viewport.scaled(self.size(), aspectMode=Qt.KeepAspectRatio,
                                      mode=Qt.SmoothTransformation)
        self.setPixmap(self.scaled)

    def load_raw_pixmap(self):
        self.raw_pixmap = QPixmap(self.target.abspath)
        self.base_zoom = self.base_pixmap.width() / self.raw_pixmap.width()
        zoom = self.base_zoom * (1.2 ** self.zoom_level)
        iw, ih = self.raw_pixmap.size().toTuple()
        sw, sh = self.size().toTuple()
        self.view_width = int(sw / zoom)
        self.view_height = int(sh / zoom)
        self.xoff = (iw - self.view_width) // 2
        self.yoff = (ih - self.view_height) // 2

    def zoom(self, pos, direction):
        if self.zoom_level + direction < 0:
            return

        sx, sy = pos.toTuple()
        sw, sh = self.size().toTuple()

        if self.raw_pixmap is None:
            self.load_raw_pixmap()

        old_zoom = self.base_zoom * (1.2 ** self.zoom_level)
        iw, ih = self.raw_pixmap.size().toTuple()

        # ix, iy: image pixel we clicked on. Will be centered after zoom
        ix = int(sx / old_zoom) + self.xoff
        iy = int(sy / old_zoom) + self.yoff

        self.zoom_level += direction
        new_zoom = self.base_zoom * (1.2 ** self.zoom_level)
        self.view_width = int(sw / new_zoom)
        self.view_height = int(sh / new_zoom)
        self.xoff, self.yoff = (ix - self.view_width // 2, iy - self.view_height // 2)
        self.redraw_image()

    def handle_mousewheel(self, event):
        self.zoom(event.position(), 1 if event.angleDelta().y() > 0 else -1)

    def handle_mousedown(self, event):
        if self.raw_pixmap is None:
            self.load_raw_pixmap()
        self.click_pos = event.position().toTuple()

    def handle_mousemove(self, event):
        cx, cy = self.click_pos
        x, y = event.position().toTuple()
        self.click_pos = (x, y)
        zoom = self.base_zoom * (1.2 ** self.zoom_level)
        self.xoff += (cx - x) // zoom
        self.yoff += (cy - y) // zoom
        self.redraw_image()

    def handle_mouseup(self, event):
        pass
