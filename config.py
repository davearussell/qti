from PySide6.QtCore import Qt

from fields import FieldDialog, SetField


def default_config(library):
    return {
        'group_by': library.default_group_by
    }


class ConfigDialog(FieldDialog):
    title = "Config"

    def __init__(self, main_window, library, config):
        super().__init__(main_window)
        self.library = library
        self.config = config
        self.need_reload = False
        self.init_fields(self.choose_fields())

    def choose_fields(self):
        return [
            SetField("group by", self.config['group_by'].copy(), self.library.keys,
                     keybind='G'),
        ]

    def accept(self):
        if self.need_reload:
            self.main_window.reload_tree()
        super().accept()

    def field_committed(self, key, value):
        self.need_reload = True
        if key == 'group by':
            self.config['group_by'] = value
        super().field_committed(key, value)
