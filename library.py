import json
import os

import metadata
import tree

class Library:
    def __init__(self, json_path):
        self.json_path = json_path
        self.root_dir = os.path.dirname(os.path.abspath(self.json_path))
        if os.path.exists(self.json_path):
            with open(self.json_path, 'r', encoding='UTF-8') as f:
                spec = json.load(f)
        else:
            spec = {'keys': [], 'images': []}
        self.metadata = metadata.Metadata()
        for key in spec['keys']:
            self.metadata.add_key(**key)
        self.quick_filters = spec.get('quick_filters', {})
        self.quick_actions = spec.get('quick_actions', {})
        self.base_tree = tree.BaseTree(self.root_dir, self.metadata, spec['images'])

    def images(self):
        return self.base_tree.images()

    def values_by_key(self):
        all_values = {}
        for image in self.images():
            for key in self.metadata.keys:
                if key.builtin:
                    continue
                key_values = all_values.setdefault(key.name, set())
                if key.multi:
                    key_values |= set(image.spec[key.name])
                else:
                    key_values.add(image.spec[key.name])
        return all_values

    def save(self):
        spec = {
            'images': [image.spec for image in self.images()],
            'keys': self.metadata.json(),
            'quick_filters': self.quick_filters,
            'quick_actions': self.quick_actions,
        }
        with open(self.json_path, 'w', encoding='UTF_8') as f:
            json.dump(spec, f, indent=4)

    def make_tree(self, filter_config):
        return tree.FilteredTree(self.base_tree, filter_config)
