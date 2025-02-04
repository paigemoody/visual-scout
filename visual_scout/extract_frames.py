import cv2
import os
import math
from datetime import timedelta
import argparse


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
    if not os.path.exists(video_file):
        raise FileNotFoundError(f"Video file {video_file} not found.")

    output_dir = "output_frames"
    base_name = os.path.basename(video_file)
    name_without_ext = os.path.splitext(base_name)[0]
    frame_dir = os.path.join(output_dir, f"{name_without_ext}__frames")
    os.makedirs(frame_dir, exist_ok=True)

    print(f"\nProcessing: {video_file}")
    cap = cv2.VideoCapture(video_file)
    if not cap.isOpened():
        raise IOError(f"Unable to open video file {video_file}")

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

        # cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)  # Move to the exact frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, min(frame_index, frame_count - 1))  # Avoid overshooting
        ret, frame = cap.read()
        
        if not ret:
            print(f"Warning: Could not read frame at index {frame_index}. Skipping...")
            break  # Exit loop to avoid infinite error printing

        timestamp = round(frame_index / fps, 2)  # Round to avoid floating point drift
        start_time = str(timedelta(seconds=int(timestamp)))  # Ensure clean HH-MM-SS format
        end_time = str(timedelta(seconds=int(timestamp + sampling_interval)))

        frame_filename = f"frame_{start_time.replace(':', '-')}_{end_time.replace(':', '-')}.jpg"
        frame_path = os.path.join(frame_dir, frame_filename)

        if cv2.imwrite(frame_path, frame):
            print(f"Saved: {frame_filename}")
            saved_frames += 1
        else:
            print(f"Error saving: {frame_filename}")

        frame_index += frame_interval  # Jump to the next interval

        if frame_index >= frame_count:  # Safety check
            print("Reached the last frame, stopping extraction.")
            break

    cap.release()
    print(f"Frames saved: {saved_frames} in {frame_dir}")


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
    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"Input directory {input_dir} not found.")

    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'}  # Add more if needed
    video_files = [f for f in os.listdir(input_dir) if os.path.splitext(f)[1].lower() in video_extensions]

    if not video_files:
        print("No video files found in the directory.")
        return

    print(f"Found {len(video_files)} video files. Processing...")

    for video_file in video_files:
        video_path = os.path.join(input_dir, video_file)
        print(f"\nExtracting frames from: {video_file}")
        extract_frames(video_path)

    print("\nAll videos processed successfully.")


def main():
    """
    Parses command-line arguments and runs extract_frames_from_directory.
    Allows the user to run the script via the command:
        python3 extract_frames.py <input_directory>
    """
    parser = argparse.ArgumentParser(description="Extract frames from all videos in a given directory.")
    parser.add_argument(
        "input_directory",
        type=str,
        help="Path to the directory containing video files."
    )

    args = parser.parse_args()

    # Ensure the directory exists
    if not os.path.exists(args.input_directory):
        print(f"Error: The directory '{args.input_directory}' does not exist.")
        return

    # Run frame extraction
    extract_frames_from_directory(args.input_directory)

if __name__ == "__main__":
    main()

