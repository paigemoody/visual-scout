import cv2
import os
import numpy as np
from datetime import timedelta
import warnings
import shutil
from PIL import Image, UnidentifiedImageError
from concurrent.futures import ProcessPoolExecutor, as_completed
from visual_scout.frame_utils import get_frame_similarity_ssim
from visual_scout.constants import SSIM_THRESHOLDS, SAMPLING_INTERVAL


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
        warning_message = f"\n\n[FileNotFoundWarning] Video file not found: {video_full_path}"
        raise FileNotFoundError(warning_message)

    try:
        cap = cv2.VideoCapture(video_full_path)
        if not cap.isOpened():
            warning_message = f"\n\n[InvalidVideoWarning] Unable to open video file: {video_full_path}. Skipping..."
            warnings.warn(warning_message)
            return False
        return cap

    except cv2.error as e:
        print("sending warning now!!")
        warnings.warn(f"\n\n[OpenCVIssueWarning] OpenCV encountered an error while opening video {video_full_path}: {str(e)}") 
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


def get_file_type_from_extension(media_file):
    # Determine if input is a video, animated GIF, or static image
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'}
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    gif_extensions = {'.gif'}
    extension = os.path.splitext(media_file)[1].lower()

    if extension in video_extensions:
        return "video"
    elif extension in image_extensions:
        return "image"
    elif extension in gif_extensions:
        return "gif"  
    else:
        raise ValueError(f"Unsupported file type: {media_file}")


def extract_frames_from_image(output_frames_media_path, media_file):
    # TO DO: return frame object
    """
    Handle static image input by saving it as a single frame in the expected format.

    This function is used when the input media is a single image rather than a video.
    It copies the image to the target output directory using a standardized frame filename 
    to ensure consistency with how video frames are stored.

    Args:
        output_frames_media_path (str): Directory where the frame should be saved.
        media_file (str): Path to the input image file.

    Returns:
        int: Number of frames saved (always 1 for static images).
    """
    # Log the image being processed
    print(f"\n\nExtracting frames from image {media_file}...")

    # Define standard frame filename (matches video frame naming pattern)
    frame_filename = "frame_0-00-00_0-00-00.jpg"
    frame_path = os.path.join(output_frames_media_path, frame_filename)

    # Copy the static image to the output location
    shutil.copy(media_file, frame_path)
    print(f"Saved image as frame: {frame_path}")

    return 1  # Total frames saved



def extract_frames_from_video(output_frames_media_path, media_file, ssmi_threshold, use_static_sample_rate):
    """
    Extracts frames from a video file at regular intervals, with optional similarity-based filtering.

    This function processes a video by sampling frames every N seconds (defined by `SAMPLING_INTERVAL`).
    If `use_static_sample_rate` is False, frames are only saved if they differ significantly from the 
    previously saved frame, using SSIM (Structural Similarity Index) comparison.

    Args:
        output_frames_media_path (str): Directory where extracted frames will be saved.
        media_file (str): Path to the input video file.
        ssmi_threshold (float): SSIM threshold below which frames are considered different enough to save.
        use_static_sample_rate (bool): If True, saves every sampled frame; if False, only saves visually distinct frames.

    Returns:
        int: The number of frames successfully saved.
    """
    print(f"\n\nExtracting frames from video {media_file}...")
    
    saved_frames = 0

    cap = open_video(media_file)
    if cap:
        # get basic video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps

        print(f"Video FPS: {fps}")
        print(f"Total Frames: {frame_count}")
        print(f"Video Duration: {timedelta(seconds=duration)}")

        # Determine how often to sample frames (e.g., every 2 seconds)
        # TODO: pass sampling interval in to fn, rather than use global
        sampling_interval = SAMPLING_INTERVAL
        frame_interval = round(fps * SAMPLING_INTERVAL)  # Convert seconds to frame count

        print(f"Extracting frames every {sampling_interval} seconds")

        frame_index = 0
        most_recently_saved_frame = (None, None)  # (frame_path, frame_image)

        # iterate through video by jumping in intervals
        while frame_index < frame_count:
            print(f"\n\nProcessing frame {frame_index} / {frame_count}")
            # ensure we don’t request a frame index beyond the last valid frame
            target_frame_index = min(frame_index, frame_count - 1)
            # move the video cursor to the target frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame_index)
            # attempt to read the frame at the current position
            ret, frame = cap.read()
            
            if not ret:
                print(f"Warning: Could not read frame at index {frame_index}. Skipping...")
                break

            

            # Determine whether to skip this frame based on similarity (if enabled)
            new_frame_similar_to_previous_frame = False
            if not use_static_sample_rate:
                new_frame_similar_to_previous_frame = get_frame_similarity_ssim(
                    most_recently_saved_frame[1], frame, ssmi_threshold
                )

            # generate readable timestamp-based filename

            # calculate the timestamp (in seconds) for the current frame
            timestamp = round(frame_index / fps, 2)

            # format the start time of the frame (e.g., '0:00:10') as a string
            start_time = str(timedelta(seconds=int(timestamp)))

            # calculate and format the end time based on the sampling interval
            end_time = str(timedelta(seconds=int(timestamp + SAMPLING_INTERVAL)))

            # generate a filename using the start and end times, replacing colons with dashes
            # eg: "frame_0-00-10_0-00-12.jpg"
            frame_filename = f"frame_{start_time.replace(':', '-')}_{end_time.replace(':', '-')}.jpg"

            # build the full path where the frame image will be saved
            frame_path = os.path.join(output_frames_media_path, frame_filename)

            # Save frame if it's different enough or static sampling is used
            if most_recently_saved_frame is None or not new_frame_similar_to_previous_frame:
                if cv2.imwrite(frame_path, frame):
                    print(f"Saved: {frame_path}")
                    saved_frames += 1
                    most_recently_saved_frame = (frame_path, frame)
                else:
                    warnings.warn(f"Error saving: {frame_filename}")
            else:
                print(f"\nSKIPPING {frame_path} (too similar to previous frame)")

            # Advance to the next sampling point
            frame_index += frame_interval
            if frame_index >= frame_count:
                break

        cap.release()

    # Cleanup: remove empty output dir if no frames saved
    if saved_frames == 0:
        os.rmdir(output_frames_media_path)
        print(f"Removed empty output directory: {output_frames_media_path}")
    else:
        print(f"Frames saved: {saved_frames} in {output_frames_media_path}")

    return saved_frames



