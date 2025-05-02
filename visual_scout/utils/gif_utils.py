import cv2
import os
import numpy as np
from datetime import timedelta
import warnings
import shutil
from PIL import Image, UnidentifiedImageError


def open_gif(gif_full_path):
    """
    Opens a GIF image file using PIL (Pillow).

    Args:
        gif_full_path (str): Full path to the GIF file.

    Returns:
        Image.Image: A PIL Image object if the file is successfully opened.
        None: If the file cannot be opened.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.exists(gif_full_path):
        raise FileNotFoundError(f"Image file not found: {gif_full_path}")

    try:
        gif = Image.open(gif_full_path)
        gif.verify()  # ensure the file is not corrupted
        return Image.open(gif_full_path)  # reopen because verify() closes the file
    except (UnidentifiedImageError, OSError) as e:
        warnings.warn(
            f"Unable to open GIF file: {gif_full_path}. Skipping... Error: {e}"
        )
        return None


def format_gif_timestamp(frame_index):
    """Returns identical start/end timestamps for a given GIF frame index."""
    timestamp = f"{frame_index:02}"
    return f"00:00:{timestamp}", f"00:00:{timestamp}"
