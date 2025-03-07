import cv2
import os
from datetime import timedelta
import warnings


def open_video(video_full_path):
    """
    Opens a video file using OpenCV and returns a VideoCapture object.

    This function attempts to open a video file and return an OpenCV `VideoCapture` object.
    It ensures the file exists before proceeding and handles errors related to file access 
    and OpenCV processing. If the file cannot be opened, a warning is issued, and `False` 
    is returned.

    Args:
        video_full_path (str): The full path to the video file.

    Returns:
        cv2.VideoCapture or bool: 
            - A `cv2.VideoCapture` object if the video is successfully opened.
            - `False` if the video cannot be opened due to file access issues or OpenCV errors.

    Raises:
        FileNotFoundError: If the video file does not exist at the specified path.
        Warning: If OpenCV fails to open the video file, a warning is issued instead of an exception.

    Error Handling:
        - If the file does not exist, a `FileNotFoundError` is raised.
        - If OpenCV cannot open the file, a warning is logged, and `False` is returned.
        - If OpenCV encounters an internal error while opening the file, a warning is issued.

    Notes:
        - The function ensures the file exists before attempting to open it.
        - OpenCV warnings are issued instead of raising exceptions for non-fatal errors.
    """

    if not os.path.exists(video_full_path):
        warning_message = f"Video file not found: {video_full_path}"
        raise FileNotFoundError(warning_message)

    try:
        cap = cv2.VideoCapture(video_full_path)
        if not cap.isOpened():
            warning_message = f"\n\nUnable to open video file: {video_full_path}. Skipping..."
            warnings.warn(warning_message)
            return False
        return cap

    except cv2.error as e:
        warnings.warn(f"OpenCV encountered an error while opening video {video_full_path}: {str(e)}") 
        return False


def extract_frames(output_frames_base_path, video_file):
    """
    Extracts frames from a video at fixed 2-second intervals and saves them as image files.

    This function processes a given video file, extracts frames at a defined interval, 
    and saves them as images in an output directory. It ensures the output directory 
    is removed if no frames are successfully extracted.

    Args:
        output_frames_base_path (str): The base directory where extracted frames will be saved.
        video_file (str): The path to the input video file.

    Raises:
        FileNotFoundError: If the specified video file does not exist.
        IOError: If the video file cannot be opened or read.
        Warning: If a frame cannot be read or saved.

    Processing Steps:
        1. Opens the video file and verifies it is readable.
        2. Computes FPS and total frame count to determine the video duration.
        3. Extracts frames at every 2-second interval.
        4. Saves each extracted frame as a JPEG file, named using timestamps.
        5. Removes up the output directory if no frames were saved.

    Notes:
        - Frames are extracted based on calculated frame indices, ensuring synchronization with FPS.
        - If a frame cannot be read or saved, a warning is issued, and the function continues.
        - The function handles floating-point precision issues when computing timestamps.
        - If no frames are successfully saved, the created output directory is deleted.

    Example:
        >>> extract_frames("output/output_frames", "example_video.mov")

    Output Directory Structure:
        output_frames_base_path/
        ├── example_video__frames/
        │   ├── frame_00-00-00_00-00-02.jpg
        │   ├── frame_00-00-02_00-00-04.jpg
        │   ├── ...
    """

    print(f"\n\nExtracting frames from {video_file}...")
    cap = open_video(video_file)

    if not cap:
        return False
    
    # only make output sub dir for video if video was able to be opened
    name_without_ext = video_file.split("/")[-1].split(".")[0]
    output_frames_video_path = os.path.join(output_frames_base_path, f"{name_without_ext}__frames")

    print("\n\noutput_frames_video_path:", output_frames_video_path)
    # make output dir 
    os.makedirs(output_frames_video_path, exist_ok=True)

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
        frame_path = os.path.join(output_frames_video_path, frame_filename)
        

        if cv2.imwrite(frame_path, frame):
            print(f"Saved: {frame_path}")
            saved_frames += 1
        else:
            warning_message = f"Error saving: {frame_filename}"
            warnings.warn(warning_message)

        frame_index += frame_interval  # Jump to the next interval

        if frame_index >= frame_count:  # Safety check
            print("Reached the last frame, stopping extraction.")
            break

    cap.release()

    # ensure the output directory is removed if no frames were extracted
    if saved_frames == 0:
        os.rmdir(output_frames_base_path)
        print(f"Removed empty output directory: {output_frames_base_path}")

    print(f"Frames saved: {saved_frames} in {output_frames_base_path}")
    

