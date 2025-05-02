import os
import unittest
import cv2
import re
from datetime import timedelta

from visual_scout.utils.video_utils import inspect_video, natural_sort_key, get_image_files

class TestVideoUtils(unittest.TestCase):

    def setUp(self):
        """Set up paths to fixture video and test directories."""
        self.fixture_dir = os.path.join(os.path.dirname(__file__), "fixtures", "example_input_dir")
        self.valid_video = os.path.join(self.fixture_dir, "example_video_horizontal.mov")
        self.invalid_video = os.path.join(self.fixture_dir, "invalid_video.mov")  # Non-existent file

        # Ensure the fixture directory exists
        if not os.path.exists(self.fixture_dir):
            raise FileNotFoundError(f"Fixture directory '{self.fixture_dir}' is missing.")

        # Ensure the valid fixture video exists
        if not os.path.exists(self.valid_video):
            raise FileNotFoundError(f"Test fixture video '{self.valid_video}' is missing. Please add it.")

    def test_inspect_video_valid(self):
        """Test that inspect_video correctly extracts metadata from the fixture video."""
        cap = cv2.VideoCapture(self.valid_video)
        expected_fps = cap.get(cv2.CAP_PROP_FPS)
        expected_frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        expected_duration = expected_frame_count / expected_fps
        cap.release()

        expected_results = {
            "video file" : self.valid_video,
            "frames per second (FPS)": expected_fps,
            "total frames": expected_frame_count,
            "video duration" : timedelta(seconds=expected_duration)
        }

        actual_results = inspect_video(self.valid_video)
        self.assertEqual(expected_results, actual_results)


    def test_inspect_video_file_not_found(self):
        """Test that inspect_video raises FileNotFoundError for a missing video file."""
        with self.assertRaises(IOError):
            inspect_video(self.invalid_video)

    def test_inspect_video_invalid_file(self):
        """Test that inspect_video raises IOError when given an unreadable file."""
        invalid_path = os.path.join(self.fixture_dir, "corrupt_video.mp4")

        # Create an empty file (not a valid video)
        with open(invalid_path, "w") as f:
            f.write("")

        with self.assertRaises(IOError):
            inspect_video(invalid_path)

        # Cleanup invalid file
        os.remove(invalid_path)

    def test_natural_sort_key(self):
        """Test that natural_sort_key correctly sorts filenames with numeric parts."""
        filenames = ["frame_1.jpg", "frame_10.jpg", "frame_2.jpg", "frame_20.jpg", "frame_11.jpg"]
        expected_order = ["frame_1.jpg", "frame_2.jpg", "frame_10.jpg", "frame_11.jpg", "frame_20.jpg"]

        sorted_filenames = sorted(filenames, key=natural_sort_key)
        self.assertEqual(sorted_filenames, expected_order)

    def test_get_image_files(self):
        """Test that get_image_files retrieves and sorts image files correctly from the fixture directory."""
        image_dir = os.path.join(self.fixture_dir, "test_images")
        os.makedirs(image_dir, exist_ok=True)

        image_filenames = ["frame_1.jpg", "frame_10.jpg", "frame_2.jpg"]
        for img in image_filenames:
            with open(os.path.join(image_dir, img), "w") as f:
                f.write("")

        expected_sorted_files = ["frame_1.jpg", "frame_2.jpg", "frame_10.jpg"]
        retrieved_files = get_image_files(image_dir)

        self.assertEqual(retrieved_files, expected_sorted_files)

        # Cleanup test images
        for img in image_filenames:
            os.remove(os.path.join(image_dir, img))
        os.rmdir(image_dir)

    def test_get_image_files_excludes_non_images(self):
        """Test that get_image_files ignores non-image files in the directory."""
        image_dir = os.path.join(self.fixture_dir, "test_images")
        os.makedirs(image_dir, exist_ok=True)

        valid_images = ["frame_1.jpg", "frame_2.jpg"]
        invalid_files = ["frame_3.txt", "frame_4.mp4"]

        for img in valid_images + invalid_files:
            with open(os.path.join(image_dir, img), "w") as f:
                f.write("")

        retrieved_files = get_image_files(image_dir)
        self.assertEqual(retrieved_files, sorted(valid_images))

        # Cleanup test images
        for img in valid_images + invalid_files:
            os.remove(os.path.join(image_dir, img))
        os.rmdir(image_dir)
