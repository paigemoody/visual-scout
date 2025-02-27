import cv2
import os
import math
import re
from datetime import timedelta


def inspect_video(video_file):
    """
    Inspects a video file and prints its key properties.

    Retrieves and displays essential metadata of a video file, 
    including its frames per second (FPS), total frame count, and duration. 
    It helps diagnose potential issues related to frame extraction and 
    ensures the video is accessible.

    Args:
        video_file (str): Path to the video file to inspect.

    Raises:
        FileNotFoundError: If the specified video file does not exist.
        IOError: If the video file cannot be opened.

    Prints:
        - Video file name.
        - Frames per second (FPS).
        - Total number of frames.
        - Video duration in HH:MM:SS format.

    Example:
        inspect_video("visual_scout/example_videos/example_video_horizontal.mov")

    Output Example:
        ```
        Video File: sample_video.mp4
        Frames per Second (FPS): 30.0
        Total Frames: 900
        Video Duration: 0:00:30
        ```
    
    Notes:
        - FPS values might not always be integers due to encoding variations.
        - The function uses OpenCV (`cv2.VideoCapture`) for metadata extraction.
        - Some videos with variable frame rates may report approximate durations.
    """
    if not os.path.exists(video_file):
        raise FileNotFoundError(f"Video file {video_file} not found.")

    cap = cv2.VideoCapture(video_file)
    if not cap.isOpened():
        raise IOError(f"Unable to open video file {video_file}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps
    video_duration = timedelta(seconds=duration)

    results = {
        "video file" : video_file,
        "frames per second (FPS)": fps,
        "total frames": frame_count,
        "video duration" : video_duration
    }

    for result in results:
        print(f"{result} : {results[result]}")

    # print(f"Video File: {video_file}")
    # print(f"Frames per Second (FPS): {fps}")
    # print(f"Total Frames: {frame_count}")
    # print(f"Video Duration: {timedelta(seconds=duration)}")

    cap.release()

    return results

def natural_sort_key(filename):
    """Generate a natural sort key for filenames."""
    return [int(text) if text.isdigit() else text for text in re.split(r'(\d+)', filename)]

def get_image_files(input_directory):
    """Retrieve and sort image files from the input directory."""
    return sorted(
        [f for f in os.listdir(input_directory) if f.endswith('.jpg')],
        key=natural_sort_key
    )
