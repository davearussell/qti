import PIL


class Image:
    def __init__(self, path_or_image):
        if isinstance(path_or_image, str):
            self.size = PIL.Image.open(path_or_image).size
            self._path = path_or_image
            self._image = None
        else:
            self._image = path_or_image
            self.size = self.get_size()

    @property
    def image(self):
        if self._image is None:
            self._image = self.load(self._path)
        return self._image

    def load(self, path):
        raise NotImplementedError()

    def get_size(self):
        raise NotImplementedError()

    def scale(self, size):
        raise NotImplementedError()

    def crop_and_pan(self, size, x, y, background_color=None):
        raise NotImplementedError()

    def center(self, size, **kwargs):
        w, h = size
        iw, ih = self.size
        return self.crop_and_pan(size, (w - iw) // 2, (h - ih) // 2, **kwargs)
