import subprocess
import os

def get_video_duration(video_path):
    """Extract the duration of a video file using ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ],
        capture_output=True, text=True
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0

def estimate_processing_cost(input_dir, model):
    """Estimate processing cost based on video durations and image counts."""
    total_length = 0
    cost_per_image = None

    assert model in ["4o", "4o-mini"], f"Invlaid model {model} - must be either 4o or 4o-mini."
    if model == "4o": 
        cost_per_image = 0.005
    elif model == "4o-mini":
        cost_per_image = 0.0003

    # Process all videos (including GIFs)
    for file in os.listdir(input_dir):
        if file.lower().endswith((".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv", ".gif")):
            video_path = os.path.join(input_dir, file)
            total_length += get_video_duration(video_path)
    
    # Count standalone images
    image_count = len([f for f in os.listdir(input_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))])
    
    # Compute cost (no rounding applied)
    frames_per_video = total_length / 2
    grids = frames_per_video / 9
    total_images = (grids * 9) + image_count
    total_cost = total_images * cost_per_image
    
    # Output results
    print(f"Total video duration: {total_length:.2f} seconds")
    print(f"Standalone images in directory: {image_count}")
    print(f"Estimated total images processed: {int(total_images)}")
    print(f"Estimated processing cost for {model}: ${total_cost:.6f}")

