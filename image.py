import os
from qt.image import load_image, save_image, scale_image


def copy_and_scale(image_path, scaled_path, size):
    image = load_image(image_path, for_display=False)
    scaled = scale_image(image, size)
    if not os.path.isdir(os.path.dirname(scaled_path)):
        os.makedirs(os.path.dirname(scaled_path))
    save_image(scaled, scaled_path)
