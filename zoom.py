from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton, QComboBox
from PySide6.QtCore import Qt, Signal
from fields import Field


class ZoomBody(QWidget):
    updated = Signal(tuple)

    def __init__(self, viewer, zoom, pan):
        super().__init__()
        self.viewer = viewer
        self.zoom = zoom
        self.pan = pan

        self.scope_box = QComboBox()
        node = viewer.target
        while node:
            self.scope_box.addItem(node.type.title())
            node = node.parent
        self.scope_box.currentIndexChanged.connect(self.scope_updated)
        self.scope_box.setFocusPolicy(Qt.ClickFocus)

        self.set_button = QPushButton("Use current zoom")
        self.set_button.clicked.connect(self.set_from_viewer)

        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear)

        self.label = QLabel("")

        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self.scope_box)
        self.layout().addWidget(self.set_button)
        self.layout().addWidget(self.clear_button)
        self.layout().addWidget(self.label)
        self.refresh()

    @property
    def scope(self):
        return self.scope_box.currentText().lower()

    def clear(self):
        self.zoom = self.pan = None
        self.updated.emit((self.scope, self.zoom, self.pan))
        self.refresh()

    def scope_updated(self):
        print("scope updated")
        self.updated.emit((self.scope, self.zoom, self.pan))
        self.refresh()

    def set_from_viewer(self):
        self.zoom = self.viewer.zoom_level
        self.pan = (self.viewer.xoff, self.viewer.yoff)
        self.updated.emit((self.scope, self.zoom, self.pan))
        self.refresh()

    def refresh(self):
        self.set_button.setEnabled(bool(self.viewer.raw_pixmap))
        if self.zoom or self.pan:
            text = "zoom: %+d  pan: %r" % (self.zoom, self.pan)
            self.clear_button.setEnabled(True)
        else:
            text = "(default)"
            self.clear_button.setEnabled(False)
        self.label.setText(text)


class ZoomField(Field):
    def __init__(self, viewer, node):
        self.viewer = viewer
        self.scope = node.type
        self.node = node
        self.zoom = node.spec.get('zoom')
        self.pan = node.spec.get('pan')
        super().__init__("Zoom & Pan", (self.scope, self.zoom, self.pan))
        self.setFocusPolicy(Qt.NoFocus)

    def make_body(self):
        self.body = ZoomBody(self.viewer, self.zoom, self.pan)
        self.body.updated.connect(self.body_updated)
        container = QWidget()
        layout = QHBoxLayout()
        container.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.body)
        layout.addStretch(1)
        return container

    def body_updated(self, value):
        self.set_value(value)
        self.updated.emit()

    def set_value(self, value):
        self.scope, self.zoom, self.pan = value

    def get_value(self):
        return (self.scope, self.zoom, self.pan)

    def update_node(self, new_value):
        scope, zoom, pan = new_value
        node = self.node
        while node.type != scope:
            node = node.parent
        for child in node.leaves():
            if pan:
                child.spec['zoom'] = zoom
                child.spec['pan'] = pan
            else:
                child.spec.pop('zoom', None)
                child.spec.pop('pan', None)
