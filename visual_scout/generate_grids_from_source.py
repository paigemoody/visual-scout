import cv2
import os
import numpy as np
from datetime import timedelta
import warnings
import shutil
from PIL import Image, UnidentifiedImageError
from visual_scout.constants import SSIM_THRESHOLDS, SAMPLING_INTERVAL
from visual_scout.utils.grid_utils import create_grid, save_grid 
from visual_scout.utils.video_utils import open_video
from visual_scout.utils.gif_utils import open_gif,format_gif_timestamp
from visual_scout.utils.media_utils import get_file_type_from_extension,format_timestamps, get_valid_media_files
from visual_scout.utils.frame_utils import create_frame_path, is_similar_frame, make_frame_record

def generate_grids_from_media_stream(media_file, output_dir, grid_dimension, ssmi_threshold, use_static_sample_rate):
    """
    Extract frames from a media file and generate grids incrementally as frames stream in.

    Args:
        media_file (str): Path to the video, gif, or image file.
        output_dir (str): Directory where grid images should be saved.
        grid_dimension (int): Grid size (e.g., 3 for 3x3).
        ssmi_threshold (float): SSIM threshold for frame similarity.
        use_static_sample_rate (bool): If True, extract every Nth frame; otherwise skip similar ones.

    Returns:
        list of dict: Metadata for each saved grid.
    """
    file_type = get_file_type_from_extension(media_file)
    frames_per_grid = grid_dimension ** 2
    collected = []
    saved_grids = []

    if file_type == "video":
        saved_grids = _generate_video_grids(media_file, output_dir, grid_dimension, frames_per_grid, ssmi_threshold, use_static_sample_rate, collected)

    elif file_type == "gif":
        saved_grids = _generate_gif_grids(media_file, output_dir, grid_dimension, frames_per_grid, ssmi_threshold, use_static_sample_rate, collected)

    elif file_type == "image":
        image = Image.open(media_file).convert("RGB")
        image_array = np.array(image)
        record = make_frame_record(image_array, "00:00:00", "00:00:00")
        collected.append(record)
        saved_grids += flush_grid(collected, output_dir, grid_dimension)

    if collected:
        saved_grids += flush_grid(collected, output_dir, grid_dimension)

    return saved_grids

def _generate_video_grids(media_file, output_dir, grid_dimension, frames_per_grid, ssmi_threshold, use_static_sample_rate, collected):
    """
    Stream frames from a video file and generate grids when enough frames are collected.

    Args:
        media_file (str): Path to video.
        output_dir (str): Where grids should be saved.
        grid_dimension (int): Grid size (e.g., 3 for 3x3).
        frames_per_grid (int): Total number of frames per grid.
        ssmi_threshold (float): SSIM threshold.
        use_static_sample_rate (bool): Whether to skip frame similarity check.
        collected (list): Shared list to store frames across calls.

    Returns:
        list of dict: Saved grid metadata.
    """
    cap = open_video(media_file)
    if not cap:
        return []

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_interval = round(fps * SAMPLING_INTERVAL)
    frame_index = 0
    most_recent_frame = None
    saved = []

    while frame_index < frame_count:
        cap.set(cv2.CAP_PROP_POS_FRAMES, min(frame_index, frame_count - 1))
        ret, frame = cap.read()
        if not ret:
            break

        timestamp = round(frame_index / fps, 2)
        start_time, end_time = format_timestamps(timestamp)

        if not is_similar_frame(most_recent_frame, frame, ssmi_threshold, use_static_sample_rate):
            frame = frame
            collected.append(make_frame_record(frame, start_time, end_time))
            most_recent_frame = frame

        if len(collected) == frames_per_grid:
            saved += flush_grid(collected, output_dir, grid_dimension)

        frame_index += frame_interval

    cap.release()
    return saved

