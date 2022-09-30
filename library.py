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
    sort_types = {
        'default': None,
        'count': lambda c: -len(c.children),
        'alpha': lambda c: c.name,
    }
    builtin_keys = ['name', 'path', 'resolution']

    def __init__(self, json_path):
        self.json_path = json_path
        self.root_dir = os.path.dirname(os.path.abspath(self.json_path))
        with open(self.json_path, 'r', encoding='UTF-8') as f:
            spec = json.load(f)
        self.images = spec['images']
        self.default_group_by = spec['group_by']
        self.key_types = spec['key_types']
        self.custom_keys = list(self.key_types.keys())
        self.scan_keys()
        self.tree = None

    def default_value(self, key):
        if key in self.builtin_keys:
            return None
        defaults = {
            'set': [],
            'str': '',
        }
        return defaults[self.key_types[key]]

    def scan_keys(self):
        self.sets = {}
        for image_spec in self.images:
            for key, value in image_spec.items():
                if key in self.builtin_keys:
                    continue
                if isinstance(value, list):
                    self.sets[key] = self.sets.get(key, set()) | set(value)

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
            'group_by': self.default_group_by,
            'key_types': self.key_types,
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
                    if key in self.default_group_by:
                        i = self.default_group_by.index(key) + 1
                        map_value = tuple(image_spec.get(k) for k in self.default_group_by[:i])
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

        sort_keys = [self.sort_types.get(k) for k in config.order_by]
        nodes = [self.tree]
        for sort_key in sort_keys:
            if sort_key:
                for node in nodes:
                    node.children.sort(key=sort_key)
            nodes = [child for node in nodes for child in node.children]

        return self.tree
