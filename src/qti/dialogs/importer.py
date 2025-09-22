import os
from functools import partial

from xui.widgets import InfoDialog, DataDialog, HBox, Label, Grid
from xui.widgets import FieldGroup, TextField, ReadOnlyField
from xui.widgets.image import get_resolution, Image

from .. import template
from ..cache import ensure_cached

SUPPORTED_EXTNS = ['.jpg', '.png', '.webp']


def find_all_images(path):
    for dirpath, _, filenames in os.walk(path):
        if '.cache/' in dirpath:
            continue
        for filename in filenames:
            if os.path.splitext(filename)[1].lower() in SUPPORTED_EXTNS:
                yield os.path.join(dirpath, filename)


def find_new_images(tree):
    existing_images = {image.abspath for image in tree.images()}
    return sorted(image for image in find_all_images(tree.root_dir) if image not in existing_images)


def make_spec(image_path, root_dir, defaults):
    relpath = os.path.relpath(image_path, root_dir)
    return defaults | {
        'path': relpath,
        'name': template.f_title(os.path.splitext(os.path.basename(image_path))[0]),
        'filename': os.path.basename(relpath),
        'resolution': list(get_resolution(image_path)),

        # These are not saved in the database but may be helpful for templating
        'directory': os.path.dirname(relpath),
        'dirname': os.path.basename(os.path.dirname(relpath)),
        'stem': os.path.splitext(os.path.basename(relpath))[0],
    }


class Thumbnail(Image):
    def __init__(self, path, size):
        self._path = path
        super().__init__(None, size)

    def draw(self):
        self.path = ensure_cached(self._path, self.size)
        super().draw()


class ImporterDialog(DataDialog):
    title = 'Import images'
    actions = ['cancel', 'ok']

    def __init__(self):
        super().__init__()
        self.node = self.app.browser.node
        self.library = self.app.library
        self.default_values = self.get_default_values()
        self.images = find_new_images(self.app.library.base_tree)
        self.specs = self.make_specs(self.images)
        if not self.images:
            self.problem = "No new images found"
        elif not self.app.filter_config.is_default(): # XXX can we relax this restriction?
            self.problem = "Cannot import when using custom grouping"
        else:
            self.problem = None
        self.field_group = self.setup_fields()
        size = self.app.settings.thumbnail_size
        self.grid = Grid([Thumbnail(image, size) for image in self.images],
                         click_cb=self.grid_click_cb)
        if self.images:
            self.update_grid_target(0)
        self.body.children = [HBox([self.field_group, self.grid])]

    def focus(self):
        self.field_group.focus()

    def run(self, exit_cb=None):
        super().run(exit_cb)
        if self.problem:
            InfoDialog(self.problem, title="Importer error").run(exit_cb=lambda _: self.exit())

    def make_specs(self, images):
        return [make_spec(image_path,
                          self.library.root_dir,
                          self.default_values | {'i': i})
                for i, image_path in enumerate(images)]

    def setup_fields(self):
        fields = [
            ReadOnlyField('directory', ''),
            ReadOnlyField('filename', ''),
            ReadOnlyField('resolution', ''),
            TextField('name', ''),
        ]
        fields += [TextField(key, self.default_values.get(key, ''))
                  for key in self.library.metadata.hierarchy()]
        field_group = FieldGroup(fields, commit_cb=self.field_updated)
        return field_group

    def grid_click_cb(self, image_i, is_double):
        self.update_grid_target(image_i)

    def is_dirty(self):
        return True

    def get_default_values(self):
        try:
            image_spec = next(self.node.images()).spec
        except StopIteration:
            image_spec = {}
        default_values = {}
        seen_our_node = not self.node.parent
        for key in self.library.metadata.hierarchy():
            default_values[key] = '' if seen_our_node else image_spec.get(key)
            if key == self.node.type:
                seen_our_node = True
        return default_values

    def update_grid_target(self, image_i):
        self.grid.set_target_i(image_i)
        spec = self.specs[image_i]
        for field in self.field_group.fields:
            field.set_value(str(spec[field.key]))
            field.mark_clean()

    def field_updated(self, field):
        if not field.dirty():
            return

        value = field.get_value()

        i = self.grid.get_target_i()
        if '{' in value or field.key in self.library.metadata.hierarchy():
            # If the value is a template, or the key is in the default group hierarchy,
            # it is likely to be applicable to more than just this image, so we apply it
            # to this and all subsequent images in the import list for convenience.
            specs = self.specs[i:]
        else:
            specs = [self.specs[i]]
        for spec in specs:
            spec[field.key] = template.apply(spec, value)
        field.set_value(str(specs[0][field.key]))
        field.mark_clean()
        self.data_updated()

    def get_error(self):
        required_keys = self.library.metadata.hierarchy() + ['name']
        if not all(all(spec.get(key) for key in required_keys)
                   for spec in self.specs):
            return "Some images are missing required keys"

    def commit(self):
        self.library.base_tree.populate(self.specs)
        self.app.reload_tree()

    def handle_keydown(self, keystroke):
        action = self.app.keybinds.get_action(keystroke)
        if self.app.keybinds.is_scroll(action):
            self.update_grid_target(self.grid.neighbour(self.grid.get_target_i(), action))
            return True
        return super().handle_keydown(keystroke)
