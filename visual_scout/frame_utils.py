import cv2
import numpy as np
import os
import shutil
from glob import glob
from skimage.metrics import structural_similarity as compare_ssim


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

def compare_frames_histogram_diff(frame_1_full_path, frame_2_full_path, similarity_metric, threshold):

    print(f"\n\nComparing {frame_1_full_path.split("/")[-1]} and {frame_2_full_path.split("/")[-1]} using {similarity_metric} with threshold {threshold}")

    color_frame_1, gray_frame_1 = load_frame(frame_1_full_path)
    color_frame_2, gray_frame_2 = load_frame(frame_2_full_path)

    diff = compute_histogram_difference(gray_frame_1, gray_frame_2, similarity_metric)
    print(f"diff: {diff}")

    within_similarity_range = (similarity_metric == "correlation" and diff < threshold) or (similarity_metric in ["chi-square", "bhattacharyya"] and diff > threshold)

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
  