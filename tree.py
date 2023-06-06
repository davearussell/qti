import os
import random

import cache


class TreeError(Exception): pass


SORT_TYPES = {
    'default': None,
    'count': lambda c: -len(c.children),
    'alpha': lambda c: c.name,
    'random': lambda c: random.random(),
}


class Node:
    def __init__(self, name):
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

    def swap_with(self, other):
        if self.parent != other.parent:
            raise TreeError("Nodes do not share a parent")
        siblings = self.parent.children
        ia = self.index
        ib = other.index
        siblings[ia], siblings[ib] = siblings[ib], siblings[ia]

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

    def delete(self):
        parent = self.parent
        parent.children.remove(self)
        while parent.parent and not parent.children:
            parent.parent.children.remove(parent)
            parent = parent.parent


class Root(Node):
    type = 'root'
    def __init__(self):
        super().__init__('root')


class Container(Node):
    def __init__(self, name, _type):
        super().__init__(name)
        self.type = _type
        self.type_label = _type

    def delete(self, from_disk=False):
        if from_disk:
            for image in self.leaves():
                image.delete_file()
        super().delete()


class Image(Node):
    type = 'image'
    type_label = 'image'

    def __init__(self, spec, root_dir):
        super().__init__(spec['name'])
        self.spec = spec
        self.root_dir = root_dir
        self.abspath = os.path.join(root_dir, spec['path'])
        self._cache_tmpl = os.path.join(root_dir, '.cache', '%dx%d', spec['path'])

    def all_tags(self):
        keys = self.root.metadata.multi_value_keys()
        return {value for key in keys for value in self.spec[key]}

    def cache_path(self, size):
        return self._cache_tmpl % size.toTuple()

    def load_pixmap(self, size):
        return cache.load_pixmap(self.abspath, self.cache_path(size), size)

    def delete_file(self):
        if os.path.exists(self.abspath):
            print("Deleting", self.abspath)
            os.unlink(self.abspath)

    def delete(self, from_disk=False):
        if from_disk:
            self.delete_file()
        super().delete()


class BaseTree(Root):
    def __init__(self, root_dir, metadata, images):
        super().__init__()
        self.root_dir = root_dir
        self.metadata = metadata
        self.populate(images)

    def populate(self, images):
        hierarchy = self.metadata.hierarchy()
        lut = {}
        for image_spec in images:
            parent = self
            for key in hierarchy:
                value = image_spec.get(key) or ''
                node = lut.get((parent, value))
                if node is None:
                    node = Container(value, key)
                    lut[(parent, value)] = node
                    parent.add_child(node)
                parent = node
            parent.add_child(Image(image_spec, self.root_dir))


class FilteredContainer(Container):
    def __init__(self, name, _type, base_node):
        super().__init__(name, _type)
        self.base_node = base_node

    def swap_with(self, other):
        bs, bo = self.base_node, other.base_node
        if bs is None or bo is None:
            raise TreeError("Nodes do not map onto base tree")
        bs.swap_with(bo)
        super().swap_with(other)

    def delete(self, from_disk=False, preserve_base=False):
        if not preserve_base:
            for leaf in self.leaves():
                leaf.base_node.delete(from_disk=from_disk)
        super().delete()


class FilteredSet(FilteredContainer):
    def __init__(self, name, _type):
        super().__init__(name, _type, None)
        self.type_label = self.singularise(self.type_label)

    def singularise(self, text):
        if text.endswith('s'):
            return text[:-1]
        return text

    def delete(self, from_disk=False, preserve_images=False):
        if preserve_images:
            assert not from_disk
            for node in self.leaves():
                node.spec[self.type].remove(self.name)
            super().delete(preserve_base=True)
        else:
            super().delete(from_disk=from_disk)


class FilteredImage(Image):
    def __init__(self, image):
        super().__init__(image.spec, image.root_dir)
        self.base_node = image

    def swap_with(self, other):
        bs, bo = self.base_node, other.base_node
        if bs is None or bo is None:
            raise TreeError("Nodes do not map onto base tree")
        bs.swap_with(bo)
        super().swap_with(other)

    def delete(self, from_disk=False):
        self.base_node.delete(from_disk=from_disk)
        super().delete()


class FilteredTree(Root):
    def __init__(self, base_tree, filter_config):
        super().__init__()
        self.base_tree = base_tree
        self.filter_config = filter_config
        self.group_by = []
        for word in filter_config.group_by:
            if ':' in word:
                key, values_ = word.split(':')
                include_values = values_.split(',')
            else:
                key, include_values = word, None
            self.group_by.append((key, include_values))
        self.populate()

    def populate(self):
        lut = {}
        hierarchy = self.base_tree.metadata.hierarchy()
        filter_expr = self.filter_config.filter
        for image in self.base_tree.leaves():
            if filter_expr and not filter_expr.matches(image.all_tags()):
                continue

            parents = [self]
            for key, include_values in self.group_by:
                values = image.spec.get(key)
                is_set = isinstance(values, list)
                if not is_set:
                    values = [values]
                if include_values:
                    values = [value for value in values if value in include_values]

                new_parents = []
                for value in values:
                    if value is None:
                        value = ''
                    if key in hierarchy:
                        base_node = image.parent
                        while base_node.type != key:
                            base_node = base_node.parent
                        lut_key = (base_node, value)
                    else:
                        base_node = None
                        lut_key = value
                    for parent in parents:
                        node = lut.get((parent, lut_key))
                        if node is None:
                            if is_set:
                                node = FilteredSet(value, key)
                            else:
                                node = FilteredContainer(value, key, base_node)
                            parent.add_child(node)
                            lut[(parent, lut_key)] = node
                        new_parents.append(node)
                parents = new_parents
            for parent in parents:
                parent.add_child(FilteredImage(image))

        sort_keys = [SORT_TYPES.get(k) for k in self.filter_config.order_by]
        nodes = [self]
        for sort_key in sort_keys:
            if sort_key:
                for node in nodes:
                    node.children.sort(key=sort_key)
            nodes = [child for node in nodes for child in node.children]
