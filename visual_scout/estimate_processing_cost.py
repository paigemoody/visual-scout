import subprocess
import os
import math 
from PIL import Image

def count_gif_frames(gif_path):
    """
    Returns the number of frames in a GIF file.

    Args:
        gif_path (str): Path to the GIF file.

    Returns:
        int: Number of frames in the GIF.
    """
    try:
        with Image.open(gif_path) as gif:
            frame_count = gif.n_frames  # n_frames gives total frames in a GIF
            print(f"{gif_path}: {frame_count} frames")
            return frame_count
    except Exception as e:
        print(f"Error processing {gif_path}: {e} -- skipping")
        return None


def get_video_duration(video_path):
    """Extract the duration of a video file using ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ],
        capture_output=True, text=True
    )
    try:
        duration = float(result.stdout.strip(video_path))
        print(f"{video_path}: {duration} seconds")
        return duration
    except Exception as e:
        print(f"Invalid video {video_path} -- skipping")
        return 0.0


def estimate_processing_cost(input_dir):
    """Estimate processing cost based on video durations and image counts."""
    total_length = 0

    # categorize input files
    video_file_exts = [".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv"]
    gif_file_exts = [".gif"]
    image_file_exts = [".jpg", ".jpeg", ".png"]

    video_filepaths = []
    gif_filepaths = []
    image_filepaths = []

    all_files = os.listdir(input_dir)

    print(f"\n\nValidating {len(all_files)} input files...")

    for file in all_files:
        file_extension = file.lower()[-4:]
        file_full_path = os.path.join(input_dir, file)
        if file_extension in video_file_exts:
            video_filepaths.append(file_full_path)
        elif file_extension in image_file_exts:
            image_filepaths.append(file_full_path)
        elif file_extension in gif_file_exts:
            gif_filepaths.append(file_full_path)
        else:
            print(f"\nFile type '{file_extension}' not supported, skipping {file}")
    
    # videos
    print(f"\n\nCalculating total duration of {len(video_filepaths)} input videos...")
    total_video_duration = 0
    for file in video_filepaths:
        duration = get_video_duration(file)
        total_video_duration += duration
    
    total_video_frames_to_process = 0
    if total_video_duration > 0:
        # assuming 2 sec frame sample rate
        total_video_frames_to_process = math.ceil(total_video_duration/2)
    
    # gifs
    print(f"\n\nCalculating total frame count of {len(gif_filepaths)} input gifs...")
    total_gif_frames = 0
    for file in gif_filepaths:
        frame_count = count_gif_frames(file)
        total_gif_frames += frame_count
    total_gif_frames_to_process = 0
    if total_gif_frames > 0:
        # assuming sampling of even frames only (eg frames 0, 2, 4, etc)
        total_gif_frames_to_process = math.ceil(total_gif_frames/2)


    print(f"\n\nTotal video frames to process after sampling and gridding: {total_video_frames_to_process}")
    print(f"Total gif frames to process after sampling and gridding: {total_gif_frames_to_process}")
    print(f"Total images to process: {len(image_filepaths)}")

    total_video_grids = math.ceil(total_video_frames_to_process / 9)
    total_gif_grids = math.ceil(total_gif_frames_to_process / 9)

    total_grids_to_process = total_video_grids + total_gif_grids

    print(f"\nTotal requests to OpenAI required: {total_grids_to_process}")

    total_image_files_to_process = total_grids_to_process + len(image_filepaths)

    cost_per_image_4o = 0.005
    cost_per_image_4o_mini = 0.0003

    total_cost_4o = total_image_files_to_process * cost_per_image_4o
    total_cost_4o_mini = total_image_files_to_process * cost_per_image_4o_mini
    
    # Output results
    print(f"\n\n\n⚠️ Warning: this is a napkin math estimate based on current cost per call for our logic using each model; your actual cost will be dependent on actual size (resolution, length, etc) of input videos and images. \n\nAlways be sure to validate cost esimates before processing large amounts of input data. \nFor a details on our estimation methodology see: https://github.com/paigemoody/visual-scout/issues/7#issuecomment-2724763408")
    print(f"\n\nEstimated processing cost for your {len(all_files)} files:")
    print(f"\n  - Using GPT 4o: ${total_cost_4o}\n")
    print(f"  - Using GPT 4o-mini: ${total_cost_4o_mini}\n")

