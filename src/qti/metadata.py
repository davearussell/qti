import copy

class Unspecified: pass

class MetadataKey:
    def __init__(self, name, builtin=False, required=False,
                 default=Unspecified, _type=None, in_hierarchy=False, multi=False):
        self.name = name
        self.builtin = builtin
        self.groupable = not builtin
        self.required = required
        self.type = _type
        if self.type is None:
            self.type = list if multi else str
        self.default = self.type() if default is Unspecified else default
        self.in_hierarchy = in_hierarchy
        self.multi = multi

    def copy(self):
        return type(self)(name=self.name, builtin=self.builtin, required=self.required,
                          default=copy.deepcopy(self.default), _type=self.type,
                          in_hierarchy=self.in_hierarchy, multi=self.multi)

    def json(self):
        return {k: getattr(self, k) for k in ['name', 'in_hierarchy', 'multi']}


BUILTIN_KEYS = [
    {'name': 'name', 'required': True},
    {'name': 'path', 'required': True},
    {'name': 'resolution', 'required': True, '_type': list},
]

class Metadata:
    def __init__(self):
        self.keys = []
        self.lut = {}
        for key in BUILTIN_KEYS:
            self.add_key(builtin=True, **key)

    def copy(self):
        new = type(self)()
        new.keys = [key.copy() for key in self.keys]
        new.lut = {key.name: key for key in new.keys}
        return new

    def add_key(self, name, **kwargs):
        assert name not in self.lut
        key = MetadataKey(name, **kwargs)
        self.keys.append(key)
        self.lut[name] = key

    def delete_key(self, name):
        assert name in self.lut
        self.keys.remove(self.lut.pop(name))

    def rename_key(self, old_name, new_name):
        assert old_name in self.lut and new_name not in self.lut
        key = self.lut[new_name] = self.lut.pop(old_name)
        key.name = new_name

    def hierarchy(self):
        return [key.name for key in self.keys if key.in_hierarchy]

    def groupable_keys(self):
        return [key.name for key in self.keys if key.groupable]

    def multi_value_keys(self):
        return [key.name for key in self.keys if key.multi]

    def editable_keys(self):
        return [key.name for key in self.keys if not key.builtin]

    def json(self):
        return [key.json() for key in self.keys if not key.builtin]

    def normalise_image_spec(self, spec):
        for key in [key for key in spec if key not in {key.name for key in self.keys}]:
            del spec[key]
        for key in self.keys:
            if key.name not in spec:
                if key.required:
                    raise Exception("Missing required key '%s'" % (key.name,))
                elif key.default is not None:
                    spec[key.name] = key.default
            elif not isinstance(spec[key.name], key.type):
                raise Exception("Bad value for key %r in %r" % (key.name, spec))
