import pygame

from xui import app as xapp

# HACK: makes pygame render fonts at about the same size as qt
FONT_RATIO = 1.35

def make_gui_settings(settings):
    return {

        'font': settings.font,
        'color': settings.text_color,
        'border_color': settings.text_color,
        'font_size': int(settings.font_size * FONT_RATIO),

        'Screen': {
            'bgcolor': settings.background_color,
        },

        'GridWidget': {
            'cell_size': settings.thumbnail_size,
            'select_color': settings.selection_color,
            'mark_color': settings.mark_color,
        },

        'BrowserWidget': {
            'name_size': int(settings.header_font_size * FONT_RATIO),
            'count_size': int(2 * settings.header_font_size * FONT_RATIO),
        },

        'StatusBarWidget': {
            'font_size': int(settings.header_font_size * FONT_RATIO),
        },

        'DialogWidget': {
            'header_font_size': int(settings.header_font_size * FONT_RATIO),
        },

        'PathbarWidget': {
            'font_size': int(settings.header_font_size * FONT_RATIO),
            'sep_color': settings.pathbar_separator,
        },

    }


class App(xapp.App):
    framerate = 30

    def __init__(self, settings, keydown_hook, exit_hook, idle_cb):
        super().__init__()
        self.window = self.screen
        self.settings = settings
        self.keydown_hook = keydown_hook
        self.exit_hook = exit_hook
        self.idle_cb = idle_cb

    def apply_settings(self, settings):
        assert settings == self.settings.to_dict()
        gui_settings = make_gui_settings(self.settings)
        self.screen.apply_settings(gui_settings)

    def set_main_widget(self, widget):
        self.screen.children.append(widget)
        self.screen.layout()
        widget.focus()

    def handl_keydown(self, keystroke):
        return self.keydown_hook(keystroke)

    def pre_exit_hook(self):
        self.exit_hook()

    def idle_hook(self, deadline):
        self.idle_cb(deadline)
