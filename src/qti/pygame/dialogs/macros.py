from xui.widgets import Widget, HBox, TextArea, PushButton, ComboBox, Label

from .common import DataDialogWidget


class MacroDialogWidget(DataDialogWidget):
    color_map = {
        'comment': (255, 128, 128),
        'error': 'red',
        'command': 'cyan',
        'variable': 'lightgreen',
    }

    def __init__(self, names, settings, highlight_cb, select_name_cb,
                 update_cb, new_cb, delete_cb, **kwargs):
        super().__init__(**kwargs)
        self.select_name_cb = select_name_cb
        self.highlight_cb = highlight_cb
        self.name_box = ComboBox(names, commit_cb=self.name_update)
        self.text_area = TextArea(update_cb=update_cb, highlight_cb=self.highlight)
        header = HBox([
            Label('Macro:'),
            self.name_box,
            Widget(halign='fill'),
            PushButton("New", click_cb=new_cb),
            PushButton("Delete", click_cb=delete_cb),
        ], spacing=10, halign='fill', child_valign='center')
        self.body.children = [header, self.text_area]

    def run(self, *args):
        super().run(*args)
        if self.name_box.choice:
            self.text_area.focus()
        else:
            self.text_area.set_enabled(False)

    def highlight(self, text):
        for i, n, label in self.highlight_cb(text):
            yield text[i:i+n], self.color_map.get(label)

    def name_update(self, _):
        self.select_name_cb(self.name_box.choice)

    def add_name(self, name):
        self.name_box.add_choice(name)
        self.text_area.set_enabled(True)

    def remove_name(self, name):
        if name == self.name_box.choice:
            self.text_area.set_value('')
        self.name_box.remove_choice(name)
        if not self.name_box.choices:
            self.text_area.set_enabled(False)
            self.focus()

    def update(self, macro_name, macro_text):
        if macro_name:
            self.name_box.set_choice(macro_name)
            self.text_area.set_value(macro_text)

    def get_text(self):
        return self.text_area.get_value()
