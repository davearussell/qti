from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtGui import QImageReader

from . import keys
import template


STYLESHEET_TMPL = """

QMainWindow {
  background-color: {{ background_color }};
}

*#Grid {
  background-color: {{ background_color }};
}

*[selectType="selected"] { color: {{ selection_color }}; }
*[selectType="marked"]   { color: {{ mark_color }};      }

*[qtiOverlay="true"] {
  background-color: rgba(0, 0, 0, 128);
}

*[qtiFont="pathbar"] {
  font-size: {{ pathbar_font_size }}pt;
  font-family: "{{ font }}";
}

*[qtiFont="keypicker"] {
  font-size: {{ key_picker_font_size }}pt;
  font-family: "{{ font }}";
}

*[qtiFont="statusbar"] {
  color: {{ text_color }};
  font-size: {{ statusbar_font_size }}pt;
  font-family: "{{ font }}";
}

*[qtiFontStyle="sep"]       { color: {{ pathbar_separator }};  }
*[qtiFontStyle="sep_fade"]  { color: {{ pathbar_separator.fade(background_color) }};  }
*[qtiFontStyle="node"]      { color: {{ text_color }}; }
*[qtiFontStyle="node_fade"] { color: {{ text_color.fade(background_color) }};  }

*#ValueBox {background-color: white; }
*[valid="false"] { color: red; }
"""


class Window(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app

    def keyPressEvent(self, event):
        self.app.keydown_hook(keys.event_keystroke(event))


class QTApp(QApplication):
    def __init__(self, keydown_hook, exit_hook):
        self.keydown_hook = keydown_hook
        self.exit_hook = exit_hook
        super().__init__([])
        QImageReader.setAllocationLimit(0)
        self.size = self.primaryScreen().size().toTuple()
        self.window = Window(self)

    def apply_settings(self, settings):
        self.setStyleSheet(template.apply(settings, STYLESHEET_TMPL))

    def set_main_widget(self, widget):
        self.window.setCentralWidget(widget)

    def run(self):
        self.window.setFixedSize(self.primaryScreen().size())
        self.window.showFullScreen()
        self.exec()
        self.exit_hook()
