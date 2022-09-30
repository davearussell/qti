import os
import re

import jinja2

from PySide6.QtWidgets import QDialog, QLabel
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtGui import QPalette, QPixmap
from PySide6.QtCore import Qt, QSize

from PIL import Image

import keys
from helpers import YesNoDialog
from cache import load_pixmap
from grid import Grid
from fields import FieldList, TextField,  ReadOnlyField


def find_all_images(path):
    for dirpath, _, filenames in os.walk(path):
        if '.cache/' in dirpath:
            continue
        for filename in filenames:
            if filename.lower()[-4:] in ['.jpg', '.png']:
                yield os.path.join(dirpath, filename)


def find_new_images_for(node):
    existing_images = {image.abspath for image in node.root.leaves()}
    search_dir = os.path.commonpath({image.abspath for image in node.leaves()})
    return sorted(image for image in find_all_images(search_dir) if image not in existing_images)


def f_title(text):
    """Converts 'hello_world_i_am_a_title' -> 'Hello World I Am A Title' """
    return ' '.join(text.split('_')).title()

def f_lstrip(text):
    """Converts 'Prefix Interesting Title' -> 'Interesting Title'"""
    return ' '.join(text.split()[1:])

def f_rstrip(text):
    """Converts 'Interesting Title Suffix' -> 'Interesting Title'"""
    return ' '.join(text.split()[:-1])

def f_strip_words(text, *strip_words):
    pats = [word.lower() for word in strip_words]
    words = text.split()
    while words and any(re.match(pat, words[-1].lower()) for pat in pats):
        words = words[:-1]
    return ' '.join(words)


def apply_template(template, spec):
    env = jinja2.Environment()
    env.filters.update({
        'title': f_title,
        'lstrip': f_lstrip,
        'rstrip': f_rstrip,
        'strip_words': f_strip_words,
    })
    return env.from_string(template).render(spec)


class NewImage(QLabel):
    thumbnail_size = QSize(200, 250)

    def __init__(self, library, image_path, spec):
        super().__init__()
        self.library = library
        self.image_path = image_path
        self.spec = spec
        self.pixmap = None
        self.setFixedSize(self.thumbnail_size)
        self.setAlignment(Qt.AlignCenter)
        self.fill_in_spec()

    def format_value(self, key):
        if key == 'resolution':
            return '%d x %d' % self.spec['resolution']
        return self.spec[key]

    def fill_in_spec(self):
        self.spec['path'] = os.path.relpath(self.image_path, self.library.root_dir)
        self.spec['directory'] = os.path.dirname(self.spec['path'])
        self.spec['dirname'] = os.path.basename(self.spec['directory'])
        self.spec['filename'] = os.path.basename(self.spec['path'])
        self.spec['basename'] = f_title(os.path.splitext(self.spec['filename'])[0])
        self.spec['name'] = self.spec['basename']
        self.spec['resolution'] = Image.open(self.image_path).size

    def paintEvent(self, event):
        if self.pixmap is None:
            self.pixmap = load_pixmap(self.library.root_dir, self.image_path, self.thumbnail_size)
            self.setPixmap(self.pixmap)
        super().paintEvent(event)


class ImporterDialog(QDialog):
    def __init__(self, app, node):
        super().__init__(app.window)
        self.node = node
        self.app = app
        self.library = app.library
        self.setWindowTitle("Import images")
        self.setLayout(QHBoxLayout())
        self.images = []
        new_images = find_new_images_for(node)
        if self.app.config.group_by != self.library.default_group_by:
            self.set_label("Cannot import when using custom grouping")
        elif new_images:
            self.setup_importer(new_images)
        else:
            self.set_label("No new images found")

    def set_label(self, text):
        label = QLabel()
        label.setText(text)
        self.layout().addWidget(label)

    def get_default_values(self):
        default_values = {}
        leaf = next(self.node.leaves())
        seen_our_node = not self.node.parent
        for key in self.library.default_group_by:
            default_values[key] = '' if seen_our_node else leaf.spec.get(key)
            if key == self.node.type:
                seen_our_node = True
        return default_values

    def setup_importer(self, new_images):
        default_values = self.get_default_values()
        self.setup_fields(default_values)
        self.load_grid(new_images, default_values)
        self.layout().setStretch(0, 1) # Fields get 25% of horizontal space
        self.layout().setStretch(1, 3) # Grid gets 75%

    def setup_fields(self, default_values):
        km = keys.KeyMap()
        fields = [
            ReadOnlyField('directory', ''),
            ReadOnlyField('filename', ''),
            ReadOnlyField('resolution', ''),
            TextField('name', '', keybind=km.assign_keybind('name')),
        ]
        fields += [TextField(key, default_values[key], keybind=km.assign_keybind(key))
                  for key in self.library.default_group_by]
        self.field_list = FieldList()
        self.field_list.init_fields(fields)
        self.layout().addWidget(self.field_list)
        self.field_list.setFocus()
        self.field_list.field_committed.connect(self.field_committed)

    def load_grid(self, new_images, default_values):
        self.setFixedSize(self.app.window.size() - QSize(200, 200))
        self.grid = Grid()
        self.grid.setFocusPolicy(Qt.NoFocus)
        pal = self.grid.palette()
        pal.setColor(QPalette.Window, Qt.black)
        self.grid.setPalette(pal)
        self.images = [NewImage(self.library, path, default_values.copy())
                       for path in new_images]
        self.grid.target_updated.connect(self.grid_target_updated)
        self.grid.load(self.images)
        self.layout().addWidget(self.grid)

    def delete_target(self):
        target = self.grid.target()
        if target:
            self.grid.remove_idx(self.images.index(target))
            self.images.remove(target)

    def grid_target_updated(self, image):
        field_keys = self.field_list.fields.keys()
        if image:
            values = {key: image.format_value(key) for key in image.spec if key in field_keys}
        else:
            values = {key: '' for key in field_keys}
        for key in values:
            self.field_list.fields[key].box.setText(values[key])

    def field_committed(self, field, value):
        target = self.grid.target()
        if '{' in value or field.key in self.library.default_group_by:
            # If the value is a template, or the key is in the default group hierarchy,
            # it is likely to be applicable to more than just this image, so we apply it
            # to this and all subsequent images in the import list for convenience.
            i = self.images.index(target)
            images = self.images[i:]
        else:
            images = [target]
        for image in images:
            image.spec[field.key] = apply_template(value, image.spec)
        field.box.setText(target.format_value(field.key))

    def commit(self):
        if not self.images:
            self.accept()
            return

        required_keys = self.library.default_group_by + ['name']
        if any(not image.spec.get(key) for key in required_keys for image in self.images):
            if not YesNoDialog(self, "Missing keys", "Some images are missing required keys. "
                              "Proceed anyway?").exec():
                return

        for image in self.images:
            spec = {}
            for key in self.library.builtin_keys + self.library.custom_keys:
                value = image.spec.get(key)
                if not value:
                    value = self.library.default_value(key)
                spec[key] = value
            self.library.images.append(spec)
        self.app.reload_tree()
        self.accept()

    def keyPressEvent(self, event):
        action = keys.get_action(event)
        key = event.key()
        if action == 'select':
            self.commit()
        elif action == 'cancel':
            self.reject()
        elif action == 'delete':
            self.delete_target()
        elif action in ['up', 'down', 'left', 'right']:
            self.grid.scroll(action)
        else:
            event.ignore()
