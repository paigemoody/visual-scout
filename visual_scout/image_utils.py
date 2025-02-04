import os
import re
import base64
import sys

# Regex for filenames with timestamps (e.g., grid_0-00-00_0-00-18.jpg)
TIMESTAMP_PATTERN = re.compile(r'(\d{1,2}-\d{2}-\d{2})_(\d{1,2}-\d{2}-\d{2})')


def encode_image_to_base64(image_path):
    """Convert an image to a base64-encoded string."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except FileNotFoundError:
        print(f"❌ Error: Image file not found at {image_path}")
        return None


def extract_timestamps(filename):
    """
    Extract start and end timestamps from a filename if it follows the pattern `hh-mm-ss_hh-mm-ss`.
    Returns None if no timestamps are found.
    """
    match = TIMESTAMP_PATTERN.search(filename)
    return match.groups() if match else None


def validate_filenames(input_dir):
    """
    Ensure all images in `input_dir` follow the timestamped filename format.
    If any files are invalid, print errors and exit.
    """
    invalid_files = []

    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png")) and not extract_timestamps(file):
                invalid_files.append(os.path.join(root, file))

    if invalid_files:
        print("\n❌ ERROR: The following files do not have a valid timestamp format:")
        for invalid in invalid_files:
            print(f"   - {invalid}")
        print("\n✅ Expected format: 'grid_hh-mm-ss_hh-mm-ss.jpg'")
        sys.exit(1)