def extract_frames_from_gif(output_frames_media_path, media_file, ssmi_threshold, use_static_sample_rate):
    """
    Extracts every nth frame (based on SAMPLING_INTERVAL) from an animated GIF 
    and saves them as JPEG images with timestamp-style filenames.

    Args:
        output_frames_media_path (str): Directory path to save extracted frames.
        media_file (str): Path to the input GIF file.

    Returns:
        int: The number of frames saved.
    """
    # TODO - Right now this grabs every other frame (based on SAMPLING_INTERVAL).
    # This is probably overkill — consider making it smarter based on actual frame content.
    
    print(f"\n\nExtracting frames from animated GIF: {media_file}...")
    
    # Open the GIF using a helper function that returns a PIL Image object
    gif = open_gif(media_file)
    
    frame_index = 0        # Keeps track of current frame position
    frames_saved = 0       # Counter for how many frames are actually saved
    most_recently_saved_frame = (None, None)

    while True:
        try:
            # Seek to the correct frame and convert to RGB before saving as JPEG
            gif.seek(frame_index)
        except EOFError:
            # No more frames to read — break out of loop
            break

        # Format the frame index into a timestamp-style string like "00-00-03"
        # Note: This assumes fewer than 100 frames for consistent filename format
        if frame_index <= 9:
            frame_index_formatted = f"0{str(frame_index)}"
        else:
            frame_index_formatted = str(frame_index)
        
        frame_filename = f"frame_00-00-{frame_index_formatted}_00-00-{frame_index_formatted}.jpg"
        frame_path = os.path.join(output_frames_media_path, frame_filename)
        
        # Evaluate frame similarity only if it's the first frame or an nth frame
        is_even_or_zero = frame_index % SAMPLING_INTERVAL == 0
        if is_even_or_zero:
            """Note: GIF frames are usually stored in P (palette-based) mode — 
            a limited 256-color indexed format used for small file sizes. 
            jpeg does not support P mode — it requires images to be in RGB or grayscale."""
            current_frame_image = gif.convert("RGB")
            current_frame_array = np.array(current_frame_image)
            # Compare to previous saved frame. If using static sample rate, skip comparison
            is_similar = False
            if not use_static_sample_rate:
                is_similar = get_frame_similarity_ssim(
                    most_recently_saved_frame[1], current_frame_array,ssmi_threshold
                )
            if not is_similar:
                current_frame_image.save(frame_path)
                most_recently_saved_frame = (frame_path, current_frame_array)
                frames_saved += 1
                print(f"Saved: {frame_path}")
            else:
                print(f"\nSKIPPING {frame_path}")
        
        # always increment frame index
        frame_index += 1

    return frames_saved


def extract_frames(output_frames_base_path, media_file, ssmi_threshold, use_static_sample_rate):
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
    
    file_type = get_file_type_from_extension(media_file)
    
    if file_type == "image":
        total_saved_frames = extract_frames_from_image(output_frames_media_path, media_file)
        return total_saved_frames
    
    elif file_type == "video":
        total_saved_frames = extract_frames_from_video(output_frames_media_path, media_file, ssmi_threshold, use_static_sample_rate)
        return total_saved_frames
    
    elif file_type == "gif":
        total_saved_frames = extract_frames_from_gif(output_frames_media_path, media_file, ssmi_threshold, use_static_sample_rate)
        return total_saved_frames
    
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


def main_extract_frames(input_dir, similarity, use_static_sample_rate=False):
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

    ssmi_threshold = SSIM_THRESHOLDS[similarity]


    # Run frame extraction in parallel
    with ProcessPoolExecutor(max_workers=3) as executor:
        # Submit all jobs to the executor
        futures = {
            executor.submit(extract_frames, full_path_output_dir, media_file_path, ssmi_threshold, use_static_sample_rate): media_file_path
            for media_file_path in media_file_paths
        }

        # Monitor completion
        for future in as_completed(futures):
            media_file = futures[future]
            try:
                future.result()
                print(f"✅ Done: {media_file}")
            except Exception as e:
                print(f"❌ Failed: {media_file} — {e}")

    print("\nFrame extraction complete.")


if __name__ == "__main__":
    main_extract_frames()