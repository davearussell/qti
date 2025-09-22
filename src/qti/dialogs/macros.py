import copy

from xui.widgets import Widget, HBox, TextArea, PushButton, ComboBox, Label
from xui.widgets import DataDialog, LineInputDialog

from ..macros import syntax_highlight


class MacroDialog(DataDialog):
    title = 'Macros'

    color_map = {
        'STRING': (255, 220, 220),
        'COMMENT': (255, 127, 127),
        'NAME': 'lightgreen',
        'KEYWORD': 'cyan',
    }

    def __init__(self):
        super().__init__()
        self.orig_macros = self.app.library.macros
        self.macros = copy.deepcopy(self.orig_macros)
        self.names = [macro['name'] for macro in self.macros]
        self.by_name = {macro['name']: macro for macro in self.macros}
        self.name_box = ComboBox(self.names, commit_cb=self.select_name_cb)
        self.text_area = TextArea(update_cb=self.text_update, commit_cb=self.text_commit,
                                  highlight_cb=self.highlight)
        self.delete_button = PushButton("Delete", click_cb=self.delete_macro)
        header = HBox([
            Label('Macro:'),
            self.name_box,
            Widget(halign='fill'),
            PushButton("New", click_cb=self.new_macro),
            self.delete_button,
        ], spacing=10, halign='fill', child_valign='center')
        self.body.children = [header, self.text_area]
        self.load_macro(self.macros[0]['name'] if self.macros else None)

    def focus(self):
        self.text_area.focus()

    def highlight(self, text):
        return [
            [
                (text, self.color_map.get(text_type))
                for text, text_type in line
            ]
            for line in syntax_highlight(text)
        ]

    def select_name_cb(self, _):
        self.load_macro(self.name_box.choice)

    def load_macro(self, name):
        if name is not None:
            self.macro = self.by_name[name]
            self.text_area.set_enabled(True)
            self.delete_button.set_enabled(True)
            self.text_area.set_value(self.macro['text'])
            self.name_box.set_choice(name)
        else:
            self.macro = None
            self.text_area.set_enabled(False)
            self.delete_button.set_enabled(False)
            self.text_area.set_value('')

    def text_update(self):
        if self.macro:
            self.macro['text'] = self.text_area.get_value()
        self.data_updated()

    def text_commit(self):
        self.commit()
        self.exit()

    def name_checker(self, name):
        if not name:
            return 'Name is empty'
        elif name in self.by_name:
            return 'Name is a duplicate'
        return None

    def new_macro(self):
        LineInputDialog(error_checker=self.name_checker, title='New Macro').run(self.new_macro_done)

    def new_macro_done(self, name):
        if name is None:
            return
        macro = {'name': name, 'text': ''}
        self.macros.append(macro)
        self.by_name[name] = macro
        self.name_box.add_choice(name)
        self.load_macro(name)

    def delete_macro(self):
        i = self.macros.index(self.macro)
        self.macros.remove(self.macro)
        del self.by_name[self.macro['name']]
        self.name_box.remove_choice(self.macro['name'])

        if len(self.macros) > i:
            self.load_macro(self.macros[i]['name'])
        elif self.macros:
            self.load_macro(self.macros[-1]['name'])
        else:
            self.load_macro(None)

    def is_dirty(self):
        return self.macros != self.orig_macros

    def commit(self):
        old_names = {macro['name'] for macro in self.orig_macros}
        new_names = {macro['name'] for macro in self.macros}
        self.app.library.macros = self.macros
        for name in old_names - new_names:
            self.app.keybinds.delete_action('macro_' + name)
        for name in new_names - old_names:
            self.app.keybinds.add_action('macro_' + name)
        self.orig_macros = copy.deepcopy(self.macros)
