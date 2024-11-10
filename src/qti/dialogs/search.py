from .. import ui
from .common import Dialog


class SearchDialog(Dialog):
    title = "Search"
    actions = {'ok': ''}
    ui_cls = ui.cls('search_dialog')

    def __init__(self, app):
        self.ui_args  = {'update_cb': self.search_text_changed, 'commit_cb': self.find_next}
        super().__init__(app, app.window)
        self.grid = app.browser.grid
        self.cells = app.browser.node_labels()
        self.match_i = None
        self.matches = []

    def update_ui(self):
        if self.matches:
            grid_i = self.matches[self.match_i]
            self.grid.set_target_index(grid_i)
            search_text = self.ui.get_value()
            match_text = self.cells[grid_i].replace(search_text, '<u>%s</u>' % search_text)
            self.ui.set_label('Match %d / %d: %s' % (self.match_i + 1, len(self.matches),
                                                     match_text))
        else:
            self.ui.set_label('No matches')

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
