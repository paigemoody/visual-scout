import unittest
import os
from PIL import Image
import math
import shutil
from visual_scout.generate_grids import (
    create_grid,
    save_grid,
    process_images_in_chunks,
    create_grids_from_frames
)

class TestGenerateGrids(unittest.TestCase):
    """Unit tests for generate_grids.."""

    def setUp(self):
        """Set up paths to fixture images, temp output directory."""
        self.fixture_dir = os.path.join(os.path.dirname(__file__), "fixtures", "example_output_frames")
        self.output_dir = os.path.join(os.path.dirname(__file__), "tmp", "temp_grid_output")
        os.makedirs(self.output_dir, exist_ok=True)

        # Use images from fixture directory
        self.video_frames_dir = os.path.join(self.fixture_dir, "example_video_horizontal_frames")
        self.sample_images = sorted([
            os.path.join(self.video_frames_dir, f) for f in os.listdir(self.video_frames_dir)
            if f.endswith(".jpg")
        ])

    def tearDown(self):
        """Completely remove the /tmp directory and all its contents."""
        tmp_dir = os.path.join(os.path.dirname(__file__), "tmp")

        if os.path.exists(tmp_dir):
            try:
                shutil.rmtree(tmp_dir)  # Delete everything inside /tmp and remove /tmp itself
                print(f"🗑 Deleted temporary test directory: {tmp_dir}")
            except Exception as e:
                print(f"Warning: Failed to delete {tmp_dir}: {e}")

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
                expected_output_grids = math.ceil(len(frame_files) / (grid_size ** 2))

                output_grids = os.listdir(video_output_subdir)

                self.assertEqual(
                    len(output_grids), expected_output_grids,
                    f"Expected {expected_output_grids} grid images for {video_folder} with grid_size {grid_size}, found {len(output_grids)}."
                )

    def test_create_grids_from_frames__2x2(self): 
        self.run__create_grids_from_frames(2)

    def test_create_grids_from_frames__3x3(self):
        self.run__create_grids_from_frames(3)

    
if __name__ == "__main__":
    unittest.main()

