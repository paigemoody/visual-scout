import cv2
import os
from datetime import timedelta
import warnings
import shutil
from PIL import Image, UnidentifiedImageError


def open_video(video_full_path):
    """
    Opens a video file using OpenCV and returns a VideoCapture object.

    Ensures the file exists before attempting to open it. If OpenCV fails to open 
    the file, a warning is issued, and `False` is returned.

    Args:
        video_full_path (str): Full path to the video file.

    Returns:
        cv2.VideoCapture or bool:
            - A `cv2.VideoCapture` object if the video is successfully opened.
            - `False` if the video cannot be opened.

    Raises:
        FileNotFoundError: If the video file does not exist.

    Notes:
        - If OpenCV encounters an error, a warning is issued instead of an exception.
        - The function returns `False` for unreadable or corrupted videos.
    """

    if not os.path.exists(video_full_path):
        warning_message = f"Video file not found: {video_full_path}"
        raise FileNotFoundError(warning_message)

    try:
        cap = cv2.VideoCapture(video_full_path)
        print(f"cap: {cap.isOpened()}")
        if not cap.isOpened():
            print("cap not opened")
            warning_message = f"\n\nUnable to open video file: {video_full_path}. Skipping..."
            warnings.warn(warning_message)
            print("sent warning") 
            return False       
        return cap

    except cv2.error as e:
        print("sending warning now!!")
        warnings.warn(f"OpenCV encountered an error while opening video {video_full_path}: {str(e)}") 
        return False

