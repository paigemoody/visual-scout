import unittest
import os
from PIL import Image
from math import ceil, sqrt
import tempfile
from visual_scout.generate_grids import (
    create_grid,
    save_grid,
    process_images_in_chunks,
    create_grids_from_frames
)


class TestGridProcessing(unittest.TestCase):
    
    def setUp(self):
        """Set up a temporary directory and load fixture images."""
        self.fixture_dir = os.path.join(os.path.dirname(__file__), "fixtures", "output" ,"example_output_frames")

        # Create a temporary directory for output
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = os.path.join(self.temp_dir.name, "temp_grid_output")
        os.makedirs(self.output_dir, exist_ok=True)

        # Use images from fixture directory
        self.video_frames_dir = os.path.join(self.fixture_dir, "example_video_horizontal_frames")
        self.sample_images = sorted([
            os.path.join(self.video_frames_dir, f) for f in os.listdir(self.video_frames_dir)
            if f.endswith(".jpg")
        ])

    def tearDown(self):
        """Automatically clean up temporary directory after each test."""
        self.temp_dir.cleanup()
        print(f"Deleted temporary test directory: {self.temp_dir.name}")


    def test_create_grid_variable_sizes(self):
        """Test that create_grid works for different grid dimensions (2x2, 3x3)."""
        for grid_size in [2, 3]:  # Test 2x2 and 3x3 grids
            with self.subTest(grid_size=grid_size):
                num_images = grid_size ** 2
                images = [Image.open(img) for img in self.sample_images[:num_images]]

                frame_width, frame_height = images[0].size
                grid = create_grid(images, frame_width, frame_height, grid_size)

                expected_size = (frame_width * grid_size, frame_height * grid_size)
                self.assertEqual(grid.size, expected_size, f"Grid should be {expected_size} but got {grid.size}.")

    def test_save_grid(self):
        """Test that save_grid correctly saves a grid using real fixture images."""
        grid = Image.new("RGB", (300, 300), "white")
        save_grid(grid, self.output_dir, "00-00-00", "00-00-02")

        expected_filename = os.path.join(self.output_dir, "grid_00-00-00_00-00-02.jpg")
        self.assertTrue(os.path.exists(expected_filename), "Saved grid image should exist in the output directory.")

    def test_process_images_in_chunks_variable_sizes(self):
        """Test that process_images_in_chunks correctly processes fixture images and produces the expected number of grids."""
        for grid_size in [2, 3]:
            with self.subTest(grid_size=grid_size):
                print(f"grid_size: {grid_size}")
                chunk_size = grid_size ** 2  # Number of images per grid
                num_input_files = len(self.sample_images)
                print(f"expecting 14 input files, found {num_input_files}")
                expected_num_grids = (num_input_files + chunk_size - 1) // chunk_size  # Round up since we also grid any remainder
                print(f"expected_num_grids: {expected_num_grids}")

                output_dir = os.path.join(self.output_dir, f"grid_{grid_size}x{grid_size}")
                print(f"output_dir: {output_dir}")
                os.makedirs(output_dir, exist_ok=True)

                process_images_in_chunks(
                    self.sample_images,
                    self.video_frames_dir,
                    output_dir,
                    grid_size
                )

                output_files = os.listdir(output_dir)
                print(f"output files: {output_files}")
                self.assertEqual(len(output_files), expected_num_grids, 
                                    f"Expected {expected_num_grids} grid images for {grid_size}x{grid_size}, but found {len(output_files)}.")

    def run__create_grids_from_frames(self, grid_size):
        """
        Little helper to utilize setup and teardown between tests of various grid sizes
        """
        print(f"grid_size: {grid_size}")
        output_path = create_grids_from_frames(grid_size, self.fixture_dir, self.output_dir)

        # make sure output directory is created
        self.assertTrue(
            os.path.exists(self.output_dir),
            f"Output directory should be created for grid size {grid_size}."
        )

        # Check if grids were created in subdirectories for each video
        for video_folder in os.listdir(self.fixture_dir):
            video_output_subdir = os.path.join(self.output_dir, f"{video_folder}__grids")

            if os.path.isdir(os.path.join(self.fixture_dir, video_folder)):
                print(f"video_output_subdir: {video_output_subdir}")
                self.assertTrue(
                    os.path.exists(video_output_subdir),
                    f"Grid directory should be created for {video_folder}."
                )

                # Count input frames and expected output grids
                frame_files = os.listdir(os.path.join(self.fixture_dir, video_folder))
                expected_output_grids = ceil(len(frame_files) / (grid_size ** 2))

                output_grids = os.listdir(video_output_subdir)

                self.assertEqual(
                    len(output_grids), expected_output_grids,
                    f"Expected {expected_output_grids} grid images for {video_folder} with grid_size {grid_size}, found {len(output_grids)}."
                )

    def test_create_grids_from_frames__2x2(self): 
        self.run__create_grids_from_frames(2)

    def test_create_grids_from_frames__3x3(self):
        self.run__create_grids_from_frames(3)


