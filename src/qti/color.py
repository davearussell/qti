from colour import Color as CColor

def to_rgb(name):
    return [round(v * 255) for v in CColor(name).rgb]

# We inherit from str for convenience: it allows us to pass Color objects directly
# into most backend APIs without first translating into a backend-specific object
class Color(str):
    def __init__(self, name):
        if len(name) == 4 and name.startswith('#'):
            # Not all APIs accept these (in particular pygame does not)
            raise ValueError("short-form hexcodes not accepted")
        self.name = str(name)
        self.rgb = to_rgb(self.name)
        self.r, self.g, self.b = self.rgb

    @classmethod
    def from_rgb(cls, rgb):
        r, g, b = rgb
        return cls('#%02x%02x%02x' % (r, g, b))

    def __str__(self):
        return self.name

    def contrasting(self):
        return self.from_rgb([255 if x < 128 else 0 for x in self.rgb])

    def fade(self, to='black', level=0.5):
        if isinstance(to, str):
            to = type(self)(to)
        return self.from_rgb([int(o * level + s * (1 - level))
                              for o, s in zip(to.rgb, self.rgb)])
