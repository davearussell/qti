import os

from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPainter, QPixmap

from PIL import Image

import template
from keys import KeyMap
from dialog import YesNoDialog, TextBoxDialog, InfoDialog, DataDialog, AbortCommit
from grid import Grid, Cell
from fields import FieldGroup, TextField,  ReadOnlyField


def find_all_images(path):
    for dirpath, _, filenames in os.walk(path):
        if '.cache/' in dirpath:
            continue
        for filename in filenames:
            if filename.lower()[-4:] in ['.jpg', '.png']:
                yield os.path.join(dirpath, filename)


def find_new_images_for(node):
    existing_images = {image.abspath for image in node.root.images()}
    search_dir = node.root.base_node.root_dir
    if existing_images and node.parent:
        search_dir = os.path.commonpath({image.abspath for image in node.images()})
        if os.path.isfile(search_dir):
            search_dir = os.path.dirname(search_dir)
    return sorted(image for image in find_all_images(search_dir) if image not in existing_images)


class NewImage(Cell):
    type = 'image'

    def __init__(self, settings, library, image_path, spec, size):
        super().__init__(size)
        self.settings = settings
        self.abspath = image_path
        self.relpath = os.path.relpath(self.abspath, library.root_dir)
        self.name = template.f_title(os.path.splitext(os.path.basename(self.relpath))[0])
        self.spec = spec
        self.fill_in_spec()

    def get_key(self, key):
        return self.spec.get(key, '')

    def format_value(self, key):
        if key == 'resolution':
            return '%d x %d' % tuple(self.spec['resolution'])
        return self.spec[key]

    def fill_in_spec(self):
        self.spec['name'] = self.name
        self.spec['path'] = self.relpath
        self.spec['resolution'] = list(Image.open(self.abspath).size)

    def load_pixmap(self):
        # TODO: refactor away duplication with browser.Thumbnail
        pixmap = super().load_pixmap()
        image = QPixmap(self.abspath).scaled(self.size,
                                             aspectMode=Qt.KeepAspectRatio,
                                             mode=Qt.FastTransformation)
        iw, ih = image.size().toTuple()
        p = QPainter(pixmap)
        p.fillRect(0, 0, self.width, self.height, self.settings.get('background_color'))
        p.drawPixmap((self.width - iw) // 2, (self.height - ih) // 2, image)
        return pixmap


class ImporterDialog(DataDialog):
    title = 'Import images'

    def __init__(self, app, node):
        super().__init__(app)
        self.node = node
        self.library = app.library
        self.keybinds = app.keybinds
        self.body = QWidget()
        self.body.setLayout(QHBoxLayout())
        self.layout().addWidget(self.body)
        self.images = []
        new_images = find_new_images_for(node)
        if not self.app.filter_config.is_default():
            self.set_label("Cannot import when using custom grouping")
        elif new_images:
            self.setup_importer(new_images)
        else:
            self.set_label("No new images found")
        self.add_buttons(apply=bool(new_images), cancel=bool(new_images))

    def dirty(self):
        return bool(self.images)

    def set_label(self, text):
        label = QLabel()
        label.setText(text)
        self.body.layout().addWidget(label)

    def get_default_values(self):
        default_values = {}
        try:
            image = next(self.node.images())
        except StopIteration:
            return {}
        seen_our_node = not self.node.parent
        for key in self.library.metadata.hierarchy():
            default_values[key] = '' if seen_our_node else image.spec.get(key)
            if key == self.node.type:
                seen_our_node = True
        return default_values

    def setup_importer(self, new_images):
        default_values = self.get_default_values()
        self.setup_fields(default_values)
        self.load_grid(new_images, default_values)
        self.setFixedSize(self.app.window.size() - QSize(200, 200))
        self.field_group.setFixedWidth(self.width() // 3)

    def setup_fields(self, default_values):
        km = KeyMap()
        fields = [
            ReadOnlyField('directory', ''),
            ReadOnlyField('filename', ''),
            ReadOnlyField('resolution', ''),
            TextField('name', '', keymap=km),
        ]
        fields += [TextField(key, default_values.get(key, ''), keymap=km)
                  for key in self.library.metadata.hierarchy()]
        self.field_group = FieldGroup()
        self.field_group.init_fields(fields)
        self.body.layout().addWidget(self.field_group)
        self.field_group.setFocus()
        self.field_group.field_unfocused.connect(self.field_updated)

    def load_grid(self, new_images, default_values):
        self.grid = Grid(self.app.settings, self.keybinds)
        self.images = [NewImage(self.app.settings, self.library, path, default_values.copy(),
                                self.app.settings.thumbnail_size)
                       for path in new_images]
        self.grid.target_updated.connect(self.grid_target_updated)
        self.grid.load(self.images, target=self.images[0])
        self.body.layout().addWidget(self.grid)

    def drop_images(self, images):
        self.images = [image for image in self.images if image not in images]
        if self.grid.target in images:
            if not self.images:
                target = None
            elif self.grid.target.index >= len(self.images):
                target = self.images[-1]
            else:
                target = self.images[self.grid.target.index]
        else:
            target = self.grid.target
        self.grid.load(self.images, target=target)

    def delete_target(self):
        if self.grid.target:
            self.drop_images([self.grid.target])

    def grid_target_updated(self, image):
        for field in self.field_group.fields:
            if image and field.key in image.spec:
                field.set_value(image.format_value(field.key))
            else:
                field.set_value('')
            field.mark_clean()

    def field_updated(self, field):
        if not field.dirty():
            return

        value = field.get_value()

        target = self.grid.target
        i = self.images.index(target)
        if '{' in value or field.key in self.library.metadata.hierarchy():
            # If the value is a template, or the key is in the default group hierarchy,
            # it is likely to be applicable to more than just this image, so we apply it
            # to this and all subsequent images in the import list for convenience.
            images = self.images[i:]
        else:
            images = [target]
        for j, image in enumerate(images):
            image.index = i + j
            image.spec[field.key] = template.evaluate(image, value, self.library.metadata)
        field.set_value(target.format_value(field.key))
        field.mark_clean()
        self.data_updated()

    def commit(self):
        required_keys = self.library.metadata.hierarchy() + ['name']
        ready = [image for image in self.images
                 if all(image.spec.get(key) for key in required_keys)]
        if not ready:
            InfoDialog(self, "Missing keys", "All images are missing required keys. Canont import.").exec()
            raise AbortCommit()
        if len(ready) < len(self.images):
            if not YesNoDialog(self, "Missing keys", "Some images are missing required keys. "
                              "These will not be added. Proceed anyway?").exec():
                raise AbortCommit()

        self.library.base_tree.populate([image.spec for image in ready])
        self.app.reload_tree()
        self.drop_images(ready)


    def exclude_images(self, pattern):
        matches = [image for image in self.images if pattern.lower() in image.path.lower()]
        if matches:
            self.drop_images(matches)

    def keyPressEvent(self, event):
        action = self.keybinds.get_action(event)
        key = event.key()
        if action == 'delete':
            self.delete_target()
        elif action in ['up', 'down', 'left', 'right']:
            self.grid.scroll(action)
        elif event.key() == Qt.Key_X:
            dialog = TextBoxDialog(self, "Exclude images",
                                   "Exclude images that match this pattern:")
            dialog.result.connect(self.exclude_images)
            dialog.exec()
        else:
            super().keyPressEvent(event)
