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
            return frame_count
    except Exception as e:
        print(f"\tError processing {gif_path}: {e} -- will be skipped")
        return 0


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
        return duration
    except Exception as e:
        print(f"\t⚠️ Invalid video {video_path} cannot be processed -- will be skipped")
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

    if len(all_files) < 1:
        print(f"\n⚠️ Error: Input directory is empty: {input_dir}\n")
        return

    print(f"\n\nValidating {len(all_files)} input file(s) in {input_dir}...")

    invalid_filepaths = {
        "video": [],
        "gif": [],
        "image": [],
        "other": []
    }

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
            invalid_filepaths["other"].append(file)
            print(f"\n\t⚠️ Unsupported file type: '{file_extension}' found for {file_full_path} -- will be skipped")
    

    # videos
    if len(video_filepaths) > 0:
        print(f"\n\nCalculating total duration of {len(video_filepaths)} input video(s)...\n")
    total_video_duration = 0
    for file in video_filepaths:
        duration = get_video_duration(file)
        if duration <=0:
            invalid_filepaths["video"].append(file)
        total_video_duration += duration
    
    total_video_frames_to_process = 0
    if total_video_duration > 0:
        # assuming 2 sec frame sample rate
        total_video_frames_to_process = math.ceil(total_video_duration/2)
    
    # gifs
    if len(gif_filepaths) > 0:
        print(f"\n\nCalculating total frame count of {len(gif_filepaths)} input gif(s)...")
    total_gif_frames = 0
    for file in gif_filepaths:
        frame_count = count_gif_frames(file)
        if frame_count <=0:
            invalid_filepaths["gif"].append(file)
        total_gif_frames += frame_count

    total_gif_frames_to_process = 0
    if total_gif_frames > 0:
        # assuming sampling of even frames only (eg frames 0, 2, 4, etc)
        total_gif_frames_to_process = math.ceil(total_gif_frames/2)


    total_video_grids = math.ceil(total_video_frames_to_process / 9)
    total_gif_grids = math.ceil(total_gif_frames_to_process / 9)

    total_grids_to_process = total_video_grids + total_gif_grids
    total_image_files_to_process = total_grids_to_process + len(image_filepaths)

    if total_image_files_to_process < 1:
        print(f"\n⚠️ No valid input files found in {input_dir}; this dataset will not be able to be processed.")
        return

    # Display summary:
    print(f"\n\nCalculating processing cost for files in {input_dir}:")

    # Videos
    print(f"""
    Videos
    - Total valid input videos: {len(video_filepaths) - len(invalid_filepaths["video"])}
    - Total duration of input videos: {total_video_duration} seconds
    - Total video frames to be processed: {total_video_frames_to_process}
    - Total video frame 3x3 grids to be processed: {total_video_grids}
    """)

    # Gifs
    print(f"""
    GIFs
    - Total valid input gifs: {len(gif_filepaths) - len(invalid_filepaths["gif"])}
    - Total gif frames to be processed: {total_gif_frames_to_process}
    - Total gif frame 3x3 grids to be processed: {total_gif_grids}
    """)

    # Images
    print(f"""
    Images
    - Total input stand-alone images to be procssed: {len(image_filepaths) - len(invalid_filepaths["image"])}
    """)

    print(f"""
    ⚠️ Invalid input files (skipped for estimation, cannot be processed): 
    
    - Videos ({len(invalid_filepaths["video"])}): {invalid_filepaths["video"]}
    - Gifs ({len(invalid_filepaths["gif"])}): {invalid_filepaths["gif"]}
    - Images ({len(invalid_filepaths["image"])}): {invalid_filepaths["image"]}
    - Unsupported file type(s) ({len(invalid_filepaths["other"])}): {invalid_filepaths["other"]}
    """)

    # Based on openAI pricing as of 3-21-2025, prompt as of 3-21-2025 and average image size - details in: 
    # https://github.com/paigemoody/visual-scout/issues/7#issuecomment-2724828185
    # TODO - make this dynamic
    cost_per_image_4o = 0.005
    cost_per_image_4o_mini = 0.0003

    total_cost_4o = total_image_files_to_process * cost_per_image_4o
    total_cost_4o_mini = total_image_files_to_process * cost_per_image_4o_mini
    
    # Output results
    print(
        f"""********* ⚠️ Warning ⚠️ ***********
          
- The following is a napkin math estimate based on current cost per call for current package logic using each OpenAI model.
        
- Your actual cost will be dependent on actual size of your input files (resolution, length, etc).
        
- Always be sure to validate cost esimates before processing large amounts of input data.
        
- For a details on estimation methodology see: https://github.com/paigemoody/visual-scout/issues/7#issuecomment-2724763408

*********************************""")
    
    print(f"\n\nEstimated processing cost for your {len(all_files)} valid input file(s):")
    print(f"\n  - Using GPT 4o: ${total_cost_4o}\n")
    print(f"  - Using GPT 4o-mini: ${total_cost_4o_mini}\n")

