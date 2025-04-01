import cv2
import numpy as np
import os
import shutil
from glob import glob
import matplotlib.pyplot as plt
from skimage.metrics import structural_similarity as compare_ssim


# SIMILARITY_METRIC Options: "correlation", "chi-square", "bhattacharyya"
SIMILARITY_METRIC = "correlation"
# SIMILARITY_METRIC = "chi-square"
# SIMILARITY_METRIC = "bhattacharyya"

# Auto-set threshold based on metric type
# Threshold tuning


DEFAULT_THRESHOLDS = {
    "correlation": 0.7,       # higher = more similar
    "chi-square": 100,        # lower = more similar
    "bhattacharyya": 0.2      # lower = more similar
}
THRESHOLD = DEFAULT_THRESHOLDS[SIMILARITY_METRIC]

def load_frame(frame_path):
    color_frame = cv2.imread(frame_path)
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

def get_frame_similarity(frame_1_full_path, frame_2_full_path, threshold):
    print(f"\n\nComparing {frame_1_full_path.split('/')[-1]} and {frame_2_full_path.split('/')[-1]} using SSIM with threshold {threshold}")

    color_frame_1, gray_frame_1 = load_frame(frame_1_full_path)
    color_frame_2, gray_frame_2 = load_frame(frame_2_full_path)

    # Compute the SSIM between the two grayscale frames
    ssim_index, ssim_map = compare_ssim(gray_frame_1, gray_frame_2, full=True)
    print(f"SSIM Index: {ssim_index}")

    # optional - visualize map
    # plt.figure(figsize=(6, 6))
    # plt.imshow(ssim_map, cmap='jet', vmin=-1, vmax=1)  # 'jet' colormap for better visibility
    # plt.colorbar(label='SSIM Value')
    # plt.title("SSIM Map")
    # plt.show()

    # If SSIM is close to 1, the images are similar. Adjust the threshold as needed.
    if ssim_index >= threshold:
        print(f"Frames are sufficiently similar (SSIM >= {threshold})")
        return True
    else:
        print(f"Frames are sufficiently different (SSIM < {threshold})")
        return False

if __name__ == "__main__":

    SSIM_threshold = 0.5
    comparisons_horizonatal_video_example = [
        ["/Users/paigemoody/Projects/visual-scout/output/output_frames/example_video_horizontal__frames/frame_0-00-00_0-00-02.jpg", "/Users/paigemoody/Projects/visual-scout/output/output_frames/example_video_horizontal__frames/frame_0-00-02_0-00-04.jpg", True], 
        ["/Users/paigemoody/Projects/visual-scout/output/output_frames/example_video_horizontal__frames/frame_0-00-04_0-00-06.jpg", "/Users/paigemoody/Projects/visual-scout/output/output_frames/example_video_horizontal__frames/frame_0-00-06_0-00-08.jpg", True],
        ["/Users/paigemoody/Projects/visual-scout/output/output_frames/example_video_horizontal__frames/frame_0-00-06_0-00-08.jpg", "/Users/paigemoody/Projects/visual-scout/output/output_frames/example_video_horizontal__frames/frame_0-00-08_0-00-10.jpg", False]
    ]

    comparisons_bet_gif = [
        ["/Users/paigemoody/Projects/visual-scout/output/output_frames/example_gif__frames/frame_00-00-00_00-00-00.jpg", "/Users/paigemoody/Projects/visual-scout/output/output_frames/example_gif__frames/frame_00-00-08_00-00-08.jpg", True]
    ]

    comparisons_football_4x4_video = [
        ["/Users/paigemoody/Projects/visual-scout/output/output_frames/2059891-short-football-4x4_20240924-122302_14231870__frames/frame_0-00-00_0-00-02.jpg", "/Users/paigemoody/Projects/visual-scout/output/output_frames/2059891-short-football-4x4_20240924-122302_14231870__frames/frame_0-00-02_0-00-04.jpg" , False],
        ["/Users/paigemoody/Projects/visual-scout/output/output_frames/2059891-short-football-4x4_20240924-122302_14231870__frames/frame_0-00-14_0-00-16.jpg", "/Users/paigemoody/Projects/visual-scout/output/output_frames/2059891-short-football-4x4_20240924-122302_14231870__frames/frame_0-00-16_0-00-18.jpg", False],
        ["/Users/paigemoody/Projects/visual-scout/output/output_frames/2059891-short-football-4x4_20240924-122302_14231870__frames/frame_0-00-36_0-00-38.jpg", "/Users/paigemoody/Projects/visual-scout/output/output_frames/2059891-short-football-4x4_20240924-122302_14231870__frames/frame_0-00-38_0-00-40.jpg", True],
    ]

    SSIM_threshold = 0.5

    full_path_output_dir = os.path.join(os.getcwd(), "output", "output_frames_smart")
    print(f"\nMaking directory {full_path_output_dir} to store frame image files")
    os.makedirs(full_path_output_dir, exist_ok=True)

    # testing---
    # base_path_example = "/Users/paigemoody/Projects/visual-scout/output/output_frames/example_video_vertical__frames/"
    # base_path_example = "/Users/paigemoody/Projects/visual-scout/output/output_frames/2059891-short-football-4x4_20240924-122302_14231870__frames"
    
    base_path_example = "/Users/paigemoody/Projects/visual-scout/output/output_frames/2055922-short-football-3x3_20240924-095650_14230901__frames"
    output_frames_media_path = os.path.join(full_path_output_dir, f"2055922-short-football-3x3_20240924-095650_14230901__frames")
    # end testing alterations section---
    
    os.makedirs(output_frames_media_path, exist_ok=True)

    example_files_list = os.listdir(base_path_example)
    example_files_list.sort()

    file_1 = example_files_list[0]
    
    for file_2 in example_files_list[1:]:
        full_path_file_1 = os.path.join(base_path_example, file_1) 
        full_path_file_2 = os.path.join(base_path_example, file_2)

        file_2_similar_to_file_1 = get_frame_similarity(full_path_file_1, full_path_file_2, SSIM_threshold)

        print("file_2_similar_to_file_1?", file_2_similar_to_file_1)

        if not file_2_similar_to_file_1:
            print(f"keeping {file_2}")
            file_1 = file_2
            output_frame_path = os.path.join(output_frames_media_path, file_2)
            shutil.copy(full_path_file_2, output_frame_path)
            print(f"Saved image as frame: {output_frame_path}")
        else:
            print(f"discarding {file_2}")

        
        