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


def only(seq):
    l = list(seq)
    if len(l) != 1:
        raise Exception("Expected 1 match, found %d" % (len(l),))
    return l[0]

def maybe(seq):
    l = list(seq)
    if len(l) > 1:
        raise Exception("Expected 0-1 matches, found %d" % (len(l),))
    return l[0] if l else None


class Node:
    type = None

    def __init__(self, name):
        self.name = name
        self.key = name
        self.parent = None
        self.children = []
        self.lut = {} # child.key -> child

    def add_child(self, child, index=None):
        child.parent = self
        if index is None:
            self.children.append(child)
        else:
            self.children.insert(index, child)
        assert child.key not in self.lut
        self.lut[child.key] = child
        return child

    def remove_child(self, child):
        assert self.lut.get(child.key) is child
        self.children.remove(child)
        del self.lut[child.key]

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

    def images(self):
        return self.descendants(lambda node: node.type == 'image')

    def delete(self):
        if self.parent is None:
            return

        self.parent.remove_child(self)
        if not self.parent.children:
            self.parent.delete()
        self.parent = None


class Root(Node):
    type = 'root'
    def __init__(self):
        super().__init__('root')


class Container(Node):
    def __init__(self, name, _type):
        super().__init__(name)
        self.type = _type

    @property
    def type_label(self):
        return self.type


class Image(Node):
    type = 'image'
    type_label = 'image'

    def __init__(self, spec, root_dir):
        super().__init__(spec['name'])
        self.spec = spec
        self.root_dir = root_dir
        self.abspath = os.path.join(root_dir, spec['path'])
        self._cache_tmpl = os.path.join(root_dir, '.cache', '%dx%d', spec['path'])
        self.base_node = self
        self.key = self.abspath

    def make_lut_key(self, key):
        hierarchy = self.root.metadata.hierarchy()
        try:
            j = hierarchy.index(key)
        except ValueError:
            return self.spec[key]
        return tuple(self.spec.get(k) for i, k in enumerate(hierarchy) if i <= j)

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

    def update_set(self, key, add, remove):
        old = self.spec[key]
        self.spec[key] = [x for x in old if x not in remove] + [x for x in add if x not in old]


class BaseTree(Root):
    def __init__(self, root_dir, metadata, images):
        super().__init__()
        self.root_dir = root_dir
        self.metadata = metadata
        self.populate(images)

    def insert_images(self, images):
        hierarchy = self.metadata.hierarchy()
        for image in images:
            parent = self
            for key in hierarchy:
                value = image.spec.get(key) or ''
                node = parent.lut.get(value)
                if node is None:
                    node = Container(value, key)
                    parent.add_child(node)
                parent = node
            parent.add_child(image)

    def images(self):
        return self.descendants(lambda node: node.type == 'image')

    def populate(self, image_specs):
        images = []
        for image_spec in image_specs:
            self.metadata.normalise_image_spec(image_spec)
            images.append(Image(image_spec, self.root_dir))
        self.insert_images(images)

    def move_images(self, images, key, value):
        ancestor = only(images[0].ancestors(lambda n: n.type == key))
        parent = ancestor.parent
        new_ancestor = maybe(node for node in parent.children if node.name == value)
        if new_ancestor is None:
            new_ancestor = Container(value, key)
            parent.add_child(new_ancestor, index=parent.children.index(ancestor) + 1)
        for image in images:
            image.delete()
        self.insert_images(images)

    def add_key(self, key, value):
        for image in self.images():
            image.spec[key] = value

    def rename_key(self, old_name, new_name):
        for node in self.descendants():
            if node.type == 'image':
                node.spec[new_name] = node.spec.pop(old_name)
            elif node.type == old_name:
                node.type = new_name

    def set_key_multi(self, key, is_multi):
        for image in self.images():
            if is_multi:
                image.spec[key] = image.spec[key].split()
            else:
                image.spec[key] = ' '.join(image.spec[key])


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

    def update(self, key, value):
        if key == 'name':
            key = self.type
        images = [image.base_node for image in self.images()]
        for image in images:
            image.spec[key] = value
        base_tree = self.root.base_node
        if key in base_tree.metadata.hierarchy():
            base_tree.move_images(images, key, value)

    def update_set(self, key, add, remove):
        for image in self.images():
            image.base_node.update_set(key, add, remove)

    def get_key(self, key):
        if key == 'name':
            return self.name

        multi = key in self.root.base_node.metadata.multi_value_keys()
        if multi:
            values = None
            varying = False
            for image in self.images():
                if values is None:
                    values = image.spec[key].copy()
                elif sorted(values) != sorted(image.spec[key]):
                    varying = True
                    values = [value for value in values if value in image.spec[key]]
            if varying:
                values.insert(0, '...')
            return values
        else:
            values = {image.get_key(key) for image in self.images()}
            return values.pop() if len(values) == 1 else '...'


class FilteredSet(FilteredContainer):
    def __init__(self, name, _type):
        super().__init__(name, _type, None)

    @property
    def type_label(self):
        if self.type.endswith('s'):
            return self.type[:-1]
        return self.type

    def update(self, key, value):
        assert key == 'name', key
        for image in self.images():
            values = image.base_node.spec[self.type]
            values[values.index(self.name)] = value


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

    def update(self, key, value):
        self.base_node.spec[key] = value
        base_tree = self.base_node.root
        if key in base_tree.metadata.hierarchy():
            base_tree.move_images([self.base_node], key, value)

    def update_set(self, key, add, remove):
        self.base_node.update_set(key, add, remove)

    def get_key(self, key):
        return self.spec[key]


class FilteredTree(Root):
    def __init__(self, base_tree, filter_config):
        super().__init__()
        self.base_node = base_tree
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
        hierarchy = self.base_node.metadata.hierarchy()
        filter_expr = self.filter_config.filter
        for image in self.base_node.images():
            if filter_expr and not filter_expr.matches(image.all_tags()):
                continue

            parents = [self]
            for key, include_values in self.group_by:
                values = image.spec.get(key)
                is_set = isinstance(values, list)
                if not is_set:
                    values = [values]
                if not values:
                    values = ['(none)']
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
                        lut_key = image.make_lut_key(key)
                    else:
                        base_node = None
                        lut_key = value
                    for parent in parents:
                        node = parent.lut.get(lut_key)
                        if node is None:
                            if is_set:
                                node = FilteredSet(value, key)
                            else:
                                node = FilteredContainer(value, key, base_node)
                            node.key = lut_key
                            parent.add_child(node)
                        new_parents.append(node)
                parents = new_parents

            copies = {FilteredImage(image) for _ in parents}
            for parent, child in zip(parents, copies):
                child.aliases = copies - {child}
                parent.add_child(child)

        sort_keys = [SORT_TYPES.get(k) for k in self.filter_config.order_by]
        nodes = [self]
        for sort_key in sort_keys:
            if sort_key:
                for node in nodes:
                    node.children.sort(key=sort_key)
            nodes = [child for node in nodes for child in node.children]

    def add_key(self, key, value):
        self.base_node.add_key(key, value)

    def rename_key(self, old_name, new_name):
        self.base_node.rename_key(old_name, new_name)
        for node in self.descendants():
            if node.type == old_name:
                node.type = new_name

    def set_key_multi(self, key, is_multi):
        self.base_node.set_key_multi(key, is_multi)
