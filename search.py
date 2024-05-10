import copy
import os
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLineEdit
from dialog import TextBoxDialog


class SearchEdit(QLineEdit):
    find_next = Signal()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.find_next.emit()
        else:
            super().keyPressEvent(event)


class SearchDialog(TextBoxDialog):
    text_box_cls = SearchEdit

    def __init__(self, app):
        super().__init__(app.window, 'Search', '')
        self.edit.find_next.connect(self.find_next)
        self.edit.textChanged.connect(self.search_text_changed)
        self.grid = app.browser.grid
        self.cells = app.browser.node_labels()
        self.match_i = None
        self.matches = []

    def update_ui(self):
        if self.matches:
            grid_i = self.matches[self.match_i]
            self.grid.set_target_index(grid_i)
            search_text = self.edit.text()
            match_text = self.cells[grid_i].replace(search_text, '<u>%s</u>' % search_text)
            self.label.setText('Match %d / %d: %s' % (self.match_i + 1, len(self.matches),
                                                      match_text))
        else:
            self.label.setText('No matches')

    def find_next(self):
        if self.matches:
            self.match_i = (self.match_i + 1) % len(self.matches)
            self.update_ui()

    def update_matches(self, text):
        self.matches = [i for i, label in enumerate(self.cells)
                        if text and label and text in label]
        if self.matches:
            self.match_i = 0
            current_cell_i = self.grid.target_index()
            for match_i, cell_i in enumerate(self.matches):
                if cell_i >= current_cell_i:
                    self.match_i = match_i
                    break

    def search_text_changed(self, text):
        self.update_matches(text)
        self.update_ui()
