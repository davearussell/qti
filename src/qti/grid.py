from xui.widgets import Image, Grid

from .cache import ensure_cached


class Thumbnail(Image):
    def __init__(self, browser, node):
        self.browser = browser
        self.node = node
        if node.children:
            self._path = next(node.images()).abspath
        else:
            self._path = node.abspath
        super().__init__(None, browser.app.settings.thumbnail_size)

    def draw(self):
        self.path = ensure_cached(self._path, self.size)
        super().draw()