def open_gif(gif_full_path):
    """
    Opens a GIF image file using PIL (Pillow).

    Args:
        gif_full_path (str): Full path to the GIF file.

    Returns:
        Image.Image: A PIL Image object if the file is successfully opened.
        None: If the file cannot be opened.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.exists(gif_full_path):
        raise FileNotFoundError(f"Image file not found: {gif_full_path}")

    try:
        gif = Image.open(gif_full_path)
        gif.verify()  # ensure the file is not corrupted
        return Image.open(gif_full_path)  # reopen because verify() closes the file
    except (UnidentifiedImageError, OSError) as e:
        warnings.warn(f"Unable to open GIF file: {gif_full_path}. Skipping... Error: {e}")
        return None


def extract_frames(output_frames_base_path, media_file):
    """
    Extracts frames from a video, animated GIF, or processes a single image file.

    If the input is a video, frames are extracted at fixed 2-second intervals.
    If the input is a static image, it is treated as a single "frame" and saved accordingly.
    If the input is an animated GIF, all frames are extracted, but frame timing may vary.

    Args:
        output_frames_base_path (str): The base directory where extracted frames will be saved.
        media_file (str): The path to the input video or image file.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        IOError: If the media file cannot be opened or read.
        Warning: If a frame cannot be read or saved.

    Processing Steps:
        1. Determines whether the input is a video, animated GIF, or static image.
        2. If it's a static image, saves it as a single frame.
        3. If it's a video, extracts frames at every 2-second interval.
        4. If it's an animated GIF, extracts all frames sequentially.
        5. Saves extracted frames with timestamped filenames.
        6. Removes the output directory if no frames were saved.

    Notes:
        - Frames are extracted based on calculated frame indices for videos.
        - GIFs do not have a fixed FPS like videos; instead, they store frame durations, which can vary per frame.
        - If no frames are successfully saved, the created output directory is deleted.


    Output Directory Structure:
        output_frames_base_path/
        ├── example_video__frames/
        │   ├── frame_00-00-00_00-00-02.jpg
        │   ├── frame_00-00-02_00-00-04.jpg
        ├── example_image__frames/
        │   ├── frame_0-00-00_0-00-00.jpg
        ├── example_animation__frames/
        │   ├── frame_00-00-00.jpg
        │   ├── frame_00-00-01.jpg
    """
    
    if not os.path.exists(media_file):
        raise FileNotFoundError(f"Media file {media_file} not found.")
    
    name_without_ext = os.path.splitext(os.path.basename(media_file))[0]
    output_frames_media_path = os.path.join(output_frames_base_path, f"{name_without_ext}__frames")
    os.makedirs(output_frames_media_path, exist_ok=True)
    
    # Determine if input is a video, animated GIF, or static image
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'}
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    gif_extension = '.gif'
    extension = os.path.splitext(media_file)[1].lower()
    
    if extension in image_extensions:
        # Handle static image case
        frame_filename = "frame_0-00-00_0-00-00.jpg"
        frame_path = os.path.join(output_frames_media_path, frame_filename)
        shutil.copy(media_file, frame_path)
        print(f"Saved image as frame: {frame_path}")
        return
    
    elif extension in video_extensions:
        # Handle video case
        print(f"\n\nExtracting frames from {media_file}...")
        saved_frames = 0
        cap = open_video(media_file)
        print("cap:", cap)
        if cap:
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

            while frame_index < frame_count:
                print(f"Processing frame {frame_index} / {frame_count}")
                cap.set(cv2.CAP_PROP_POS_FRAMES, min(frame_index, frame_count - 1))
                ret, frame = cap.read()
                
                if not ret:
                    print(f"Warning: Could not read frame at index {frame_index}. Skipping...")
                    break

                timestamp = round(frame_index / fps, 2)
                start_time = str(timedelta(seconds=int(timestamp)))
                end_time = str(timedelta(seconds=int(timestamp + sampling_interval)))

                frame_filename = f"frame_{start_time.replace(':', '-')}_{end_time.replace(':', '-')}.jpg"
                frame_path = os.path.join(output_frames_media_path, frame_filename)
                
                if cv2.imwrite(frame_path, frame):
                    print(f"Saved: {frame_path}")
                    saved_frames += 1
                else:
                    warnings.warn(f"Error saving: {frame_filename}")

                frame_index += frame_interval
                if frame_index >= frame_count:
                    print("Reached the last frame, stopping extraction.")
                    break

            cap.release()
        
        if saved_frames == 0:
            os.rmdir(output_frames_media_path)
            print(f"Removed empty output directory: {output_frames_media_path}")
        else:
            print(f"Frames saved: {saved_frames} in {output_frames_media_path}")
        return
    
    elif extension == gif_extension:
        # TODO - rn this gets all frames from GIFs - overkill - make it smarter
        # Handle animated GIF case - in the Pillow (PIL) package, a GIF is considered an image
        print(f"\n\nExtracting frames from animated GIF: {media_file}...")
        gif = open_gif(media_file)
        frame_index = 0

        while True:
            frame_filename = f"frame_00-00-{frame_index}.jpg"
            frame_path = os.path.join(output_frames_media_path, frame_filename)
            gif.seek(frame_index)
            gif.convert("RGB").save(frame_path)
            print(f"Saved: {frame_path}")
            frame_index += 1

            try:
                gif.seek(frame_index)
            except EOFError:
                break
        
        return
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
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'}
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    gif_extension = {'.gif'}
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

def create_output_dir():
    """
    Creates the output directory for storing extracted frame images.

    This function constructs the full path for the `output_frames` directory 
    within the `output` folder at the current working directory. If the 
    directory does not exist, it is created.

    Returns:
        str: The full path to the created output directory.

    Notes:
        - If the directory already exists, no error is raised.
        - The function prints the directory path for confirmation.
    """
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
    media_file_paths = get_valid_media_files(full_path_input_dir)

    # Define and create the output directory

    full_path_output_dir = create_output_dir()

    # Run frame extraction
    for media_file_path in media_file_paths:
        print(f"\nExtracting frames from: {media_file_path}")
        extract_frames(full_path_output_dir, media_file_path)

    print("\nFrame extraction complete.")


if __name__ == "__main__":
    main_extract_frames()