class TestCreateGrid(unittest.TestCase):
    def setUp(self):
        """Set up test images of fixed size."""
        self.frame_width = 100
        self.frame_height = 100
        self.max_grid_dim = 3  # Max grid dimension (3x3)

        # Generate test images (solid black squares)
        self.images = [Image.new("RGB", (self.frame_width, self.frame_height), "black") for _ in range(10)]

    def test_single_image_grid(self):
        """Test that a single image results in a 1x1 grid."""
        grid = create_grid(self.images[:1], self.frame_width, self.frame_height, self.max_grid_dim)
        self.assertEqual(grid.size, (self.frame_width, self.frame_height))

    def test_exact_square_number_of_images(self):
        """Test grids where the number of images is a perfect square."""
        grid = create_grid(self.images[:4], self.frame_width, self.frame_height, self.max_grid_dim)
        self.assertEqual(grid.size, (2 * self.frame_width, 2 * self.frame_height))  # 2x2 grid

        grid = create_grid(self.images[:9], self.frame_width, self.frame_height, self.max_grid_dim)
        self.assertEqual(grid.size, (3 * self.frame_width, 3 * self.frame_height))  # 3x3 grid

    def test_non_square_number_of_images(self):
        """Test cases where the number of images is not a perfect square."""
        grid = create_grid(self.images[:2], self.frame_width, self.frame_height, self.max_grid_dim)
        self.assertEqual(grid.size, (2 * self.frame_width, 2 * self.frame_height))  # 2x2 grid

        grid = create_grid(self.images[:3], self.frame_width, self.frame_height, self.max_grid_dim)
        self.assertEqual(grid.size, (2 * self.frame_width, 2 * self.frame_height))  # 2x2 grid

        grid = create_grid(self.images[:5], self.frame_width, self.frame_height, self.max_grid_dim)
        self.assertEqual(grid.size, (3 * self.frame_width, 3 * self.frame_height))  # 3x3 grid

    def test_grid_limited_by_max_dimension(self):
        """Ensure the grid respects the max dimension limit."""
        grid = create_grid(self.images[:10], self.frame_width, self.frame_height, 3)  # Needs 4x4 but limited to 3x3
        self.assertEqual(grid.size, (3 * self.frame_width, 3 * self.frame_height))

        grid = create_grid(self.images[:10], self.frame_width, self.frame_height, 4)  # Max 4x4 should be used
        self.assertEqual(grid.size, (4 * self.frame_width, 4 * self.frame_height))

    def test_blank_spaces_filled_correctly(self):
        """Ensure images are placed left-to-right, top-to-bottom, and remaining spaces stay blank."""
        grid = create_grid(self.images[:7], self.frame_width, self.frame_height, 3)  # Needs 3x3 grid

        # Check that the last row has blank spaces
        blank_pixel = grid.getpixel((2 * self.frame_width + 1, 2 * self.frame_height + 1))  # Sample blank area
        self.assertEqual(blank_pixel, (255, 255, 255))  # Ensure blank areas remain white

    def test_zero_images(self):
        """Ensure an empty grid is handled gracefully."""
        grid = create_grid([], self.frame_width, self.frame_height, self.max_grid_dim)
        self.assertEqual(grid.size, (self.frame_width, self.frame_height))  # Should return a 1x1 blank grid

    def test_odd_aspect_ratio(self):
        """Ensure images of different aspect ratios still fit correctly, with blank space if necessary."""
        odd_aspect_image = Image.new("RGB", (self.frame_width, int(self.frame_height * 1.5)), "black")
        grid = create_grid([odd_aspect_image], self.frame_width, self.frame_height, self.max_grid_dim)

        self.assertEqual(grid.size, (self.frame_width, self.frame_height))  # Still 1x1 grid



