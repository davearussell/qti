from PySide6.QtWidgets import QWidget, QLabel, QFrame, QHBoxLayout
from PySide6.QtCore import Qt, Signal
from library import Node


class PathbarLabel(QLabel):
    def __init__(self, text, style):
        super().__init__()
        self.setProperty("qtiFont", "pathbar")
        self.setProperty("qtiFontStyle", style)
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setText(text)


class NodeLabel(PathbarLabel):
    clicked = Signal(Node)

    def __init__(self, node, color):
        self.node = node
        text = node.name
        if node.parent:
            siblings = node.parent.children
            text += "\n[%d / %d]" % (siblings.index(node) + 1, len(siblings))
        super().__init__(text, color)
        self.setToolTip(node.name)

    def mousePressEvent(self, event):
        self.clicked.emit(self.node)


class Pathbar(QFrame):
    clicked = Signal(Node)

    fade_target = False

    def __init__(self):
        super().__init__()
        self.setProperty("qtiOverlay", "true")
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

    def clear(self):
        QWidget().setLayout(self.layout)
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

    def set_target(self, target):
        self.clear()

        if target is None:
            self.layout.addWidget(PathbarLabel('No images found', Qt.gray))
            return

        nodes = []
        node = target
        while node.parent:
            nodes.insert(0, node)
            node = node.parent

        sep_style = "sep"
        node_style = "node"
        for node in nodes:
            if self.fade_target and node is target:
                sep_style += "_fade"
                node_style += "_fade"
            if self.layout.count():
                self.layout.addWidget(PathbarLabel('>', sep_style))
            label = NodeLabel(node, node_style)
            label.clicked.connect(self.clicked)
            self.layout.addWidget(label)
        self.layout.addStretch(1)
