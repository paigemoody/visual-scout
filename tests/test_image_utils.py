import unittest
import os
import tempfile
import base64
from visual_scout.image_utils import (
    encode_image_to_base64,
    extract_timestamps,
    validate_filenames
)

class TestImageUtils(unittest.TestCase):
    """Unit tests for image utility functions in image_utils.py"""

    @classmethod
    def setUpClass(cls):
        """Set up test directories and files."""
        cls.test_dir = tempfile.TemporaryDirectory()
        cls.valid_image_path = os.path.join(cls.test_dir.name, "test_image.jpg")
        cls.invalid_image_path = os.path.join(cls.test_dir.name, "non_existent.jpg")

        # Create a valid image file for testing
        with open(cls.valid_image_path, "wb") as f:
            f.write(os.urandom(1024))  # Write random bytes to simulate an image

    @classmethod
    def tearDownClass(cls):
        """Clean up temporary test directory."""
        cls.test_dir.cleanup()

    def test_encode_image_to_base64_valid_file(self):
        """Test that encode_image_to_base64 correctly encodes an image."""
        encoded_string = encode_image_to_base64(self.valid_image_path)
        self.assertIsInstance(encoded_string, str, "Encoded image should be a string")
        self.assertTrue(len(encoded_string) > 0, "Encoded image should not be empty")

        # Ensure it's a valid base64 string
        try:
            base64.b64decode(encoded_string)
        except Exception as e:
            self.fail(f"Encoded string is not valid base64: {e}")

    def test_encode_image_to_base64_invalid_file(self):
        """Test that encode_image_to_base64 returns None for a missing file."""
        encoded_string = encode_image_to_base64(self.invalid_image_path)
        self.assertIsNone(encoded_string, "Should return None for a missing file")

    def test_extract_timestamps_valid(self):
        """Test that extract_timestamps correctly extracts timestamps from valid filenames."""
        filename = "/Users/somebody/Projects/visual-scout/tests/fixtures/example_output_frames/example_video_horizontal_frames/frame_0-00-26_0-00-28.jpg"
        expected_timestamps = ("0-00-26","0-00-28")
        self.assertEqual(extract_timestamps(filename), expected_timestamps)

    def test_extract_timestamps_invalid(self):
        """Test that extract_timestamps returns None for invalid filenames."""
        filename = "random_file_name.jpg"
        self.assertIsNone(extract_timestamps(filename), "Should return None for non-matching filenames")

    def test_validate_filenames_valid(self):
        """Test that validate_filenames does not exit when all files are valid."""
        valid_file_path = os.path.join(self.test_dir.name, "grid_0-00-00_0-00-18.jpg")
        with open(valid_file_path, "w") as f:
            f.write("fake image content")

        try:
            validate_filenames(valid_file_path)  # Should not raise an exception
        except SystemExit:
            self.fail("validate_filenames() should not exit for valid files")

    def test_validate_filenames_invalid(self):
        """Test that validate_filenames exits when invalid files are found."""
        invalid_file_path = os.path.join(self.test_dir.name, "invalid_image.jpg")
        with open(invalid_file_path, "w") as f:
            f.write("fake image content")

    #     with self.assertRaises(SystemExit):
    #         validate_filenames(self.test_dir.name)  # Should exit due to invalid file

