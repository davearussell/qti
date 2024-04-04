import time

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, Signal, QEvent, QSize, QTimer
from PySide6.QtGui import QPixmap, QPainter

from qt.keys import event_keystroke


class Viewer(QLabel):
    target_selected = Signal(object)
    unselected = Signal(object)
    target_updated = Signal(object)

    def __init__(self, app):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.app = app
        self.keybinds = app.keybinds
        self.node = None
        self.target = None
        self.auto_scroll_enabled = False
        self.auto_scroll_at = None
        self.auto_scroll_timer = QTimer()
        self.auto_scroll_timer.timeout.connect(self.auto_scroll_tick)
        self.action_map = {
            'left': self.scroll,
            'right': self.scroll,
            'top': self.scroll,
            'bottom': self.scroll,
            'select': self.select,
            'unselect': self.unselect,
            'reset_zoom': self.reset_zoom,
            'auto_scroll': self.toggle_auto_scroll,
        }

    def load(self, node, target):
        self.node = node
        self.target = target
        self.base_pixmap = self.target.load_pixmap(self.size())
        self.raw_pixmap = None
        self.base_zoom = None
        self.zoom_level = 0
        self.xoff = self.yoff = None
        if target.spec.get('zoom') is not None:
            self.load_raw_pixmap(zoom=target.spec['zoom'], pan=target.spec['pan'])
            self.redraw_image()
        else:
            self.setPixmap(self.base_pixmap)
        self.target_updated.emit(target)

    def scroll(self, action):
        images = self.node.children
        index = images.index(self.target)
        offset = {'right': 1, 'left': -1, 'top': -index, 'bottom': -index - 1}[action]
        target = images[(index + offset) % (len(images))]
        self.load(self.node, target)
        self.target_updated.emit(target)

    def select(self, _action=None):
        self.target_selected.emit(self.target)

    def unselect(self, _action=None):
        self.unselected.emit(self.target)

    def toggle_auto_scroll(self, _action=None):
        if self.auto_scroll_enabled:
            self.stop_auto_scroll()
        else:
            self.start_auto_scroll()

    def start_auto_scroll(self):
        self.auto_scroll_enabled = True
        self.auto_scroll_at = time.time() + self.app.settings.get('auto_scroll_period')
        self.auto_scroll_timer.start(100)

    def stop_auto_scroll(self):
        self.auto_scroll_enabled = False
        self.auto_scroll_timer.stop()

    def auto_scroll_tick(self):
        remaining = self.auto_scroll_at - time.time()
        if remaining < 0 :
            self.scroll('right')
            self.auto_scroll_at += self.app.settings.get('auto_scroll_period')
        else:
            self.app.status_bar.set_text('Auto scroll [%d]' % remaining, duration_s=0.11)

    def keyPressEvent(self, event):
        keystroke = event_keystroke(event)
        action = self.keybinds.get_action(keystroke)
        if action != 'auto_scroll':
            self.stop_auto_scroll()
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

    def zoom_factor(self):
        return self.base_zoom * (self.app.settings.zoom_rate ** self.zoom_level)

    def _reset_zoom(self, zoom=0, pan=None):
        self.base_zoom = self.base_pixmap.width() / self.raw_pixmap.width()
        self.zoom_level = zoom
        iw, ih = self.raw_pixmap.size().toTuple()
        sw, sh = self.size().toTuple()
        self.view_width = int(sw / self.zoom_factor())
        self.view_height = int(sh / self.zoom_factor())
        if pan:
            self.xoff, self.yoff = pan
        else:
            self.xoff = (iw - self.view_width) // 2
            self.yoff = (ih - self.view_height) // 2

    def load_raw_pixmap(self, **kwargs):
        self.raw_pixmap = QPixmap(self.target.abspath)
        self._reset_zoom(**kwargs)

    def reset_zoom(self, _action=None):
        if self.raw_pixmap is not None:
            self._reset_zoom()
            self.redraw_image()

    def zoom(self, pos, direction):
        if self.zoom_level + direction < 0:
            return

        sx, sy = pos.toTuple()
        sw, sh = self.size().toTuple()

        if self.raw_pixmap is None:
            self.load_raw_pixmap()

        old_zoom = self.zoom_factor()
        iw, ih = self.raw_pixmap.size().toTuple()

        # ix, iy: image pixel we clicked on. Will be centered after zoom
        ix = int(sx / old_zoom) + self.xoff
        iy = int(sy / old_zoom) + self.yoff

        self.zoom_level += direction
        new_zoom = self.zoom_factor()
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
        zoom = self.zoom_factor()
        self.xoff += (cx - x) // zoom
        self.yoff += (cy - y) // zoom
        self.redraw_image()

    def handle_mouseup(self, event):
        pass
