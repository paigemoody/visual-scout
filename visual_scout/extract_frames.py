import cv2
import os
import numpy as np
from datetime import timedelta
import warnings
import shutil
from PIL import Image, UnidentifiedImageError
from concurrent.futures import ProcessPoolExecutor, as_completed
from visual_scout.utils.frame_utils import get_frame_similarity_ssim, make_frame_record, create_output_dir, create_frame_path, is_similar_frame
from visual_scout.constants import SSIM_THRESHOLDS, SAMPLING_INTERVAL
from visual_scout.utils.video_utils import open_video
from visual_scout.utils.media_utils import get_valid_media_files, get_file_type_from_extension, format_timestamps
from visual_scout.utils.image_utils import save_image_to_disk
from visual_scout.utils.gif_utils import open_gif, format_gif_timestamp



def extract_frames_from_image(output_frames_media_path, media_file, save_fn=None):
    """
    Handle static image input by returning the image and timestamp metadata.
    Optionally saves the image using the provided save function.

    Args:
        output_frames_media_path (str): Path used to construct the frame filename.
        media_file (str): Path to the input image file.
        save_fn (callable or None): Optional function to save the image.
                                    Called with (image_array, frame_path).

    Returns:
        list of dict: A single item list with:
            - 'image': The image as a numpy array
            - 'start_time': '00:00:00'
            - 'end_time': '00:00:00'
    """
    print(f"\n\nExtracting frames from image {media_file}...")

    # Standard timestamp format for a single static image
    start_time = "00:00:00"
    end_time = "00:00:00"
    frame_filename = "frame_0-00-00_0-00-00.jpg"
    frame_path = os.path.join(output_frames_media_path, frame_filename)

    # Load image and convert to array
    image = Image.open(media_file).convert("RGB")
    image_array = np.array(image)

    # Save the frame if a save_fn is provided
    if save_fn:
        save_fn(image_array, frame_path)

    print(
        f"Saved image as frame: {frame_path}"
        if save_fn
        else "Image processed but not saved."
    )

    frame_record= make_frame_record(image_array, start_time, end_time)

    return [frame_record]


def extract_frames_from_video(
    output_frames_media_path,
    media_file,
    ssmi_threshold,
    use_static_sample_rate,
    save_fn=None,
):
    """
    Extract frames from a video file and return them with their time metadata.

    Frames are sampled at fixed intervals (defined by SAMPLING_INTERVAL). If
    `use_static_sample_rate` is False, frames are only collected if they differ
    from the last saved frame using SSIM comparison.

    Args:
        output_frames_media_path (str): Path used for filename generation (regardless of save location).
        media_file (str): Path to the input video file.
        ssmi_threshold (float): SSIM threshold to determine whether frames are visually different.
        use_static_sample_rate (bool): If True, save every sampled frame. If False, skip similar ones.
        save_fn (callable or None): Optional function to save frames. Called with (frame, frame_path).
                                    If None, frames are not saved to disk or elsewhere.

    Returns:
        list of dict: Each item contains:
            - 'image': The frame (as a numpy array)
            - 'start_time': Timestamp for frame start (HH:MM:SS string)
            - 'end_time': Timestamp for frame end (HH:MM:SS string)
    """
    print(f"\n\nExtracting frames from video {media_file}...")

    cap = open_video(media_file)

    collected_frames = []
    saved_frames = 0

    if cap:
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps

        print(f"Video FPS: {fps}")
        print(f"Total Frames: {frame_count}")
        print(f"Video Duration: {timedelta(seconds=duration)}")

        sampling_interval = SAMPLING_INTERVAL  # Seconds between samples
        frame_interval = round(fps * sampling_interval)  # Frames between samples

        print(f"Extracting frames every {sampling_interval} seconds")

        frame_index = 0
        most_recently_saved_frame = (None, None)  # (path, image)

        while frame_index < frame_count:
            print(f"\n\nProcessing frame {frame_index} / {frame_count}")

            # Prevent out-of-bounds frame index
            target_frame_index = min(frame_index, frame_count - 1)
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame_index)
            ret, frame = cap.read()

            if not ret:
                print(
                    f"Warning: Could not read frame at index {frame_index}. Skipping..."
                )
                break

            # Generate readable timestamps for file naming and metadata
            timestamp = round(frame_index / fps, 2)
            start_time, end_time = format_timestamps(timestamp)
            frame_path = create_frame_path(output_frames_media_path, start_time, end_time)

            # Optionally skip similar frames based on SSIM
            new_frame_similar_to_previous_frame = is_similar_frame(
                most_recently_saved_frame[1], frame, ssmi_threshold, use_static_sample_rate
            )

            # Save and collect the frame if it's different or we're using static sampling
            if (
                most_recently_saved_frame[1] is None
                or not new_frame_similar_to_previous_frame
            ):
                if save_fn:
                    save_fn(frame, frame_path)

                saved_frames += 1
                most_recently_saved_frame = (frame_path, frame)

                frame_record = make_frame_record(frame, start_time, end_time)
                collected_frames.append(
                    frame_record
                )
            else:
                print(f"\nSkipping {frame_path} (sufficiently similar to previous frame)")

            frame_index += frame_interval

        cap.release()

    if save_fn:
        if saved_frames == 0:
            os.rmdir(output_frames_media_path)
            print(f"Removed empty output directory: {output_frames_media_path}")
        else:
            print(f"Frames saved: {saved_frames} in {output_frames_media_path}")

    return collected_frames


