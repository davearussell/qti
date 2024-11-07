from PySide6.QtWidgets import QWidget, QLabel, QFrame, QHBoxLayout
from PySide6.QtCore import Qt, Signal


class PathbarLabel(QLabel):
    def __init__(self, text, style):
        super().__init__()
        self.setProperty("qtiFont", "pathbar")
        self.setProperty("qtiFontStyle", style)
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setText(text)


class EntryLabel(PathbarLabel):
    clicked = Signal(object)

    def __init__(self, entry, color):
        self.entry = entry
        text = "%s\n[%d / %d]" % (entry.name, entry.index + 1, entry.total)
        super().__init__(text, color)
        self.setToolTip(entry.name)

    def mousePressEvent(self, event):
        self.clicked.emit(self.entry)


class PathbarWidget(QFrame):
    fade_target = False

    def __init__(self, app, click_cb):
        super().__init__()
        self.setProperty("qtiOverlay", "true")
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.click_cb = click_cb

    def clear(self):
        QWidget().setLayout(self.layout)
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

    def set_entries(self, entries):
        self.clear()

        if not entries:
            self.layout.addWidget(PathbarLabel('No images found', 'node'))
            return

        sep_style = "sep"
        entry_style = "node"
        for entry in entries:
            if entry.fade:
                sep_style += "_fade"
                entry_style += "_fade"
            if self.layout.count():
                self.layout.addWidget(PathbarLabel('>', sep_style))
            label = EntryLabel(entry, entry_style)
            label.clicked.connect(self.click_cb)
            self.layout.addWidget(label)
        self.layout.addStretch(1)
