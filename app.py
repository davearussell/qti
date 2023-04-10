import copy

import jinja2

from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtGui import QImageReader
from PySide6.QtCore import Signal, QSize, QSettings

import library
import browser
import settings
from status_bar import StatusBar
from editor import EditorDialog
from bulk_edit import BulkEditDialog
from filtering import default_filter_config, FilterConfigDialog
from deleter import DeleterDialog
from importer import ImporterDialog
from metadata import MetadataEditorDialog
from app_settings import AppSettingsDialog
from key_config import KeybindDialog
from cache import set_root_dir
from background import BackgroundCacher
import keys

STYLESHEET_TMPL = """

QMainWindow {
  background-color: {{ background_color.name() }};
}

*#Grid {
  background-color: {{ background_color.name() }};
}

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
  color: {{ text_color.name() }};
  font-size: {{ statusbar_font_size }}pt;
  font-family: "{{ font }}";
}

*[qtiFontStyle="sep"]       { color: {{ pathbar_separator.name() }};  }
*[qtiFontStyle="sep_fade"]  { color: {{ pathbar_separator.darker().name() }};  }
*[qtiFontStyle="node"]      { color: {{ text_color.name() }}; }
*[qtiFontStyle="node_fade"] { color: {{ text_color.darker().name() }};  }

*#ValueBox {background-color: white; }
*[valid="false"] { color: red; }
"""


class Window(QMainWindow):
    def __init__(self, app, size):
        super().__init__()
        self.app = app
        self.keybinds = app.keybinds
        self.browser = browser.Browser(app)
        self.setCentralWidget(self.browser)
        self.snapshots = []

    def save_snapshot(self):
        snapshot = (self.browser.node, self.browser.target, self.browser.mode,
                    copy.deepcopy(self.app.filter_config))
        self.snapshots.append(snapshot)

    def restore_snapshot(self):
        if self.snapshots:
            node, target, mode, self.app.filter_config = self.snapshots.pop()
            self.browser.load_node(node, target=target, mode=mode)

    def jump_to_subject(self):
        # TODO generalize this via a dialog
        mode = self.browser.mode
        target = self.browser.target
        image = next(target.leaves())
        subjects = image.spec['subjects']
        if not subjects:
            return
        self.save_snapshot()
        self.app.filter_config.group_by = ['subjects:%s' % ','.join(subjects)]
        self.app.filter_config.clear_filters()
        root = self.app.library.make_tree(self.app.filter_config)
        node = [x for x in root.children if x.name in subjects][0]
        self.browser.load_node(node, mode=mode)

    def keyPressEvent(self, event):
        action = self.keybinds.get_action(event)
        if action == 'quit':
            self.app.quit()
        elif action == 'edit':
            if self.browser.target:
                editor = EditorDialog(self.app, self.browser)
                editor.exec()
        elif action == 'bulk_edit':
            if self.browser.target:
                BulkEditDialog(self.app, self.browser.node).exec()
        elif action == 'filter_config':
            FilterConfigDialog(self.app, self.app.library, self.app.filter_config).exec()
        elif action == 'delete':
            DeleterDialog(self.app, self.browser.target).exec()
        elif action == 'edit_metadata':
            MetadataEditorDialog(self.app).exec()
        elif action == 'edit_keybinds':
            KeybindDialog(self.app).exec()
        elif action == 'save_snapshot':
            self.save_snapshot()
        elif action == 'restore_snapshot':
            self.restore_snapshot()
        elif action == 'jump_to_subject':
            self.jump_to_subject()
        elif action == 'add_new_images':
            ImporterDialog(self.app, self.browser.node).exec()
        elif action == 'app_settings':
            AppSettingsDialog(self.app).exec()
        else:
            event.ignore()


class Application(QApplication):
    quitting = Signal()

    def __init__(self, json_file):
        super().__init__([])
        QImageReader.setAllocationLimit(0)
        self.q = QSettings('davesoft', 'qti')
        self.settings = settings.Settings(self.q)
        self.keybinds = keys.Keybinds(self.q)
        self.library = library.Library(json_file)
        for qf in self.library.quick_filters:
            self.keybinds.add_action('quick_filter_' + qf)
        self.quitting.connect(self.library.save)
        self.filter_config = default_filter_config(self.library)
        self.status_bar = StatusBar()
        self.window = Window(self, self.primaryScreen().size())
        set_root_dir(self.library.root_dir)
        self.cacher = BackgroundCacher(self)
        self.apply_settings()

    @property
    def viewer(self):
        if self.window.browser.mode != 'viewer':
            return None
        return self.window.browser.viewer

    def exec(self):
        self.reload_tree()
        self.window.showFullScreen()
        super().exec()
        self.quitting.emit()

    def apply_settings(self):
        env = jinja2.Environment().from_string(STYLESHEET_TMPL)
        stylesheet = env.render(self.settings.to_dict())
        self.setStyleSheet(stylesheet)
        self.reload_tree()
        self.cacher.cache_all_images()

    def reload_tree(self):
        target = self.window.browser.target
        tree = self.library.make_tree(self.filter_config)

        if not (target and tree.children):
            self.window.browser.load_node(tree, mode='grid')
            return

        path_from_root = []
        node = target
        while node.parent:
            path_elem = (node.type, node.name, node.parent.children.index(node))
            path_from_root.insert(0, path_elem)
            node = node.parent

        browser_mode = None
        node = None
        target = tree
        for node_type, name, idx in path_from_root:
            node = target
            targets = [child for child in node.children if child.name == name]
            if not targets:
                if idx >= len(node.children):
                    idx = len(node.children) - 1
                target = node.children[idx]
                if target.type != 'image':
                    browser_mode = 'grid'
                break
            target = targets[0]

        self.window.browser.load_node(node, target=target, mode=browser_mode)
