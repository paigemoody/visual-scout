import os
import re
import argparse
from PIL import Image

from .video_utils import get_image_files, extract_timestamps

def create_grid(images, frame_width, frame_height, grid_dimension):
    """Create a grid image from a list of individual images."""
    grid_width = grid_dimension * frame_width
    grid_height = grid_dimension * frame_height
    grid = Image.new("RGB", (grid_width, grid_height), "white")

    for idx, img in enumerate(images):
        row, col = divmod(idx, grid_dimension)
        x, y = col * frame_width, row * frame_height
        grid.paste(img, (x, y))

    return grid

def save_grid(grid, output_directory, start_timestamp, end_timestamp):
    """Save the grid image with an appropriate filename."""
    os.makedirs(output_directory, exist_ok=True)
    output_filename = f"grid_{start_timestamp}_{end_timestamp}.jpg"
    grid.save(os.path.join(output_directory, output_filename))
    print(f"Saved grid in: {output_directory}/{output_filename}")

def process_images_in_chunks(files, input_directory, output_directory, grid_dimension):
    """Process image files in chunks of GRID_DIMENSION to create grids."""
    chunk_size = grid_dimension ** 2  # NxN grid = (grid_dimension * grid_dimension) images per grid
    for i in range(0, len(files), chunk_size):
        chunk = files[i:i + chunk_size]
        images = [Image.open(os.path.join(input_directory, file)) for file in chunk]

        frame_width, frame_height = images[0].size
        grid = create_grid(images, frame_width, frame_height, grid_dimension)

        start_timestamp, _ = extract_timestamps(chunk[0])
        _, end_timestamp = extract_timestamps(chunk[-1])

        save_grid(grid, output_directory, start_timestamp, end_timestamp)

def create_grids_from_frames(grid_dimension):
    """Processes frames from `output_frames/`, saving grids in `output_grids/{video_name}__grids/`."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up one level
    input_directory = os.path.join(base_dir, "output_frames")
    output_directory = os.path.join(base_dir, "output_grids")

    if not os.path.exists(input_directory):
        raise FileNotFoundError(f"Input directory '{input_directory}' does not exist.")

    for video_folder in os.listdir(input_directory):
        video_folder_path = os.path.join(input_directory, video_folder)
        if os.path.isdir(video_folder_path):  # Ensure it's a directory
            print(f"Processing frames from: {video_folder}")

            # Define output directory for this specific video
            video_grid_dir = os.path.join(output_directory, f"{video_folder}__grids")

            files = get_image_files(video_folder_path)
            if files:
                process_images_in_chunks(files, video_folder_path, video_grid_dir, grid_dimension)
            else:
                print(f"No image files found in '{video_folder_path}'.")

    print(f"Grids have been saved in: {output_directory}")

def main():
    """Parses command-line arguments and runs the grid generation process."""
    parser = argparse.ArgumentParser(description="Generate image grids from extracted frames.")
    parser.add_argument(
        "--grid-size",
        type=int,
        default=3,
        help="Grid dimension (NxN), default is 3x3"
    )

    args = parser.parse_args()
    create_grids_from_frames(args.grid_size)

if __name__ == "__main__":
    main()
