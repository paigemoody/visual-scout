import os
from PIL import Image
from visual_scout.image_utils import extract_timestamps
from visual_scout.video_utils import get_image_files

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
    """Process image files in chunks of grid_dimension to create grids."""
    chunk_size = grid_dimension ** 2  # NxN grid = (grid_dimension * grid_dimension) images per grid
    for i in range(0, len(files), chunk_size):
        chunk = files[i:i + chunk_size]
        images = [Image.open(os.path.join(input_directory, file)) for file in chunk]

        frame_width, frame_height = images[0].size
        grid = create_grid(images, frame_width, frame_height, grid_dimension)

        first_file_in_chunk = chunk[0]
        last_file_in_chunk = chunk[-1]
        first_file_in_chunk_timestamps = extract_timestamps(first_file_in_chunk)
        last_file_in_chunk_timestamps = extract_timestamps(last_file_in_chunk)

        start_timestamp = first_file_in_chunk_timestamps[0]
        end_timestamp = last_file_in_chunk_timestamps[-1]

        save_grid(grid, output_directory, start_timestamp, end_timestamp)

def create_grids_from_frames(grid_dimension, input_directory, output_directory):
    """Processes frames from given input location"""

    print(f"input_directory:{input_directory}")

    input_videos = os.listdir(input_directory)

    print(f"input_videos: {input_videos}")
    for video_folder in os.listdir(input_directory):
        video_folder_path = os.path.join(input_directory, video_folder)
        if os.path.isdir(video_folder_path):  # Ensure it's a directory
            print(f"\nProcessing frames from: {video_folder}")

            # Define output directory for this specific video
            video_grid_dir = os.path.join(output_directory, f"{video_folder}__grids")

            files = get_image_files(video_folder_path)
            if files:
                process_images_in_chunks(files, video_folder_path, video_grid_dir, grid_dimension)
            else:
                print(f"No image files found in '{video_folder_path}'.")

    print(f"\nGrids have been saved in: {output_directory}")
    return output_directory


def main_generate_grids(grid_size):
    base_dir = os.getcwd()
    
    # Define input and output directories
    input_directory = os.path.join(base_dir, "output", "output_frames")
    output_directory = os.path.join(base_dir, "output", "output_grids")
    
    print(f"\nChecking input frames from: {input_directory}")

    # Ensure input directory exists and is not empty
    if not os.path.exists(input_directory) or not os.listdir(input_directory):
        raise FileNotFoundError(f"❌ Error: Input frames directory '{input_directory}' does not exist or exists but is empty - be sure to generate frames before generating grids.")

    # Create output directory to hold grids
    os.makedirs(output_directory, exist_ok=True)
    print(f"\nGrids will be saved to: {output_directory}")

    # Proceed with grid generation
    create_grids_from_frames(grid_size, input_directory, output_directory)


if __name__ == "__main__":
    main_generate_grids()
