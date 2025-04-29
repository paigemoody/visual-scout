import subprocess
import os
import math 
from PIL import Image
from visual_scout.constants import COST_PER_REQUEST_4o, COST_PER_REQUEST_4o_mini

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

def get_list_filenames_from_filepaths(filepaths_list):
    filenames_list = [file_path.split("/")[-1] for file_path in filepaths_list]
    if filenames_list:
        return filenames_list
    return ""


def convert_video_to_mp4(video_path):
    """Convert any video format to MP4 without audio using ffmpeg and log detailed output.
    
    # TODO - see if this is actually necessary...
    """
    # Define the output MP4 file path
    base, ext = os.path.splitext(video_path)
    mp4_video_path = f"{base}.mp4"
    
    # Use the ultrafast preset, disable audio with -an, and don't encode audio
    process = subprocess.Popen([
        "ffmpeg", "-i", video_path, "-vcodec", "libx264", "-preset", "ultrafast", 
        "-crf", "28", "-an",  # -an disables audio
        mp4_video_path
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Capture the output and errors for logging purposes
    stdout, stderr = process.communicate()

    # Log the ffmpeg output for debugging
    print(f"FFmpeg STDOUT: {stdout}")
    print(f"FFmpeg STDERR: {stderr}")
    
    return mp4_video_path


def get_video_duration(video_path):
    """Extract the duration of a video file, converting it to MP4 if necessary."""
    # If the video is not in MP4 format, convert it?
    # base, ext = os.path.splitext(video_path)
    # if ext.lower() != '.mp4':
    #     print(f"Converting {video_path} to MP4...")
    #     video_path = convert_video_to_mp4(video_path)
    
    # Extract the duration of the MP4 video
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ],
        capture_output=True, text=True
    )
    
    try:
        duration = float(result.stdout.strip())
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

    for file_path in all_files:
        file_extension = file_path.lower()[-4:]
        file_full_path = os.path.join(input_dir, file_path)
        if file_extension in video_file_exts:
            video_filepaths.append(file_full_path)
        elif file_extension in image_file_exts:
            image_filepaths.append(file_full_path)
        elif file_extension in gif_file_exts:
            gif_filepaths.append(file_full_path)
        else:
            invalid_filepaths["other"].append(file_full_path)
            print(f"\n\t⚠️ Unsupported file type: '{file_extension}' found for {file_full_path} -- will be skipped")
    

    # videos
    if len(video_filepaths) > 0:
        print(f"\n\nCalculating total duration of {len(video_filepaths)} input video(s)...\n")
    total_video_duration = 0
    for file_path in video_filepaths:
        duration = get_video_duration(file_path)
        print(f"\nduration {file_path}: {duration/60} minutes")
        if duration <=0:
            invalid_filepaths["video"].append(file_path)
        total_video_duration += duration
    
    print("total_video_duration:", total_video_duration)
    
    total_video_frames_to_process = 0
    if total_video_duration > 0:
        # assuming 2 sec frame sample rate
        total_video_frames_to_process = math.ceil(total_video_duration/2)
    
    # gifs
    if len(gif_filepaths) > 0:
        print(f"\n\nCalculating total frame count of {len(gif_filepaths)} input gif(s)...")
    total_gif_frames = 0
    for file in gif_filepaths:
        frame_count = count_gif_frames(file_path)
        if frame_count <=0:
            invalid_filepaths["gif"].append(file_path)
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
    total_valid_videos = len(video_filepaths) - len(invalid_filepaths["video"])
    print(f"""
    Videos
    - Total valid input videos: {total_valid_videos}
    - Total duration of input videos: {round(total_video_duration,1)} seconds ( {round(total_video_duration/60,2)} minutes, {round(total_video_duration/3600, 2)} hours)
    - Total video frames to be processed: {total_video_frames_to_process}
    - Total video frame 3x3 grids to be processed: {total_video_grids}
    """)

    # Gifs
    total_valid_gifs = len(gif_filepaths) - len(invalid_filepaths["gif"])
    print(f"""
    GIFs
    - Total valid input gifs: {total_valid_gifs}
    - Total gif frames to be processed: {total_gif_frames_to_process}
    - Total gif frame 3x3 grids to be processed: {total_gif_grids}
    """)

    # Images
    total_valid_images = len(image_filepaths) - len(invalid_filepaths["image"])
    print(f"""
    Images
    - Total input stand-alone images to be procssed: {total_valid_images}
    """)

    total_valid_input_files = total_valid_videos + total_valid_gifs + total_valid_images

    print(f"""
    ⚠️ Invalid input files (skipped for estimation, cannot be processed): 
    
    - Videos ({len(invalid_filepaths["video"])}): {get_list_filenames_from_filepaths(invalid_filepaths["video"])}
    - Gifs ({len(invalid_filepaths["gif"])}): {get_list_filenames_from_filepaths(invalid_filepaths["gif"])}
    - Images ({len(invalid_filepaths["image"])}): {get_list_filenames_from_filepaths(invalid_filepaths["image"])}
    - Unsupported file type(s) ({len(invalid_filepaths["other"])}): {get_list_filenames_from_filepaths(invalid_filepaths["other"])}
    """)

    total_cost_4o = total_image_files_to_process * COST_PER_REQUEST_4o
    total_cost_4o_mini = total_image_files_to_process * COST_PER_REQUEST_4o_mini
    
    # Output results
    print(
        f"""********* ⚠️ Warning ⚠️ ***********
          
- The following is a napkin math estimate based on current cost per call for current package logic using each OpenAI model.
        
- Your actual cost will be dependent on actual size of your input files (resolution, length, etc).
        
- Always be sure to validate cost esimates before processing large amounts of input data.
        
- For a details on estimation methodology see: https://github.com/paigemoody/visual-scout/issues/7#issuecomment-2724763408

*********************************""")
    
    print(f"\n\nEstimated processing cost for your {total_valid_input_files} valid input file(s):")
    print(f"\n  - Using GPT 4o: ${total_cost_4o}\n")
    print(f"  - Using GPT 4o-mini: ${total_cost_4o_mini}\n")

    return total_cost_4o, total_cost_4o_mini

