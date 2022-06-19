import os

from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QFontMetrics
from PySide6.QtCore import Qt, Signal, QSize

import cache


class Thumbnail(QLabel):
    def __init__(self, node, size):
        super().__init__()
        self.node = node
        if self.node.children:
            image = next(self.node.leaves())
            self.image_path = image.abspath
            self.name = node.name
            self.count = len(node.children)
        else:
            self.image_path = node.abspath
            self.name = None
            self.count = None

        self.root_dir = node.library.root_dir

        self.painter = QPainter()
        self.pixmap = None
        self.setFixedSize(QSize(*size))
        self.setAlignment(Qt.AlignCenter)

    def draw_text(self, text, font_size, align, margin=5, opacity=0.6):
        font = self.painter.font()
        font.setPointSize(font_size)
        self.painter.setFont(font)
        rect = QFontMetrics(font).tightBoundingRect(text)
        rect.adjust(-margin, -margin, margin, margin)
        if align & Qt.AlignTop:
            rect.moveTop(0)
        if align & Qt.AlignBottom:
            rect.moveBottom(self.height())
        if align & Qt.AlignLeft:
            rect.moveLeft(0)
        if align & Qt.AlignRight:
            rect.moveRight(self.width())
        if align & Qt.AlignHCenter:
            rect.moveLeft(self.width() / 2 - rect.width() / 2)
        if align & Qt.AlignVCenter:
            rect.moveTop(self.height() / 2 - rect.height() / 2)
        self.painter.fillRect(rect, QColor(0, 0, 0, 255 * opacity))
        self.painter.setPen(Qt.white)
        self.painter.drawText(rect, Qt.AlignCenter, text)

    def draw_overlay(self):
        if self.name:
            self.draw_text(self.name, 14, Qt.AlignTop | Qt.AlignHCenter)
        if self.count:
            self.draw_text(str(self.count), 30, Qt.AlignBottom | Qt.AlignRight)

    def paintEvent(self, event):
        if self.pixmap is None:
            self.pixmap = cache.load_pixmap(self.root_dir, self.image_path, self.size())
            self.setPixmap(self.pixmap)
        super().paintEvent(event)
        self.painter.begin(self)
        self.draw_overlay()
        self.painter.end()
