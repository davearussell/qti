from PySide6.QtWidgets import QComboBox, QTextEdit, QPushButton, QWidget, QHBoxLayout, QLabel
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QColor
from qt.dialogs.common import DataDialogWidget


class Highlighter(QSyntaxHighlighter):
    color_map = {
        'comment': 'dark red',
        'error': 'red',
        'command': 'blue',
        'variable': 'green',
    }

    def __init__(self, document, settings, highlight_cb):
        self.settings = settings
        self.highlight_cb = highlight_cb
        self.fmt = QTextCharFormat()
        self.fmt.setFont(self.settings.font)
        self.fmt.setFontPointSize(self.settings.macro_font_size)
        super().__init__(document)

    def highlightBlock(self, text):
        for start, count, word_type in self.highlight_cb(text):
            self.fmt.setForeground(QColor(self.color_map.get(word_type, 'black')))
            self.setFormat(start, count, self.fmt)


class MacroDialogWidget(DataDialogWidget):
    def __init__(self, names, settings, highlight_cb, select_name_cb,
                 update_cb, new_cb, delete_cb, **kwargs):
        super().__init__(**kwargs)
        self.setFixedSize(self.parent().size() / 3)

        self.new_box = QPushButton("New")
        self.new_box.clicked.connect(new_cb)

        self.delete_box = QPushButton("Delete")
        self.delete_box.clicked.connect(delete_cb)

        self.names = QComboBox()
        for name in names:
            self.names.addItem(name)
        self.names.currentTextChanged.connect(select_name_cb)

        self.text_area = QTextEdit()
        self.text_area.setLineWrapMode(QTextEdit.NoWrap)
        self.text_area.textChanged.connect(update_cb)
        self.highlighter = Highlighter(self.text_area.document(), settings, highlight_cb)
        if not names:
            self.set_editable(False)

        header = QWidget()
        header.setLayout(QHBoxLayout())
        header.layout().addWidget(QLabel("Edit macro:"))
        header.layout().addWidget(self.names)
        header.layout().addStretch(1)
        header.layout().addWidget(self.new_box)
        header.layout().addWidget(self.delete_box)
        self.layout().addWidget(header)
        self.layout().addWidget(self.text_area)
        self.add_action_buttons()

    def set_editable(self, value):
        self.delete_box.setEnabled(value)
        self.text_area.setReadOnly(not value)

    def add_name(self, name):
        self.names.addItem(name)
        self.set_editable(True)

    def remove_name(self, name):
        self.names.removeItem(self.names.findText(name))
        if not self.names.count():
            self.set_editable(False)

    def update(self, name, text):
        self.names.setCurrentText(name)
        self.text_area.setPlainText(text)

    def get_text(self):
        return self.text_area.toPlainText()
