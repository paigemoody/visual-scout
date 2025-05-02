import cv2
import os
import numpy as np
from datetime import timedelta
import warnings
import shutil
from PIL import Image, UnidentifiedImageError
from visual_scout.constants import SAMPLING_INTERVAL


def get_file_type_from_extension(media_file):
    # Determine if input is a video, animated GIF, or static image
    video_extensions = {".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv"}
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
    gif_extensions = {".gif"}
    extension = os.path.splitext(media_file)[1].lower()

    if extension in video_extensions:
        return "video"
    elif extension in image_extensions:
        return "image"
    elif extension in gif_extensions:
        return "gif"
    else:
        raise ValueError(f"Unsupported file type: {media_file}")


def get_valid_media_files(full_path_input_dir):
    """
    Scans a directory for valid video and image files and returns a list of their full paths.

    This function checks if the specified input directory exists and scans for files
    with common video (`.mp4`, `.avi`, `.mov`, `.mkv`, `.flv`, `.wmv`) and image
    (`.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`, `.webp`) extensions.
    It prints validation details and filters out non-media files.

    Args:
        full_path_input_dir (str): The absolute path to the input directory containing media files.

    Returns:
        list: A list of full paths to detected media files.
        None: If no valid media files are found.

    Raises:
        FileNotFoundError: If the input directory does not exist.

    Workflow:
        1. Checks if the input directory exists.
        2. Iterates through all files in the directory and filters files based on valid media extensions.
        3. Returns a list of full paths for valid media files.

    Notes:
        - Only filters based on file extensions; deeper validation (e.g., corrupt files) happens later.
    """

    # Validate files in input dir
    print(f"\n\nValidating files in {full_path_input_dir}...")

    # Ensure the input dir exists
    if not os.path.exists(full_path_input_dir):
        raise FileNotFoundError(f"Input directory {full_path_input_dir} not found.")

    # Define valid extensions
    video_extensions = {".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv"}
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
    gif_extension = {".gif"}
    valid_extensions = video_extensions | image_extensions | gif_extension

    media_files = []
    all_files = os.listdir(full_path_input_dir)
    print(f"\n\nTotal input files: {len(all_files)}\n")

    for f in all_files:
        extension = os.path.splitext(f)[1].lower()
        if extension in valid_extensions:
            media_file_full_path = os.path.join(full_path_input_dir, f)
            media_files.append(media_file_full_path)
        else:
            print(f"Non-media file to be ignored: {f}")

    if not media_files:
        print("No media files found in the directory.")
        return

    print(f"\nTotal input media files {len(media_files)} \n\nStarting processing...")
    return media_files

def format_timestamps(timestamp, interval=SAMPLING_INTERVAL):
    """
    Format a numeric timestamp (in seconds) and interval into human-readable start and end times.

    Args:
        timestamp (float): The starting time in seconds.
        interval (int): Duration of the sampling interval in seconds.

    Returns:
        tuple: (start_time_str, end_time_str), both in HH:MM:SS format
    """
    start_time = str(timedelta(seconds=int(timestamp)))
    end_time = str(timedelta(seconds=int(timestamp + interval)))
    return start_time, end_time
