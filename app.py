import copy

import jinja2

from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtGui import QImageReader

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
from quick_filters import QuickFilterDialog
from quick_actions import QuickActionDialog
from app_settings import AppSettingsDialog
from key_config import KeybindDialog
from background import BackgroundCacher
from search import SearchDialog
import keys
import template
from qt.datastore import Datastore

from qt.keys import event_keystroke

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
        self.setFixedSize(size)
        self.browser = browser.Browser(app)
        self.setCentralWidget(self.browser)

    def keyPressEvent(self, event):
        keystroke = event_keystroke(event)
        action = self.keybinds.get_action(keystroke)
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
            DeleterDialog(self.app, self.browser.marked_nodes()).exec()
        elif action == 'edit_metadata':
            MetadataEditorDialog(self.app).exec()
        elif action == 'edit_quick_filters':
            QuickFilterDialog(self.app).exec()
        elif action == 'edit_quick_actions':
            QuickActionDialog(self.app).exec()
        elif action == 'edit_keybinds':
            KeybindDialog(self.app).exec()
        elif action == 'save_snapshot':
            self.app.save_snapshot()
        elif action == 'restore_snapshot':
            self.app.restore_snapshot()
        elif action and action.startswith('quick_filter_'):
            self.app.apply_quick_filter(action[len('quick_filter_'):])
        elif action and action.startswith('quick_action_'):
            self.app.apply_quick_action(action[len('quick_action_'):])
        elif action == 'add_new_images':
            ImporterDialog(self.app, self.browser.node).exec()
        elif action == 'app_settings':
            AppSettingsDialog(self.app).exec()
        elif action == 'search':
            SearchDialog(self.app).exec()
        else:
            event.ignore()


