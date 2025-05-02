import os
from PIL import Image
from math import ceil, sqrt
from visual_scout.utils.image_utils import extract_timestamps
from visual_scout.utils.video_utils import get_image_files


def create_grid(images, frame_width, frame_height, grid_dimension):
    """
    Create a square grid image from a list of images, arranged left-to-right, top-to-bottom.

    The grid will be no larger than `grid_dimension` x `grid_dimension`, and will automatically
    shrink to the smallest square that can fit all images. If the number of images is less than
    `grid_dimension^2`, empty grid cells will be left blank (white).

    Args:
        images (list of PIL.Image): List of PIL Image objects to arrange in the grid.
        frame_width (int): Width of each individual image in the grid.
        frame_height (int): Height of each individual image in the grid.
        grid_dimension (int): Maximum number of rows and columns in the grid.

    Returns:
        PIL.Image: A composite image with the input images arranged in a square grid.
                   Empty slots are filled with white.
                   If `images` is empty, returns a single blank image of size (frame_width, frame_height).
    """
    num_images = len(images)

    # handle the case where there are no images
    if num_images == 0:
        return Image.new(
            "RGB", (frame_width, frame_height), "white"
        )  # Return 1x1 blank image

    # compute minimum square grid needed
    raw_grid_size = ceil(sqrt(num_images))
    optimal_grid_dim = min(grid_dimension, raw_grid_size)

    # create a blank (white) grid
    grid_size = (optimal_grid_dim * frame_width, optimal_grid_dim * frame_height)
    grid = Image.new("RGB", grid_size, "white")

    # arrange images in the grid
    for idx, img in enumerate(images):
        row, col = divmod(idx, optimal_grid_dim)
        x, y = col * frame_width, row * frame_height
        grid.paste(img, (x, y))

    return grid


def save_grid(grid, output_directory, start_timestamp, end_timestamp):
    """
    Save a grid image to the specified directory using a timestamp-based filename.

    The filename will follow the format: 'grid_<start_timestamp>_<end_timestamp>.jpg'.

    Args:
        grid (PIL.Image): The grid image to be saved.
        output_directory (str): Directory where the image will be saved. Created if it doesn't exist.
        start_timestamp (str): Start timestamp used in the filename.
        end_timestamp (str): End timestamp used in the filename.

    Returns:
        None. The image is saved to disk, and a confirmation message is printed.
    """
    os.makedirs(output_directory, exist_ok=True)
    output_filename = f"grid_{start_timestamp}_{end_timestamp}.jpg"
    output_path = os.path.join(output_directory, output_filename)
    grid.save(output_path)
    print(f"Saved grid in: {output_directory}/{output_filename}")
    return output_path


def process_images_in_chunks(files, input_directory, output_directory, grid_dimension):
    """
    Process a list of image files in chunks to generate and save grid images.

    Each grid contains up to `grid_dimension^2` images, arranged left-to-right, top-to-bottom.
    The function loads images from `input_directory`, creates a grid for each chunk,
    and saves the resulting grid to `output_directory` with a filename based on the
    timestamps of the first and last images in the chunk.

    Args:
        files (list of str): Filenames of images to process, ordered chronologically.
        input_directory (str): Path to the directory containing input image files.
        output_directory (str): Path to the directory where grid images will be saved.
        grid_dimension (int): Maximum number of rows/columns in each grid (e.g., 3 for a 3x3 grid).

    Returns:
        list of dict: A list of metadata dictionaries for each saved grid, containing:
            - 'path' (str): Full path to the saved grid image.
            - 'start_timestamp' (str): Timestamp from the first image in the chunk.
            - 'end_timestamp' (str): Timestamp from the last image in the chunk.
            - 'num_images' (int): Number of images used to generate the grid.
    """
    chunk_size = (
        grid_dimension**2
    )  # total number of images per grid is the square of the dimension (eg 3x3 = 9)
    saved_grids = []

    # iterate over the file list in chunks of chunk_size
    for i in range(0, len(files), chunk_size):
        chunk = files[i : i + chunk_size]

        # load all images in the current chunk
        images = []
        for file in chunk:
            image_path = os.path.join(input_directory, file)
            img = Image.open(image_path)
            images.append(img)

        # use size of the first image to define grid cell dimensions
        frame_width, frame_height = images[0].size

        # create a composite grid image from the current chunk
        grid = create_grid(images, frame_width, frame_height, grid_dimension)

        # extract timestamps from the first and last image in the chunk for filename
        first_file_in_chunk = chunk[0]
        last_file_in_chunk = chunk[-1]
        start_timestamp = extract_timestamps(first_file_in_chunk)[0]
        end_timestamp = extract_timestamps(last_file_in_chunk)[-1]

        # save the grid image and collect its path
        output_path = save_grid(grid, output_directory, start_timestamp, end_timestamp)

        # store metadata about the saved grid
        saved_grids.append(
            {
                "path": output_path,
                "start_timestamp": start_timestamp,
                "end_timestamp": end_timestamp,
                "num_images": len(chunk),
            }
        )

    return saved_grids


