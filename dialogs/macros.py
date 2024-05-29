import copy
from .common import DataDialog
from .simple import LineEditDialog
from qt.dialogs.macros import MacroDialogWidget
from macros import Command


class NewDialog(LineEditDialog):
    title = 'New macro'

    def __init__(self, parent, names):
        self.names = names
        super().__init__(parent)

    def error(self):
        name = self.ui.get_value()
        if not name:
            return 'Name is empty'
        if name in self.names:
            return 'Name is a duplicate'


class MacroDialog(DataDialog):
    title = 'Macros'
    ui_cls = MacroDialogWidget

    def __init__(self, app):
        self.app = app
        self.orig_macros = app.library.macros
        self.macros = copy.deepcopy(self.orig_macros)
        self.by_name = {macro['name']: macro for macro in self.macros}
        super().__init__(app.window)
        self.select_name(self.macros[0]['name'] if self.macros else None)

    @property
    def ui_args(self):
        return {
            'names': [macro['name'] for macro in self.macros],
            'settings': self.app.settings,
            'highlight_cb': Command.syntax_highlight,
            'select_name_cb': self.select_name,
            'update_cb': self.handle_update,
            'new_cb': self.new_macro,
            'delete_cb': self.delete_macro,
        }

    def select_name(self, name):
        if name:
            self.macro = self.by_name[name]
            self.ui.update(name, self.macro['text'])
        else:
            self.macro = None
            self.ui.update('', '')

    def handle_update(self):
        if self.macro:
            self.macro['text'] = self.ui.get_text()
        self.data_updated()

    def new_macro(self):
        name = NewDialog(self.ui, self.by_name).run()
        if name is None:
            return
        macro = {'name': name, 'text': ''}
        self.macros.append(macro)
        self.by_name[name] = macro
        self.ui.add_name(name)
        self.select_name(name)

    def delete_macro(self):
        i = self.macros.index(self.macro)
        self.macros.remove(self.macro)
        del self.by_name[self.macro['name']]
        self.ui.remove_name(self.macro['name'])

        if len(self.macros) > i:
            self.select_name(self.macros[i]['name'])
        elif self.macros:
            self.select_name(self.macros[-1]['name'])
        else:
            self.select_name(None)

    def dirty(self):
        return self.macros != self.orig_macros

    def commit(self):
        old_names = {macro['name'] for macro in self.orig_macros}
        new_names = {macro['name'] for macro in self.macros}
        self.app.library.macros = self.macros
        for name in old_names - new_names:
            self.app.keybinds.delete_action('macro_' + name)
        for name in new_names - old_names:
            self.app.keybinds.add_action('macro_' + name)
