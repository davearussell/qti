import os
from functools import partial

from ..image import Image

from .. import template
from ..grid import Grid

from .simple import InfoDialog
from .common import DataDialog
from .fields import FieldGroup, TextField, ReadOnlyField

from .. import ui


def find_all_images(path):
    for dirpath, _, filenames in os.walk(path):
        if '.cache/' in dirpath:
            continue
        for filename in filenames:
            if filename.lower()[-4:] in ['.jpg', '.png']:
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
        'resolution': list(Image(image_path).size),

        # These are not saved in the database but may be helpful for templating
        'directory': os.path.dirname(relpath),
        'dirname': os.path.basename(os.path.dirname(relpath)),
        'stem': os.path.splitext(os.path.basename(relpath))[0],
    }


class ImporterDialog(DataDialog):
    title = 'Import images'
    ui_cls = ui.cls('importer_dialog')
    actions = {
        'ok': None,
        'cancel': None,
    }

    def __init__(self, app, node, images):
        self.app = app
        self.node = node
        self.library = app.library
        self.keybinds = app.keybinds
        self.default_values = self.get_default_values()
        self.images = images
        self.specs = self.make_specs(self.images)
        self.field_group = self.setup_fields()
        self.grid = self.setup_grid()
        super().__init__(app, app.window)
        self.data_updated()

    def make_specs(self, images):
        return [make_spec(image_path,
                          self.library.root_dir,
                          self.default_values | {'i': i})
                for i, image_path in enumerate(images)]

    @property
    def ui_args(self):
        return {
            'fields': self.field_group.ui,
            'grid': self.grid.ui,
        }

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

    def setup_grid(self):
        grid = Grid(self.app, scroll_cb=self.grid_target_updated, no_selection=True)
        cells = [{'image_path': image} for image in self.images]
        grid.load(cells)
        return grid

    def dirty(self):
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

    def grid_target_updated(self, index):
        spec = self.specs[index]
        for field in self.field_group.fields:
            field.set_value(str(spec[field.key]))
            field.mark_clean()

    def field_updated(self, field):
        if not field.dirty():
            return

        value = field.get_value()

        i = self.grid.target_index()
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

    def error(self):
        required_keys = self.library.metadata.hierarchy() + ['name']
        if not all(all(spec.get(key) for key in required_keys)
                   for spec in self.specs):
            return "Some images are missing required keys"

    def commit(self):
        self.library.base_tree.populate(self.specs)
        self.app.reload_tree()

    def keydown_cb(self, keystroke):
        return self.grid.handle_action(self.keybinds.get_action(keystroke))


def make_importer(app, node):
    problem = None
    images = find_new_images(app.library.base_tree)
    if not app.filter_config.is_default(): # XXX can we relax this restriction?
        problem = "Cannot import when using custom grouping"
    if not images:
        problem = "No new images found"
    if problem:
        return InfoDialog(app, app.window, problem, title="Importer error")
    else:
        return ImporterDialog(app, node, images)
