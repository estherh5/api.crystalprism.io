# -*- coding: utf-8 -*-

from io import BytesIO

from PIL import Image


def average_hash(image_data):
    # Generate the 16-character average hash that serves as a drawing's id.
    #
    # The image is normalised to RGBA before it is resized because Pillow
    # silently ignores the resampling filter for palette (mode P) images and
    # then converts them to grayscale through the palette, which shifts pixel
    # values by a step or two between Pillow releases and flips a hash bit.
    # Normalising first makes the hash depend on the pixels alone. RGBA input
    # is unaffected -- it is all the canvas toDataURL emits -- so drawing ids
    # minted before this normalisation stay valid.
    drawing = Image.open(BytesIO(image_data))

    if drawing.mode != 'RGBA':
        drawing = drawing.convert('RGBA')

    # Reduce drawing size and convert it to grayscale to assess drawing
    # uniqueness
    drawing_small = drawing.resize(
        (8, 8), Image.Resampling.LANCZOS).convert('L')

    # Get average pixel value of small drawing
    pixels = list(drawing_small.getdata())
    average_pixels = sum(pixels) / len(pixels)

    # Generate bit string by comparing each pixel in the small drawing to the
    # average pixel value
    bit_string = "".join(map(
        lambda pixel: '1' if pixel < average_pixels else '0', pixels))

    # Return unique id for drawing by converting bit string to hexadecimal
    return int(bit_string, 2).__format__('016x')