def get_valid_input_videos(full_path_input_dir):
    """
    Scans a directory for valid video files and returns a list of their full paths.

    This function checks if the specified input directory exists and scans for files 
    with common video extensions (`.mp4`, `.avi`, `.mov`, `.mkv`, `.flv`, `.wmv`). 
    It prints validation details and filters out non-video files.

    Args:
        full_path_input_dir (str): The absolute path to the input directory containing video files.

    Returns:
        list: A list of full paths to detected video files.
        None: If no valid video files are found.

    Raises:
        FileNotFoundError: If the input directory does not exist.

    Workflow:
        1. Checks if the input directory exists.
        2. Iterates through all files in the directory and filters files based on valid video extensions.
        3. Returns a list of full paths for valid video files.

    Notes:
        - Only filters based on file extensions; deeper validation (e.g., corrupt files) happens later.
    """

    # Validate files in input dir
    print(f"\n\nValidating files in {full_path_input_dir}...")

    # Ensure the input dir exists
    if not os.path.exists(full_path_input_dir):
        raise FileNotFoundError(f"Input directory {full_path_input_dir} not found.")

    # Validate extensions, separate out video files (based on ext only - deeper validation happens later)
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'}

    video_files = []
    all_files = os.listdir(full_path_input_dir)
    print(f"\n\nTotal input files: {len(all_files)}\n")

    for f in all_files:
        extension = os.path.splitext(f)[1].lower()
        if extension in video_extensions:
            video_file_full_path = os.path.join(full_path_input_dir, f)
            video_files.append(video_file_full_path)
        else:
            print(f"Non-video file to be ignored: {f}")

    if not video_files:
        print("No video files found in the directory.")
        return
    
    print(f"\nTotal input video files {len(video_files)} \n\nStarting processing...")

    return video_files


def create_output_dir():
    """"""
    full_path_output_dir = os.path.join(os.getcwd(), "output", "output_frames")
    print(f"\nMaking directory {full_path_output_dir} to store frame image files")
    os.makedirs(full_path_output_dir, exist_ok=True)

    return full_path_output_dir




def main_extract_frames(input_dir):
    """
    Extracts frames from all valid video files in the specified input directory.

    This function verifies the existence of the input directory, identifies valid 
    video files, and extracts frames at fixed intervals from each video. Extracted 
    frames are saved in an organized output directory structure.

    Args:
        input_dir (str): The path to the directory containing input videos. 
                         Can be either a relative or absolute path.

    Raises:
        FileNotFoundError: If the input directory does not exist or contains no valid video files.

    Workflow:
        1. Ensures `input_dir` is an absolute path.
        2. Validates the existence of the input directory.
        3. Identifies valid video files in the directory.
        4. Creates an output directory (`output/output_frames/`) if it doesn’t exist.
        5. Extracts frames from each video and saves them in subdirectories.
        6. Prints progress updates and completion messages.

    Output:
        - Extracted frames are saved in `output/output_frames/{video_name}__frames/`
        - Each frame file is named based on its timestamp.

    Example Usage:
        >>> main_extract_frames("videos")
        Making directory /current_directory/output/output_frames to store frame image files
        Extracting frames from: /current_directory/videos/sample_video.mp4
        Frame extraction complete.

    Notes:
        - Uses `get_valid_input_videos()` to filter video files by extension.
        - Calls `extract_frames()` for each valid video file.
        - Creates necessary directories if they don’t exist.
    """

    # Ensure `input_dir` is an absolute path
    if not os.path.isabs(input_dir):
        base_path = os.getcwd()
        full_path_input_dir = os.path.join(base_path, input_dir)
    else:
        full_path_input_dir = input_dir

    # Validate and retrieve video files
    video_file_paths = get_valid_input_videos(full_path_input_dir)

    # Define and create the output directory

    full_path_output_dir = create_output_dir()
    # full_path_output_dir = os.path.join(os.getcwd(), "output", "output_frames")
    # print(f"\nMaking directory {full_path_output_dir} to store frame image files")
    # os.makedirs(full_path_output_dir, exist_ok=True)

    # Run frame extraction
    for video_file_path in video_file_paths:
        print(f"\nExtracting frames from: {video_file_path}")
        extract_frames(full_path_output_dir, video_file_path)

    print("\nFrame extraction complete.")


if __name__ == "__main__":
    main_extract_frames()
