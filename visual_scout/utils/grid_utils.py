from math import ceil, sqrt
import cv2
import os
import numpy as np
from datetime import timedelta
import warnings
import shutil
from PIL import Image, UnidentifiedImageError


def create_grid(images, frame_width, frame_height, grid_dimension):
    """
    Create a square grid image from a list of images, arranged left-to-right, top-to-bottom.

    The grid will be no larger than `grid_dimension` x `grid_dimension`, and will automatically
    shrink to the smallest square that can fit all images. If the number of images is less than
    `grid_dimension^2`, empty grid cells will be left blank (white).

    Args:
        images (list of PIL.Image): List of PIL Image objects to arrange in the grid.
        frame_width (int): Width of each individual image in the grid.
        frame_height (int): Height of each individual image in the grid.
        grid_dimension (int): Maximum number of rows and columns in the grid.

    Returns:
        PIL.Image: A composite image with the input images arranged in a square grid.
                   Empty slots are filled with white.
                   If `images` is empty, returns a single blank image of size (frame_width, frame_height).
    """
    num_images = len(images)

    # handle the case where there are no images
    if num_images == 0:
        return Image.new(
            "RGB", (frame_width, frame_height), "white"
        )  # Return 1x1 blank image

    # compute minimum square grid needed
    raw_grid_size = ceil(sqrt(num_images))
    optimal_grid_dim = min(grid_dimension, raw_grid_size)

    # create a blank (white) grid
    grid_size = (optimal_grid_dim * frame_width, optimal_grid_dim * frame_height)
    grid = Image.new("RGB", grid_size, "white")

    # arrange images in the grid
    for idx, img in enumerate(images):
        row, col = divmod(idx, optimal_grid_dim)
        x, y = col * frame_width, row * frame_height
        grid.paste(img, (x, y))

    return grid

def save_grid(grid, output_directory, start_timestamp, end_timestamp):
    """
    Save a grid image to the specified directory using a timestamp-based filename.

    The filename will follow the format: 'grid_<start_timestamp>_<end_timestamp>.jpg'.

    Args:
        grid (PIL.Image): The grid image to be saved.
        output_directory (str): Directory where the image will be saved. Created if it doesn't exist.
        start_timestamp (str): Start timestamp used in the filename.
        end_timestamp (str): End timestamp used in the filename.

    Returns:
        None. The image is saved to disk, and a confirmation message is printed.
    """
    os.makedirs(output_directory, exist_ok=True)
    output_filename = f"grid_{start_timestamp}_{end_timestamp}.jpg"
    output_path = os.path.join(output_directory, output_filename)
    grid.save(output_path)
    print(f"Saved grid in: {output_directory}/{output_filename}")
    return output_path