class Application(QApplication):
    def __init__(self, json_file):
        super().__init__([])
        QImageReader.setAllocationLimit(0)
        self.store = Datastore()
        self.settings = settings.Settings(self.store)
        self.keybinds = keys.Keybinds(self.store)
        self.library = library.Library(json_file)
        for qf in self.library.quick_filters:
            self.keybinds.add_action('quick_filter_' + qf)
        for qf in self.library.quick_actions:
            self.keybinds.add_action('quick_action_' + qf)
        self.filter_config = default_filter_config(self.library)
        self.status_bar = StatusBar()
        self.window = Window(self, self.primaryScreen().size())
        self.browser = self.window.browser
        self.cacher = BackgroundCacher(self)
        self.apply_settings()
        self.snapshots = []

    @property
    def viewer(self):
        if self.browser.mode != 'viewer':
            return None
        return self.browser.viewer

    def exec(self):
        self.window.browser.load_node(self.library.make_tree(self.filter_config), mode='grid')
        self.window.showFullScreen()
        super().exec()
        self.exit_hook()

    def exit_hook(self):
        self.library.save()
        self.cacher.stop()

    def apply_settings(self):
        env = jinja2.Environment().from_string(STYLESHEET_TMPL)
        stylesheet = env.render(self.settings.to_dict())
        self.setStyleSheet(stylesheet)
        self.browser.reload_node()
        self.cacher.cache_all_images()

    def save_snapshot(self):
        snapshot = (self.browser.node, self.browser.target, self.browser.mode,
                    copy.deepcopy(self.filter_config))
        self.snapshots.append(snapshot)

    def restore_snapshot(self):
        if self.snapshots:
            node, target, mode, self.filter_config = self.snapshots.pop()
            self.browser.load_node(node, target=target, mode=mode)

    def apply_quick_filter(self, name):
        qf = self.library.quick_filters.get(name)
        if qf is None:
            return

        target = self.browser.target
        keys = self.library.metadata.groupable_keys()
        key_values = {key: set() for key in keys}

        for image in target.images():
            for key in keys:
                if image.spec.get(key):
                    value = image.spec[key]
                    if isinstance(value, str):
                        value = [value]
                    key_values[key] |= set(value)
        spec = {key: ','.join(values) for key, values in key_values.items()}
        spec['name'] = target.name

        self.save_snapshot()
        self.filter_config.clear_filters()
        skip_root = False
        if qf.get('group'):
            group_by = []
            for i, word in enumerate(qf['group']):
                if i == 0 and ':' in word:
                    skip_root = True
                group_by.append(template.apply(spec, word))
            self.filter_config.group_by = group_by
        if qf.get('order'):
            self.filter_config.order_by = qf['order'].copy()
        if qf.get('expr'):
            self.filter_config.custom_expr = qf['expr']

        root = self.library.make_tree(self.filter_config)
        node = root.children[0] if root.children and skip_root else root
        mode = 'grid' if node.type != 'image' else self.browser.mode
        self.browser.load_node(node, mode=mode)

    def apply_quick_action(self, name):
        qa = self.library.quick_actions.get(name)
        if qa is None:
            return
        md = self.library.metadata.lut.get(qa['key'])
        if md is None:
            return

        target = self.browser.target
        if not md.multi:
            if qa['operation'] != 'add':
                return
            target.update(qa['key'], qa['value'])
        else:
            if qa['operation'] == 'add':
                target.update_set(qa['key'], add={qa['value']}, remove=set())
                self.status_bar.set_text("Added %(key)s %(value)r" % qa, duration_s=5)
            elif qa['operation'] == 'remove':
                target.update_set(qa['key'], remove={qa['value']}, add=set())
                self.status_bar.set_text("Removed %(key)s %(value)r" % qa, duration_s=5)
            elif qa['operation'] == 'toggle':
                assert 0, "write me"
                self.status_bar.set_text("Toggled %(key)s %(value)r" % qa, duration_s=5)
            else:
                assert 0, qa

    def select_target(self, new_tree, old_target):
        # If either the old or current tree was empty, return the root of the new tree
        if not(old_target and new_tree.children):
            return new_tree, None, 'grid'

        # Search for images that are present in both old and new trees. Initially we only
        # look for images that are descendants of the old target, but widen the search if
        # none exist
        old_node = old_target
        image = None
        while old_node and not image:
            old_images = {image.base_node for image in old_node.images()}
            for image in new_tree.images():
                if image.base_node in old_images:
                    break
            else:
                image = None
                old_target = old_node
                old_node = old_node.parent

        # If we found a common image, we will point at one of its ancenstors.
        # The logic is a bit fiddly, but aims for the principle of least surprise
        # 1. If the image belongs to the old target,
        #    a. If we're still grouping the old target's type, choose the ancestor
        #       of the same type
        #    b. Otherwise, if we're grouping by the old target's *parent's* type,
        #       choose said type's child that contains our image
        # 2. Otherwise, choose the closest-to-leaf ancestor which is a parent of
        #    the common image
        if image:
            ancestors = {node.type: node for node in image.ancestors()}
            if old_target.type in ancestors:
                target = ancestors[old_target.type]
            elif old_target.parent and old_target.parent.type in ancestors:
                parent = ancestors[old_target.parent.type]
                target = [node for node in ancestors.values() if node.parent == parent][0]
            else:
                target = image # XXX or is root better?
            mode = None if target.type == 'image' else 'grid'
            return target.parent, target, mode

        # If we get here, then there are no images in common between the old and new views.
        # Just point at the root of the tree.
        return new_tree, None, 'grid'

    def select_target_by_path(self, tree, target_path):
        if not tree.children: # tree is empty
            return tree, None, None

        target = tree

        while target.children:
            child_type = target.children[0].type
            if child_type not in target_path:
                break # we've reached our target node

            child_key = target_path.get(child_type)
            child = target.lut.get(child_key)
            if child is None: # target is no longer in view, select a sibling instead
                return target, target.children[0], None
            target = child

        return target.parent, target, None

    def reload_tree(self, target_path=None):
        old_target = self.window.browser.target
        tree = self.library.make_tree(self.filter_config)
        if target_path:
            node, target, mode = self.select_target_by_path(tree, target_path)
        else:
            node, target, mode = self.select_target(tree, old_target)
        self.window.browser.load_node(node, target=target, mode=mode)