def create_grids_from_frames(grid_dimension, input_directory, output_directory):
    """
    Generate and save image grids from video frame folders in a given directory.

    This function scans the `input_directory` for subfolders (each representing a video),
    processes the image frames within each subfolder, and generates grid images
    using `grid_dimension` as the maximum number of rows/columns per grid.

    Grids are saved to the `output_directory`, with each video’s grids stored in a
    separate subfolder named "<video_folder_name>__grids".

    Args:
        grid_dimension (int): Maximum number of rows and columns in each grid (e.g., 3 for a 3x3 grid).
        input_directory (str): Path containing one subdirectory per video, each with extracted image frames.
        output_directory (str): Path where the generated grid images will be saved.

    Returns:
        str: The path to the output directory where grids were saved.
    """
    input_videos = os.listdir(input_directory)

    # loop through each folder inside the input directory
    for video_folder in os.listdir(input_directory):
        video_folder_path = os.path.join(input_directory, video_folder)

        # skip if the entry is not a directory
        if os.path.isdir(video_folder_path):
            print(f"\nProcessing frames from: {video_folder}")

            # Create a subfolder for storing grids related to this specific video
            video_grid_dir = os.path.join(output_directory, f"{video_folder}__grids")

            # get all image filenames (eg .jpg, .png) from the video folder
            files = get_image_files(video_folder_path)

            # only process if image files are found
            if files:
                process_images_in_chunks(
                    files, video_folder_path, video_grid_dir, grid_dimension
                )
            else:
                print(f"No image files found in '{video_folder_path}'.")

    print(f"\nGrids have been saved in: {output_directory}")
    return output_directory


def main_generate_grids(grid_size):
    """
    Main entry point for generating image grids from extracted video frames.

    This function looks for frame images in the default input directory
    ('output/output_frames'), checks that it exists and is not empty,
    and then triggers grid generation using the specified grid size.
    Grids are saved in 'output/output_grids'.

    Args:
        grid_size (int): Number of rows and columns for each grid (e.g., 3 = 3x3 grid).

    Returns:
        str: Path to the directory where grids were saved.

    Raises:
        FileNotFoundError: If the input directory is missing or contains no files.
    """
    base_dir = os.getcwd()

    # define input and output directories relative to the project root
    input_directory = os.path.join(base_dir, "output", "output_frames")
    output_directory = os.path.join(base_dir, "output", "output_grids")

    print(f"\nChecking input frames from: {input_directory}")

    # ensure input directory exists and has at least one item
    if not os.path.exists(input_directory) or not os.listdir(input_directory):
        raise FileNotFoundError(
            f"Error: Input frames directory '{input_directory}' does not exist or exists but is empty - "
            f"be sure to generate frames before generating grids."
        )

    # create the output directory if it doesn't exist
    os.makedirs(output_directory, exist_ok=True)
    print(f"\nGrids will be saved to: {output_directory}")

    # trigger the grid generation process
    return create_grids_from_frames(grid_size, input_directory, output_directory)


if __name__ == "__main__":
    main_generate_grids()
