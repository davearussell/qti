import json
from pathlib import Path

class Datastore:
    def __init__(self):
        self.path = Path('~/.config/davesoft/qti.json').expanduser()
        if self.path.exists():
            self._data = json.load(open(self.path))
        else:
            self._data = {}

    def save(self):
        if not self.path.parent.exists():
            self.path.parent.mkdir(parents=True)
        with open(self.path, 'w') as f:
            json.dump(self._data, f, indent=4)

    def contains(self, key):
        return key in self._data

    def get(self, key):
        return self._data.get(key)

    def set(self, key, value):
        if value is None:
            self._data.pop(key, None)
        else:
            self._data[key] = str(value)
        self.save()

    def remove(self, key):
        self._data.pop(key, None)
        self.save()

    def keys(self):
        return self._data.keys()
