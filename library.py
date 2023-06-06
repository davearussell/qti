import json
import os

import tree

class Library:
    _builtin_keys = [
        {'name': 'name', 'builtin': True},
        {'name': 'path', 'builtin': True},
        {'name': 'resolution', 'builtin': True},
        {'name': 'zoom', 'builtin': True, 'optional': True},
        {'name': 'pan', 'builtin': True, 'optional': True},
    ]

    def __init__(self, json_path):
        self.json_path = json_path
        self.root_dir = os.path.dirname(os.path.abspath(self.json_path))
        with open(self.json_path, 'r', encoding='UTF-8') as f:
            spec = json.load(f)
        self._custom_keys = spec['keys']
        self.quick_filters = spec.get('quick_filters', {})
        self.sanitise_images(spec['images'])
        self.base_tree = tree.BaseTree(self.root_dir, self.hierarchy, spec['images'])
        self.scan_keys()

    def all_images(self):
        return self.base_tree.leaves()

    @property
    def hierarchy(self):
        return [ck['name'] for ck in self._custom_keys if ck.get('in_hierarchy')]

    def groupable_keys(self):
        return [key['name'] for key in self._custom_keys]

    def metadata_keys(self):
        return self._builtin_keys + self._custom_keys

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

    def sanitise_images(self, images):
        all_keys = [key['name'] for key in self.metadata_keys()]
        for spec in images:
            for key in list(spec.keys()):
                if key not in all_keys:
                    del spec[key]
            for key in self._builtin_keys:
                if key['name'] not in spec and not key['optional']:
                    raise Exception("Missing required key '%s'" % (key,))
            spec['resolution'] = tuple(spec['resolution'])
            for key in self._custom_keys:
                name, multi = key['name'], key.get('multi')
                default = [] if multi else ''
                if name not in spec:
                    spec[name] = default
                elif type(spec[name]) != type(default):
                    raise Exception("Bad value for key %r in %r" % (key, spec))

    def scan_keys(self):
        self.sets = {}
        for image in self.base_tree.leaves():
            for key in self._custom_keys:
                if not key.get('multi'):
                    continue
                name = key['name']
                self.sets[name] = self.sets.get(name, set()) | set(image.spec[name])

    def save(self):
        spec = {
            'images': [image.spec for image in self.all_images()],
            'keys': self._custom_keys,
            'quick_filters': self.quick_filters,
        }
        with open(self.json_path, 'w', encoding='UTF_8') as f:
            json.dump(spec, f, indent=4)

    def make_tree(self, filter_config):
        return tree.FilteredTree(self.base_tree, filter_config)
