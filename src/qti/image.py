from PIL import Image


def image_resolution(image_path):
    return Image.open(image_path).size