def _generate_gif_grids(media_file, output_dir, grid_dimension, frames_per_grid, ssmi_threshold, use_static_sample_rate, collected):
    """
    Stream frames from an animated GIF and generate grids when enough frames are collected.

    Args:
        media_file (str): Path to gif.
        output_dir (str): Where grids should be saved.
        grid_dimension (int): Grid size.
        frames_per_grid (int): Number of frames per grid.
        ssmi_threshold (float): SSIM threshold.
        use_static_sample_rate (bool): Whether to skip similarity check.
        collected (list): Frame buffer shared across calls.

    Returns:
        list of dict: Metadata for each grid saved.
    """
    gif = open_gif(media_file)
    if not gif:
        return []

    frame_index = 0
    most_recent_frame = None
    saved = []

    while True:
        try:
            gif.seek(frame_index)
        except EOFError:
            break

        if frame_index % SAMPLING_INTERVAL == 0:
            frame_img = gif.convert("RGB")
            frame_array = np.array(frame_img)
            start_time, end_time = format_gif_timestamp(frame_index)

            if not is_similar_frame(most_recent_frame, frame_array, ssmi_threshold, use_static_sample_rate):
                collected.append(make_frame_record(frame_array, start_time, end_time))
                most_recent_frame = frame_array

            if len(collected) == frames_per_grid:
                saved += flush_grid(collected, output_dir, grid_dimension)

        frame_index += 1

    return saved

def flush_grid(collected, output_dir, grid_dimension):
    """
    Convert a list of frame records into a grid image and save it.

    Args:
        collected (list): Frame records with 'image', 'start_time', 'end_time'.
        output_dir (str): Directory to save grid.
        grid_dimension (int): NxN size of grid.

    Returns:
        list of dict: Metadata about the saved grid.
    """
    if not collected:
        return []
    frame_width, frame_height = collected[0]["image"].shape[1], collected[0]["image"].shape[0]
    grid = create_grid([Image.fromarray(cv2.cvtColor(f["image"], cv2.COLOR_BGR2RGB)) for f in collected], frame_width, frame_height, grid_dimension)
    start_time_formatted = collected[0]["start_time"].replace(":", "-")
    end_time_formatted = collected[0]["end_time"].replace(":", "-")
    path = save_grid(grid, output_dir, start_time_formatted, end_time_formatted)
    meta = {
        "path": path,
        "start_timestamp": collected[0]["start_time"],
        "end_timestamp": collected[-1]["end_time"],
        "num_images": len(collected),
    }
    collected.clear()
    return [meta]

def main_generate_grids_from_media(input_dir, grid_size, similarity="default", use_static_sample_rate=False):
    """
    Generate image grids directly from media files (video, gif, image) in an input directory.

    Args:
        input_dir (str): Directory containing media files to process.
        grid_size (int): Grid dimension (e.g. 3 = 3x3 grid).
        similarity (str): One of 'loose', 'default', or 'strict'.
        use_static_sample_rate (bool): If True, extract every nth frame without similarity check.

    Returns:
        str: Path to the directory where grids were saved.
    """
    input_dir = os.path.abspath(input_dir)
    if not os.path.exists(input_dir) or not os.listdir(input_dir):
        raise FileNotFoundError(f"Input directory '{input_dir}' does not exist or is empty.")

    base_output_dir = os.path.join(os.getcwd(), "output", "output_grids")

    os.makedirs(base_output_dir, exist_ok=True)
    print(f"\nGrids will be saved to: {base_output_dir}")

    ssmi_threshold = SSIM_THRESHOLDS[similarity]
    media_files = get_valid_media_files(input_dir)

    for media_file in media_files:
        print(f"\nProcessing: {media_file}")
        output_dir = os.path.join(base_output_dir, os.path.basename(media_file).split(".")[0]+"__frames__grids")
        print(f"Output to be written to {output_dir}")
        try:
            generate_grids_from_media_stream(
                media_file,
                output_dir,
                grid_size,
                ssmi_threshold,
                use_static_sample_rate,
            )
        except Exception as e:
            print(f"❌ Failed to process {media_file}: {e}")

    return output_dir

if __name__ == "__main__":
    input_dir = "visual_scout/example_input"
    main_generate_grids_from_media(input_dir, 3, similarity="default", use_static_sample_rate=False)