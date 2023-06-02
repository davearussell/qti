import json
import os
import random

class Node:
    def __init__(self, library, name):
        self.library = library
        self.name = name
        self.parent = None
        self.children = []

    def add_child(self, child, index=None):
        child.parent = self
        if index is None:
            self.children.append(child)
        else:
            self.children.insert(index, child)
        return child

    @property
    def root(self):
        node = self
        while node.parent:
            node = node.parent
        return node

    @property
    def index(self):
        if self.parent:
            return self.parent.children.index(self)

    def ancestors(self, predicate=None):
        node = self
        while node:
            if predicate is None or predicate(node):
                yield node
            node = node.parent

    def descendants(self, predicate=None):
        if predicate is None or predicate(self):
            yield self
        for child in self.children:
            yield from child.descendants(predicate=predicate)

    def leaves(self):
        return self.descendants(lambda node: not node.children)


class Root(Node):
    type = 'root'
    def __init__(self, library, filter_config):
        super().__init__(library, 'root')
        self.filter_config = filter_config


class Container(Node):
    def __init__(self, library, name, _type):
        super().__init__(library, name)
        self.type = _type
        self.is_set = self.type in library.sets

    @property
    def type_label(self):
        if self.is_set and self.type.endswith('s'):
            return self.type[:-1]
        return self.type


class Image(Node):
    type = 'image'
    type_label = 'image'
    is_set = False

    def __init__(self, library, spec):
        super().__init__(library, spec['name'])
        self.spec = spec
        self.root_dir = spec['_root_dir']
        self.relpath = spec['path']
        self.abspath = os.path.join(self.root_dir, self.relpath)

    def delete_from_library(self):
        self.library.images.remove(self.spec)


class Library:
    _sort_types = {
        'default': None,
        'count': lambda c: -len(c.children),
        'alpha': lambda c: c.name,
        'random': lambda c: random.random(),
    }

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
        self.images = []
        for image_spec in spec['images']:
            self.add_image(image_spec)
        self.scan_keys()
        self.tree = None

    @property
    def hierarchy(self):
        return [ck['name'] for ck in self._custom_keys if ck.get('in_hierarchy')]

    def groupable_keys(self):
        return [key['name'] for key in self._custom_keys]

    def sort_types(self):
        return [k for k in self._sort_types.keys()]

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
        for image_spec in self.images:
            image_spec[new_name] = image_spec.pop(old_name)
        for l in [self.hierarchy, self.tree.filter_config.group_by]:
            if old_name in l:
                l[l.index(old_name)] = new_name
        for node in self.tree.descendants():
            if node.type == old_name:
                node.type = new_name

    def delete_key(self, name):
        print("delete_key", name)
        key = self.find_key(name)
        self._custom_keys.remove(key)
        # For simplicity, we don't bother to delete the key from every image
        # at this point. It will get deleted automatically on next app restart

    def new_key(self, name):
        print("new_key", name)
        self._custom_keys.append({'name': name})
        for image_spec in self.images:
            image_spec[name] = ''

    def reorder_keys(self, order):
        print("reorder_keys", order)
        keys = [self.find_key(name) for name in order]
        self._custom_keys = [key for key in keys if not key.get('builtin')]

    def set_key_multi(self, name, multi):
        print("set_key_multi", name, multi)
        key = self.find_key(name)
        assert multi != bool(key.get('multi')), key
        key['multi'] = multi
        for image_spec in self.images:
            if multi:
                image_spec[name] = image_spec[name].split()
            else:
                image_spec[name] = ' '.join(image_spec[name])

    def set_key_in_hierarchy(self, name, value):
        print("set_key_in_hierarchy", name, value)
        key = self.find_key(name)
        key['in_hierarchy'] = value

    def add_image(self, spec):
        all_keys = [key['name'] for key in self.metadata_keys()]
        spec = {key: spec[key] for key in spec if key in all_keys}
        spec['_root_dir'] = self.root_dir
        for key in self._builtin_keys:
            if key['name'] not in spec and not key['optional']:
                raise Exception("Missing required key '%s'" % (key,))
        for key in self._custom_keys:
            name, multi = key['name'], key.get('multi')
            default = [] if multi else ''
            if name not in spec:
                spec[name] = default
            elif type(spec[name]) != type(default):
                raise Exception("Bad value for key %r in %r" % (key, spec))
        self.images.append(spec)

    def scan_keys(self):
        self.sets = {}
        for image_spec in self.images:
            for key in self._custom_keys:
                if not key.get('multi'):
                    continue
                name = key['name']
                self.sets[name] = self.sets.get(name, set()) | set(image_spec[name])

    def refresh_images(self):
        # If the current tree has some reordered nodes, then regenerate our
        # image list to match the new ordering. The exception is if the tree
        # has a non-default filter config, since we don't want to generate an
        # incomplete or misordered image list.
        if self.tree and self.tree.filter_config.is_default():
            self.images = [image.spec for image in self.tree.leaves()]

    def save(self):
        images = [{k: v for k, v in spec.items() if not k.startswith('_')}
                  for spec in self.images]
        spec = {
            'images': images,
            'keys': self._custom_keys,
            'quick_filters': self.quick_filters,
        }
        with open(self.json_path, 'w', encoding='UTF_8') as f:
            json.dump(spec, f, indent=4)

    def make_tree(self, filter_config):
        filter_expr = filter_config.filter
        self.tree = Root(self, filter_config)
        child_map = {} # parent -> child_name -> child

        group_by = []
        for word in filter_config.group_by:
            if ':' in word:
                key, values_ = word.split(':')
                include_values = values_.split(',')
            else:
                key, include_values = word, None
            group_by.append((key, include_values))

        for image_spec in self.images:
            if filter_expr:
                tags = set()
                for key in self.sets:
                    if key in image_spec:
                        tags |= set(image_spec[key])
                if not filter_expr.matches(tags):
                    continue

            parents = [self.tree]
            for key, include_values in group_by:
                values = image_spec.get(key)
                if not isinstance(values, list):
                    values = [values]
                if include_values:
                    values = [value for value in values if value in include_values]

                new_parents = []
                for value in values:
                    if value is None:
                        value = ''
                    map_value = value
                    if key in self.hierarchy:
                        i = self.hierarchy.index(key) + 1
                        map_value = tuple(image_spec.get(k) for k in self.hierarchy[:i])
                    for parent in parents:
                        node = child_map.setdefault(parent, {}).get(map_value)
                        if node is None:
                            node = Container(self, value, key)
                            parent.add_child(node)
                            child_map[parent][map_value] = node
                        new_parents.append(node)
                parents = new_parents
            for parent in parents:
                parent.add_child(Image(self, image_spec))

        sort_keys = [self._sort_types.get(k) for k in filter_config.order_by]
        nodes = [self.tree]
        for sort_key in sort_keys:
            if sort_key:
                for node in nodes:
                    node.children.sort(key=sort_key)
            nodes = [child for node in nodes for child in node.children]

        return self.tree
