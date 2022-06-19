import json
import os

class Node:
    def __init__(self, library, name):
        self.library = library
        self.root_dir = library.root_dir
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


class Container(Node):
    def __init__(self, library, name, _type):
        super().__init__(library, name)
        self.type = _type


class Image(Node):
    type = 'image'

    def __init__(self, library, spec):
        super().__init__(library, spec['name'])
        self.spec = spec
        self.abspath = os.path.join(self.root_dir, spec['path'])


class Library:
    def __init__(self, json_path):
        self.json_path = json_path
        self.root_dir = os.path.dirname(self.json_path)
        with open(self.json_path, 'r', encoding='UTF-8') as f:
            spec = json.load(f)
        self.images = spec['images']
        self.default_group_by = spec['group_by']

    def make_tree(self):
        root = Container(self, 'root', 'root')
        for image_spec in self.images:
            parents = [root]

            for key in self.default_group_by:
                values = image_spec.get(key)
                if not isinstance(values, list):
                    values = [values]

                new_parents = []
                for value in values:
                    for parent in parents:
                        matches = [child for child in parent.children if child.name == value]
                        if matches:
                            assert len(matches) == 1
                            parent = matches[0]
                        else:
                            parent = parent.add_child(Container(self, value, key))
                        new_parents.append(parent)
                parents = new_parents
            for parent in parents:
                parent.add_child(Image(self, image_spec))
        return root
