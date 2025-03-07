import cv2
import os
from datetime import timedelta
import warnings
from visual_scout.io_utils import make_output_dir


def open_video(video_file):
    executed_from = os.getcwd().replace("//", "/") # handle possible leading slash in input
    video_full_path = os.path.join(executed_from, video_file)

    if not os.path.exists(video_full_path):
        warning_message = f"Video file not found: {video_full_path}"
        raise FileNotFoundError(warning_message)

    try:
        cap = cv2.VideoCapture(video_full_path)
        if not cap.isOpened():
            warning_message = f"Unable to open video file: {video_full_path}. Skipping..."
            warnings.warn(warning_message)
            return False
        return cap

    except cv2.error as e:
        warnings.warn(f"OpenCV encountered an error while opening video {video_full_path}: {str(e)}") 
        return False


def extract_frames(video_file):
    """
    Extracts frames from a video at fixed 2-second intervals and saves them as image files.

    Args:
        video_file (str): Path to the input video file.

    Raises:
        FileNotFoundError: If the specified video file does not exist.
        IOError: If the video file cannot be opened.

    Notes:
        - The function calculates the video's FPS to determine the exact frames to extract.
        - Instead of setting a timestamp directly, it extracts frames based on index calculations.
        - The extracted frames are saved as JPEG images.
    """
    cap = open_video(video_file)

    if not cap:
        return False
    # only make output sub dir if video was able to be opened
    output_frame_dir = make_output_dir(video_file, "frames")

    print("\n\n:", output_frame_dir)


    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps

    print(f"Video FPS: {fps}")
    print(f"Total Frames: {frame_count}")
    print(f"Video Duration: {timedelta(seconds=duration)}")

    sampling_interval = 2  # Extract a frame every 2 seconds
    frame_interval = round(fps * sampling_interval)  # Force rounding to nearest integer frame count

    print(f"Extracting every {frame_interval} frames ({sampling_interval} seconds interval)")
    
    frame_index = 0
    saved_frames = 0

    while frame_index < frame_count:  # Ensure we do not go beyond available frames
        print(f"Processing frame {frame_index} / {frame_count}")  # Debug log

        cap.set(cv2.CAP_PROP_POS_FRAMES, min(frame_index, frame_count - 1))  # Avoid overshooting
        ret, frame = cap.read()
        
        if not ret:
            print(f"Warning: Could not read frame at index {frame_index}. Skipping...")
            break  # Exit loop to avoid infinite error printing

        timestamp = round(frame_index / fps, 2)  # Round to avoid floating point drift
        start_time = str(timedelta(seconds=int(timestamp)))  # Ensure clean HH-MM-SS format
        end_time = str(timedelta(seconds=int(timestamp + sampling_interval)))

        frame_filename = f"frame_{start_time.replace(':', '-')}_{end_time.replace(':', '-')}.jpg"
        frame_path = os.path.join(output_frame_dir, frame_filename)

        if cv2.imwrite(frame_path, frame):
            print(f"Saved: {frame_path}")
            saved_frames += 1
        else:
            print(f"Error saving: {frame_filename}")

        frame_index += frame_interval  # Jump to the next interval

        if frame_index >= frame_count:  # Safety check
            print("Reached the last frame, stopping extraction.")
            break

    cap.release()

    # ensure the output directory is removed if no frames were extracted
    if saved_frames == 0:
        os.rmdir(output_frame_dir)
        print(f"Removed empty output directory: {output_frame_dir}")

    print(f"Frames saved: {saved_frames} in {output_frame_dir}")


def extract_frames_from_directory(input_dir):
    """
    Processes all video files in a given directory and extracts frames at fixed intervals.

    This function searches for all video files in the specified input directory and 
    extracts frames using the `extract_frames` function. The extracted frames are 
    saved in corresponding subdirectories within the output directory, "output_frames/".

    Args:
        input_dir (str): Directory containing video files to process.

    Raises:
        FileNotFoundError: If the specified input directory does not exist.
    """
    print(f"\n\nValidating files in {input_dir}...")
    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"Input directory {input_dir} not found.")

    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'}

    video_files = []

    all_files = os.listdir(input_dir)
    print(f"\n\nTotal input files: {len(all_files)}\n")

    for f in all_files:
        extension = os.path.splitext(f)[1].lower()
        if extension in video_extensions:
            video_files.append(f)
        else:
            print(f"Non-video file to be ignored: {f}")

    if not video_files:
        print("No video files found in the directory.")
        return

    print(f"\nTotal input video files {len(video_files)} \n\nStarting processing...")

    for video_file in video_files:
        video_path = os.path.join(input_dir, video_file)
        print(f"\nExtracting frames from: {video_file}")
        extract_frames(video_path)

    print("\nFrame extraction complete.")


def main_extract_frames(input_dir):
    """
    Confirm input dir exists, then run frame extraction
    """

    # Ensure the directory exists
    if not os.path.exists(input_dir):
        print(f"Error: The directory '{input_dir}' does not exist.")
        return

    # Run frame extraction
    extract_frames_from_directory(input_dir)

if __name__ == "__main__":
    main_extract_frames()
