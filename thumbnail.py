from PySide6.QtWidgets import QWidget, QLabel, QStackedLayout, QGridLayout
from PySide6.QtCore import Qt

import cache


class Image(QLabel):
    def __init__(self, root_dir, path, size):
        super().__init__()
        self.setFixedSize(size)
        self.setAlignment(Qt.AlignCenter)
        self.root_dir = root_dir
        self.path = path

    def paintEvent(self, event):
        if not self.pixmap():
            self.setPixmap(cache.load_pixmap(self.root_dir, self.path, self.size()))
        super().paintEvent(event)


class Thumbnail(QWidget):
    def __init__(self, node, size):
        super().__init__()
        self.node = node
        self.setFixedSize(size)
        self.setLayout(QStackedLayout())
        self.layout().setStackingMode(QStackedLayout.StackAll)
        if node.children:
            self.add_text(node.name, "thumbnailName", Qt.AlignTop | Qt.AlignHCenter)
            self.add_text(str(len(node.children)), "thumbnailCount", Qt.AlignBottom | Qt.AlignRight)
            image_path = next(node.leaves()).abspath
        else:
            image_path = node.abspath
        self.layout().addWidget(Image(node.library.root_dir, image_path, size))

    def add_text(self, text, font_style, align):
        widget = QLabel()
        widget.setProperty("qtiColors", "semitransparent")
        widget.setProperty("qtiFont", font_style)
        widget.setContentsMargins(5, 0, 5, 0)
        widget.setText(text)
        widget.setMaximumSize(self.size())

        container = QWidget()
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widget, 1, 1)
        container.setLayout(layout)
        if align & (Qt.AlignTop | Qt.AlignVCenter):
            layout.setRowStretch(2, 1)
        if align & (Qt.AlignBottom | Qt.AlignVCenter):
            layout.setRowStretch(0, 1)
        if align & (Qt.AlignLeft | Qt.AlignHCenter):
            layout.setColumnStretch(2, 1)
        if align & (Qt.AlignRight | Qt.AlignHCenter):
            layout.setColumnStretch(0, 1)
        self.layout().addWidget(container)
