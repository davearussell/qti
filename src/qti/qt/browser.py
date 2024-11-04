from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedLayout
from PySide6.QtGui import QPainter, QFont, QColor
from PySide6.QtCore import Qt

from ..cache import load_scaled

from .image import center_image
from .keys import event_keystroke


def make_grid_cell(image_path, size, settings, label=None, count=None):
    image = load_scaled(image_path, size)
    pixmap = center_image(image, size, background_color=settings.background_color)

    p = QPainter(pixmap)
    p.setPen(settings.text_color)

    if label:
        p.setFont(QFont(settings.font, settings.thumbnail_name_font_size))
        r = p.fontMetrics().tightBoundingRect(label)
        r.adjust(0, 0, 10, 10)
        r.moveTop(0)
        r.moveLeft(pixmap.width() / 2 - r.width() / 2)
        p.fillRect(r, QColor(0, 0, 0, 128))
        p.drawText(r, Qt.AlignCenter, label)

    if count:
        p.setFont(QFont(settings.font, settings.thumbnail_count_font_size))
        r = p.fontMetrics().tightBoundingRect(str(count))
        # If we render using the rect returned by tightBoundingRect, it cuts off the
        # top of the text and leaves empty space at the bottom. Account for this by
        # increasing rect size and moving its bottom outside the bounds of the pixmap
        r.adjust(0, 0, 10, 12)
        r.moveBottom(pixmap.height() + 7)
        r.moveRight(pixmap.width())
        p.fillRect(r, QColor(0, 0, 0, 128))
        p.drawText(r, Qt.AlignCenter, str(count))

    return pixmap


class BrowserWidget(QWidget):
    def __init__(self, grid, viewer, status_bar, pathbar, keydown_cb):
        super().__init__()
        self.pathbar = pathbar
        self.status_bar = status_bar
        self.grid = grid
        self.viewer = viewer
        self.active = None
        self.keydown_cb = keydown_cb
        self.setup_layout()

    def setup_layout(self):
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

    def set_mode(self, mode):
        active = self.grid if mode == 'grid' else self.viewer
        inactive = self.viewer if mode == 'grid' else self.grid
        inactive.hide()
        active.show()
        active.setFocus()
        self.active = active

    def set_bar_visibility(self, hidden):
        for bar in [self.pathbar, self.status_bar]:
            if hidden:
                bar.hide()
            else:
                bar.show()

    def keyPressEvent(self, event):
        if not self.keydown_cb(event_keystroke(event)):
            super().keyPressEvent(event)

    # Our layout prevents the viewer from receiving mouse events directly,
    # so we must pass them on here when in viewer mode
    def wheelEvent(self, event):
        if self.active == self.viewer:
            self.viewer.wheelEvent(event)
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        if self.active == self.viewer:
            self.viewer.mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.active == self.viewer:
            self.viewer.mouseMoveEvent(event)
        else:
            super().mouseMoveEvent(event)