def extract_frames_from_gif(
    output_frames_media_path,
    media_file,
    ssmi_threshold,
    use_static_sample_rate,
    save_fn=None,
):
    """
    Extracts frames from an animated GIF at regular intervals, optionally skipping similar frames.

    Frames are converted to RGB and returned as a list of image objects with associated timestamps.
    If `save_fn` is provided, each qualifying frame is also saved using that function.

    Args:
        output_frames_media_path (str): Base path for naming saved frames (even if not saving locally).
        media_file (str): Path to the input GIF file.
        ssmi_threshold (float): SSIM threshold for frame similarity.
        use_static_sample_rate (bool): If True, extract every Nth frame. If False, skip similar ones.
        save_fn (callable or None): Optional save function called with (frame_array, frame_path).

    Returns:
        list of dict: Each item contains:
            - 'image': The frame (as a numpy array)
            - 'start_time': Timestamp for frame (HH:MM:SS string)
            - 'end_time': Same as start_time for consistency
    """
    print(f"\n\nExtracting frames from animated GIF: {media_file}...")

    gif = open_gif(media_file)  # returns a PIL.Image object
    if not gif:
        return []

    frame_index = 0
    frames_saved = 0
    collected_frames = []
    most_recently_saved_frame = (None, None)  # (path, frame_array)

    while True:
        try:
            # move to the current frame in the GIF
            gif.seek(frame_index)
        except EOFError:
            # no more frames to process
            break

        # only sample every Nth frame based on configured interval
        should_sample = frame_index % SAMPLING_INTERVAL == 0
        if should_sample:
            # convert palette-based GIF frame to RGB so we can save as JPEG
            current_frame_image = gif.convert("RGB")
            current_frame_array = np.array(current_frame_image)

            # determine whether this frame is similar to the last one we saved
            is_similar = False
            if not use_static_sample_rate:
                is_similar = get_frame_similarity_ssim(
                    most_recently_saved_frame[1], current_frame_array, ssmi_threshold
                )

            # save this frame if it's different enough or if we are saving all sampled frames
            if most_recently_saved_frame[1] is None or not is_similar:
                # format start and end time (GIF frames use the same value for both)
                start_time, end_time = format_gif_timestamp(frame_index)
                frame_path = create_frame_path(output_frames_media_path, start_time, end_time)

                # save frame to disk if a save function is provided
                if save_fn:
                    save_fn(current_frame_array, frame_path)

                # create and store metadata record for this frame
                frame_record = make_frame_record(current_frame_array, start_time, end_time)
                collected_frames.append(frame_record)

                # track the last saved frame
                most_recently_saved_frame = (frame_path, current_frame_array)
                frames_saved += 1
                print(f"Saved: {frame_path}")
            else:
                print(f"\nSKIPPING frame {frame_index} (too similar to previous)")

        # move to the next frame in the GIF
        frame_index += 1

    print(f"\nTotal frames collected from {media_file}: {len(collected_frames)}")
    return collected_frames


def extract_frames(
    output_frames_base_path, media_file, ssmi_threshold, use_static_sample_rate
):
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
    output_frames_media_path = os.path.join(
        output_frames_base_path, f"{name_without_ext}__frames"
    )
    os.makedirs(output_frames_media_path, exist_ok=True)

    file_type = get_file_type_from_extension(media_file)

    if file_type == "image":
        total_saved_frames = extract_frames_from_image(
            output_frames_media_path, media_file, save_image_to_disk
        )
        return total_saved_frames

    elif file_type == "video":
        total_saved_frames = extract_frames_from_video(
            output_frames_media_path,
            media_file,
            ssmi_threshold,
            use_static_sample_rate,
            save_image_to_disk,
        )
        return total_saved_frames

    elif file_type == "gif":
        total_saved_frames = extract_frames_from_gif(
            output_frames_media_path,
            media_file,
            ssmi_threshold,
            use_static_sample_rate,
            save_image_to_disk,
        )
        return total_saved_frames

    else:
        raise ValueError(f"Unsupported file type: {media_file}")








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
            executor.submit(
                extract_frames,
                full_path_output_dir,
                media_file_path,
                ssmi_threshold,
                use_static_sample_rate,
            ): media_file_path
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
