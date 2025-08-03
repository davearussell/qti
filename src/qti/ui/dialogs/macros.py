from xui.widgets import Widget, HBox, TextArea, PushButton, ComboBox, Label

from .common import DataDialogWidget


class MacroDialogWidget(DataDialogWidget):
    color_map = {
        'STRING': (255, 220, 220),
        'COMMENT': (255, 127, 127),
        'NAME': 'lightgreen',
        'KEYWORD': 'cyan',
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
        return [
            [
                (text, self.color_map.get(text_type))
                for text, text_type in line
            ]
            for line in self.highlight_cb(text)
        ]

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
