import json
import os

import metadata
import tree

class Library:
    def __init__(self, json_path):
        self.json_path = json_path
        self.root_dir = os.path.dirname(os.path.abspath(self.json_path))
        with open(self.json_path, 'r', encoding='UTF-8') as f:
            spec = json.load(f)
        self.metadata = metadata.Metadata()
        for key in spec['keys']:
            self.metadata.add_key(**key)
        self.quick_filters = spec.get('quick_filters', {})
        self.normalise_images(spec['images'])
        self.base_tree = tree.BaseTree(self.root_dir, self.metadata, spec['images'])

    def all_images(self):
        return self.base_tree.leaves()

    def normalise_images(self, images):
        for spec in images:
            self.metadata.normalise_image_spec(spec)

    def scan_sets(self):
        sets = {}
        for image in self.base_tree.leaves():
            for key in self.metadata.keys:
                if not key.multi:
                    continue
                name = key.name
                sets[name] = sets.get(name, set()) | set(image.spec[name])
        return sets

    def save(self):
        spec = {
            'images': [image.spec for image in self.all_images()],
            'keys': self.metadata.json(),
            'quick_filters': self.quick_filters,
        }
        with open(self.json_path, 'w', encoding='UTF_8') as f:
            json.dump(spec, f, indent=4)

    def make_tree(self, filter_config):
        return tree.FilteredTree(self.base_tree, filter_config)
