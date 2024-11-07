from PySide6.QtWidgets import QLabel, QFrame, QHBoxLayout


class StatusBarWidget(QFrame):
    def __init__(self, app, text=''):
        super().__init__()
        self.setProperty("qtiOverlay", "true")

        self.setLayout(QHBoxLayout())
        self.label = QLabel()
        self.label.setProperty("qtiFont", "statusbar")
        self.set_text(text)
        self.layout().addWidget(self.label)

    def set_text(self, text):
        self.label.setText(text)
