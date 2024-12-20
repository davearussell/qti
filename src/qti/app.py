import copy
import traceback

from . import library
from . import browser
from . import settings
from . import cache
from . import keys
from . import macros
from . import timer
from . import ui

from .status_bar import StatusBar
from .dialogs.editor import EditorDialog
from .dialogs.bulk_edit import BulkEditDialog
from .filtering import default_filter_config
from .dialogs.deleter import DeleterDialog
from .dialogs.filter_config import FilterConfigDialog
from .dialogs.importer import make_importer
from .dialogs.metadata_editor import MetadataEditorDialog
from .dialogs.macros import MacroDialog
from .dialogs.app_settings import AppSettingsDialog
from .dialogs.key_config import KeybindDialog
from .background import BackgroundCacher
from .dialogs.search import SearchDialog
from .datastore import Datastore


class Application:
    def __init__(self, json_file):
        self.store = Datastore()
        self.settings = settings.Settings(self.store)
        self.ui = ui.cls('app')(self.settings, self.handle_keydown, self.exit_hook, self.idle_cb)
        self.keybinds = keys.Keybinds(self.store)
        self.library = library.Library(json_file)
        self.metadata = self.library.metadata
        cache.set_root_dir(self.library.root_dir)
        for macro in self.library.macros:
            self.keybinds.add_action('macro_' + macro['name'])
        self.filter_config = default_filter_config(self.library)
        self.status_bar = StatusBar(self)
        self.browser = browser.Browser(self)
        self.ui.set_main_widget(self.browser.ui)
        self.size = self.ui.size
        self.window = self.ui.window
        self.browser.load_node(self.library.make_tree(self.filter_config), mode='grid')
        self.cacher = BackgroundCacher(self)
        self.apply_settings()
        self.snapshots = []

    def handle_keydown(self, keystroke):
        action = self.keybinds.get_action(keystroke)
        if action == 'quit':
            self.ui.quit()
        elif action == 'edit':
            if self.browser.target:
                EditorDialog(self).run()
        elif action == 'bulk_edit':
            if self.browser.target:
                BulkEditDialog(self, self.browser.node).run()
        elif action == 'filter_config':
            FilterConfigDialog(self).run()
        elif action == 'delete':
            DeleterDialog(self, self.browser.marked_nodes()).run()
        elif action == 'edit_metadata':
            MetadataEditorDialog(self).run()
        elif action == 'edit_macros':
            MacroDialog(self).run()
        elif action == 'edit_keybinds':
            KeybindDialog(self).run()
        elif action == 'save_snapshot':
            self.save_snapshot()
        elif action == 'restore_snapshot':
            self.restore_snapshot()
        elif action and action.startswith('macro_'):
            self.run_macro(action[len('macro_'):])
        elif action == 'add_new_images':
            make_importer(self, self.browser.node).run()
        elif action == 'app_settings':
            AppSettingsDialog(self).run()
        elif action == 'search':
            if self.browser.mode == 'grid':
                SearchDialog(self).run()
        else:
            return False
        return True

    @property
    def viewer(self):
        if self.browser.mode != 'viewer':
            return None
        return self.browser.viewer

    def run(self):
        self.ui.run()

    def idle_cb(self, deadline):
        pass

    def timer(self, *args, **kwargs):
        return timer.Timer(self, *args, **kwargs)

    def exit_hook(self):
        self.library.save()
        self.cacher.stop()

    def apply_settings(self):
        self.ui.apply_settings(self.settings.to_dict())
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

    def run_macro(self, name):
        for macro in self.library.macros:
            if macro['name'] == name:
                try:
                    macros.run_macro(self, macro['text'])
                except Exception as e:
                    traceback.print_exc()
                    self.status_bar.set_text('Macro error: %s' % (e,), duration_s=10)
                return
        assert 0, name

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
        old_target = self.browser.target
        tree = self.library.make_tree(self.filter_config)
        if target_path:
            node, target, mode = self.select_target_by_path(tree, target_path)
        else:
            node, target, mode = self.select_target(tree, old_target)
        self.browser.load_node(node, target=target, mode=mode)
