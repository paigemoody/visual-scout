import cv2
import numpy as np
import os
import shutil
from glob import glob
from skimage.metrics import structural_similarity as compare_ssim


def make_frame_record(image, start_time, end_time):
    return {
        "image": image,
        "start_time": start_time,
        "end_time": end_time
    }

def create_frame_path(output_dir, start_time, end_time):
    """
    Create a standardized frame path using start/end timestamps.
    Replaces colons to ensure cross-platform safe filenames.
    """
    filename = f"frame_{start_time.replace(':', '-')}_{end_time.replace(':', '-')}.jpg"
    return os.path.join(output_dir, filename)


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

def load_frame(color_frame):
    gray_frame = cv2.cvtColor(color_frame, cv2.COLOR_BGR2GRAY)
    return color_frame, gray_frame

def compute_histogram_difference(img1, img2, metric):
    hist1 = cv2.calcHist([img1], [0], None, [256], [0, 256])
    hist2 = cv2.calcHist([img2], [0], None, [256], [0, 256])

    if metric == "correlation":
        return cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
    elif metric == "chi-square":
        return cv2.compareHist(hist1, hist2, cv2.HISTCMP_CHISQR)
    elif metric == "bhattacharyya":
        return cv2.compareHist(hist1, hist2, cv2.HISTCMP_BHATTACHARYYA)
    else:
        raise ValueError("Invalid similarity metric selected.")


def compare_frames_histogram_diff(
    frame_1_full_path, frame_2_full_path, similarity_metric, threshold
):

    print(
        f"\n\nComparing {frame_1_full_path.split("/")[-1]} and {frame_2_full_path.split("/")[-1]} using {similarity_metric} with threshold {threshold}"
    )

    color_frame_1, gray_frame_1 = load_frame(frame_1_full_path)
    color_frame_2, gray_frame_2 = load_frame(frame_2_full_path)

    diff = compute_histogram_difference(gray_frame_1, gray_frame_2, similarity_metric)
    print(f"diff: {diff}")

    within_similarity_range = (
        similarity_metric == "correlation" and diff < threshold
    ) or (similarity_metric in ["chi-square", "bhattacharyya"] and diff > threshold)

    if within_similarity_range:
        # keep previous frame
        print(f"\nWithin similarity range")
        return True

    else:
        print(f"\nSufficiently different frames")
        return False


def get_frame_similarity_ssim(frame_1, frame_2, threshold):

    if (frame_1 is None) or (frame_2 is None):
        print("Comparison requires two frames!")
        return False

    color_frame_1, gray_frame_1 = load_frame(frame_1)
    color_frame_2, gray_frame_2 = load_frame(frame_2)

    # Compute the SSIM between the two grayscale frames
    # TODO remove full=True - when we don't need the full ssmi image returned
    ssim_index, ssim_map = compare_ssim(gray_frame_1, gray_frame_2, full=True)
    print(f"SSIM Index: {ssim_index}")

    # If SSIM is close to 1, the images are similar. Adjust the threshold as needed.
    if ssim_index >= threshold:
        print(f"Frames are sufficiently similar (SSIM >= {threshold})")
        return True
    else:
        print(f"Frames are sufficiently different (SSIM < {threshold})")
        return False

def is_similar_frame(previous_frame, current_frame, threshold, use_static_sample_rate):
    """
    Determine if the current frame is visually similar to the previous one using SSIM.

    Args:
        previous_frame (np.ndarray or None): The previously saved frame.
        current_frame (np.ndarray): The frame being considered.
        threshold (float): SSIM threshold for similarity.
        use_static_sample_rate (bool): If True, bypass similarity checking.

    Returns:
        bool: True if frames are similar (and should be skipped), False otherwise.
    """
    if use_static_sample_rate or previous_frame is None:
        return False
    return get_frame_similarity_ssim(previous_frame, current_frame, threshold)