import json
import os

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
    def __init__(self, library, config):
        super().__init__(library, 'root')
        self.config = config
        self.dirty = False


class Container(Node):
    def __init__(self, library, name, _type):
        super().__init__(library, name)
        self.type = _type
        self.is_set = self.type in library.sets
        self.type_label = self.type
        if self.is_set:
            assert self.type_label.endswith('s')
            self.type_label = self.type_label[:-1]


class Image(Node):
    type = 'image'
    type_label = 'image'
    is_set = False

    def __init__(self, library, spec):
        super().__init__(library, spec['name'])
        self.spec = spec
        self.abspath = os.path.join(library.root_dir, spec['path'])

    def delete_from_library(self):
        self.library.images.remove(self.spec)


class Library:
    _sort_types = {
        'default': None,
        'count': lambda c: -len(c.children),
        'alpha': lambda c: c.name,
    }

    _builtin_keys = [
        {'name': 'name', 'builtin': True},
        {'name': 'path', 'builtin': True},
        {'name': 'resolution', 'builtin': True},
    ]

    def __init__(self, json_path):
        self.json_path = json_path
        self.root_dir = os.path.dirname(os.path.abspath(self.json_path))
        with open(self.json_path, 'r', encoding='UTF-8') as f:
            spec = json.load(f)
        self.hierarchy = spec['hierarchy']
        self._custom_keys = spec['keys']
        self.images = []
        for image_spec in spec['images']:
            self.add_image(image_spec)
        self.scan_keys()
        self.tree = None

    def groupable_keys(self):
        return [key['name'] for key in self._custom_keys]

    def sort_types(self):
        return [k for k in self._sort_types.keys()]

    def metadata_keys(self):
        return self._builtin_keys + self._custom_keys

    def add_image(self, spec):
        all_keys = [key['name'] for key in self.metadata_keys()]
        spec = {key: spec[key] for key in spec if key in all_keys}
        for key in self._builtin_keys:
            if key['name'] not in spec:
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
        # has a non-default view config, since we don't want to generate an
        # incomplete or misordered image list.
        if self.tree and self.tree.dirty and self.tree.config.is_default():
            self.images = [image.spec for image in self.tree.leaves()]
            self.tree.dirty = False

    def save(self):
        self.refresh_images()
        spec = {
            'images': self.images,
            'hierarchy': self.hierarchy,
            'keys': self._custom_keys,
        }
        with open(self.json_path, 'w', encoding='UTF_8') as f:
            json.dump(spec, f, indent=4)

    def make_tree(self, config):
        self.refresh_images()
        filter_expr = config.filter
        self.tree = Root(self, config)
        child_map = {} # parent -> child_name -> child
        for image_spec in self.images:
            if filter_expr:
                tags = set()
                for key in self.sets:
                    if key in image_spec:
                        tags |= set(image_spec[key])
                if not filter_expr.matches(tags):
                    continue

            parents = [self.tree]
            for key in config.group_by:
                values = image_spec.get(key)
                if not isinstance(values, list):
                    values = [values]

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

        sort_keys = [self._sort_types.get(k) for k in config.order_by]
        nodes = [self.tree]
        for sort_key in sort_keys:
            if sort_key:
                for node in nodes:
                    node.children.sort(key=sort_key)
            nodes = [child for node in nodes for child in node.children]

        return self.tree
