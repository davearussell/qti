from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt, QSize


class PathbarLabel(QLabel):
    def __init__(self, text, color):
        super().__init__()
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        palette = self.palette()
        palette.setColor(QPalette.WindowText, color)
        self.setPalette(palette)
        self.setText(text)


class NodeLabel(PathbarLabel):
    def __init__(self, node, color):
        self.node = node
        text = node.name
        if node.parent:
            siblings = node.parent.children
            text += "\n[%d / %d]" % (siblings.index(node) + 1, len(siblings))
        super().__init__(text, color)
        self.setToolTip(node.name)


class Pathbar(QWidget):
    background_opacity = 0.5
    fade_target = False

    def __init__(self):
        super().__init__()
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        font = self.font()
        font.setPointSize(16)
        self.setFont(font)
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(0, 0, 0, int(255 *self.background_opacity)))
        self.setPalette(palette)

    def clear(self):
        QWidget().setLayout(self.layout)
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

    def set_target(self, target):
        nodes = []
        node = target
        while node:
            nodes.insert(0, node)
            node = node.parent

        self.clear()
        sep_color = Qt.cyan
        node_color = Qt.white
        for node in nodes:
            if self.fade_target and node is target:
                sep_color = Qt.blue
                node_color = Qt.gray
            if node.parent:
                self.layout.addWidget(PathbarLabel('>', sep_color))
            self.layout.addWidget(NodeLabel(node, node_color))
        self.layout.addStretch(1)
