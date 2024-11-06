import time

from .cache import ensure_cached
from . import ui

Image = ui.cls('image')


class Viewer:
    def __init__(self, app, scroll_cb, close_cb):
        self.ui = ui.cls('viewer')(mouse_cb=self.handle_mouse)
        self.scroll_cb = scroll_cb
        self.close_cb = close_cb
        self.app = app
        self.node = None
        self.target = None
        self.auto_scroll_enabled = False
        self.auto_scroll_at = None
        self.auto_scroll_timer = app.timer(self.auto_scroll_tick, repeat=True)
        self.action_map = {
            'left': self.scroll,
            'right': self.scroll,
            'top': self.scroll,
            'bottom': self.scroll,
            'select': self.close,
            'unselect': self.close,
            'reset_zoom': self.reset_zoom,
            'auto_scroll': self.toggle_auto_scroll,
        }

    def load(self, node, target):
        self.node = node
        self.target = target
        self.init_image(self.target.abspath, self.ui.size)
        self.scroll_cb(node.children.index(target))

    def init_image(self, image_path, window_size):
        self.window_size = window_size
        self.scaled_path = ensure_cached(image_path, window_size)
        self.base_image = Image(self.scaled_path)
        self.raw_image = Image(self.target.abspath)
        self.base_zoom = self.base_image.size[0] / self.raw_image.size[0]
        self.reset_zoom()

    def reset_zoom(self, _action=None):
        self.zoom_level = 0
        self.view_width = int(self.window_size[0] / self.base_zoom)
        self.view_height = int(self.window_size[1] / self.base_zoom)
        self.xoff = (self.raw_image.size[0] - self.view_width) // 2
        self.yoff = (self.raw_image.size[1] - self.view_height) // 2
        self.ui.load(self.base_image)

    def scroll(self, action):
        images = self.node.children
        index = images.index(self.target)
        offset = {'right': 1, 'left': -1, 'top': -index, 'bottom': -index - 1}[action]
        new_index = (index + offset) % (len(images))
        target = images[new_index]
        self.load(self.node, target)
        self.scroll_cb(new_index)

    def close(self, _action=None):
        self.close_cb(self.target)

    def toggle_auto_scroll(self, _action=None):
        if self.auto_scroll_enabled:
            self.stop_auto_scroll()
        else:
            self.start_auto_scroll()

    def start_auto_scroll(self):
        self.auto_scroll_enabled = True
        self.auto_scroll_at = time.time() + self.app.settings.get('auto_scroll_period')
        self.auto_scroll_timer.start(0.1)

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

    def handle_action(self, action):
        if action != 'auto_scroll':
            self.stop_auto_scroll()
        if action in self.action_map:
            self.action_map[action](action)
            return True
        return False

    def redraw_image(self):
        viewport = self.raw_image.crop_and_pan((self.view_width, self.view_height), -self.xoff,
                                               -self.yoff, self.app.settings.background_color)
        self.ui.load(viewport.scale(self.ui.size))

    def zoom_factor(self):
        return self.base_zoom * (self.app.settings.zoom_rate ** self.zoom_level)

    def load_raw_image(self):
        self.raw_image = Image(self.target.abspath)

    def handle_mouse(self, event_type, position, value):
        if event_type == 'wheel':
            self.zoom(position, value)
        elif event_type == 'click':
            self.start_panning(position)
        elif event_type == 'drag':
            self.pan(position)
        else:
            return False
        return True

    def zoom(self, pos, direction):
        if self.zoom_level + direction < 0:
            return

        sx, sy = pos
        sw, sh = self.ui.size

        if self.raw_image is None:
            self.load_raw_image()

        old_zoom = self.zoom_factor()
        iw, ih = self.raw_image.size

        # ix, iy: image pixel we clicked on. Will be centered after zoom
        ix = int(sx / old_zoom) + self.xoff
        iy = int(sy / old_zoom) + self.yoff

        self.zoom_level += direction
        new_zoom = self.zoom_factor()
        self.view_width = int(sw / new_zoom)
        self.view_height = int(sh / new_zoom)
        self.xoff, self.yoff = (ix - self.view_width // 2, iy - self.view_height // 2)
        self.redraw_image()

    def start_panning(self, pos):
        if self.raw_image is None:
            self.load_raw_image()
        self.click_pos = pos

    def pan(self, pos):
        cx, cy = self.click_pos
        self.click_pos = pos
        x, y = pos
        zoom = self.zoom_factor()
        self.xoff += (cx - x) // zoom
        self.yoff += (cy - y) // zoom
        self.redraw_image()
