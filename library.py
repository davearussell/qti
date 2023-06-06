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

    def find_key(self, name):
        matches = [key for key in self.metadata_keys() if key['name'] == name]
        assert len(matches) == 1, (name, self.metadata_keys())
        return matches[0]

    def rename_key(self, old_name, new_name):
        print("rename_key", old_name, new_name)
        key = self.find_key(old_name)
        key['name'] = new_name
        for image in self.all_images():
            image.spec[new_name] = image.spec.pop(old_name)
        if old_name in self.sets:
            self.sets[new_name] = self.sets.pop(old_name)

    def delete_key(self, name):
        print("delete_key", name)
        key = self.find_key(name)
        self._custom_keys.remove(key)
        # For simplicity, we don't bother to delete the key from every image
        # at this point. It will get deleted automatically on next app restart

    def new_key(self, name):
        print("new_key", name)
        self._custom_keys.append({'name': name})
        for image in self.all_images():
            image.spec[name] = ''

    def reorder_keys(self, order):
        print("reorder_keys", order)
        keys = [self.find_key(name) for name in order]
        self._custom_keys = [key for key in keys if not key.get('builtin')]

    def set_key_multi(self, name, multi):
        print("set_key_multi", name, multi)
        key = self.find_key(name)
        assert multi != bool(key.get('multi')), key
        key['multi'] = multi
        for image in self.all_images():
            if multi:
                image.spec[name] = image.spec[name].split()
            else:
                image.spec[name] = ' '.join(image.spec[name])

    def set_key_in_hierarchy(self, name, value):
        print("set_key_in_hierarchy", name, value)
        key = self.find_key(name)
        key['in_hierarchy'] = value

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
