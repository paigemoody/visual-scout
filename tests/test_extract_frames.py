import unittest
import os
import shutil
import tempfile
from visual_scout.extract_frames import extract_frames, extract_frames_from_directory


class TestExtractFrames(unittest.TestCase):
    """Unit tests for extract_frames.py using a pre-existing test video fixture."""

    @classmethod
    def setUpClass(cls):
        """Set up a test video fixture (one-time setup)."""
        cls.test_video_src = os.path.join(os.path.dirname(__file__), "fixtures", "example_input_dir", "example_video_horizontal.mov")
        if not os.path.exists(cls.test_video_src):
            raise FileNotFoundError(f"Test video fixture not found: {cls.test_video_src}")

    def setUp(self):
        """Copy the test video to a temp location for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_video_file = os.path.join(self.temp_dir, "example_video_horizontal.mov")
        shutil.copy(self.test_video_src, self.temp_video_file)

        # Define expected output directories
        self.output_dir = "output_frames"
        base_name = os.path.basename(self.temp_video_file).split(".")[0]
        self.valid_output_dir = os.path.join(self.output_dir, f"{base_name}__frames")
        self.invalid_output_dir = os.path.join(self.output_dir, "invalid_video__frames")

    def tearDown(self):
        """Remove temporary test files and any leftover output directories after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        shutil.rmtree(self.valid_output_dir, ignore_errors=True)
        shutil.rmtree(self.invalid_output_dir, ignore_errors=True)

    def test_extract_frames_success(self):
        """Test if frames are extracted and saved correctly from a valid video file."""
        extract_frames(self.temp_video_file)

        self.assertTrue(os.path.exists(self.valid_output_dir), "Frame directory was not created.")
        extracted_frames = [f for f in os.listdir(self.valid_output_dir) if f.endswith(".jpg")]
        self.assertGreater(len(extracted_frames), 0, "No frames were extracted.")

    def test_extract_frames_file_not_found(self):
        """Test that extract_frames raises FileNotFoundError for a non-existent file."""
        with self.assertRaises(FileNotFoundError):
            extract_frames("non_existent_video.mov")

    def test_extract_frames_invalid_video(self):
        """Test that extract_frames raises an IOError when given an invalid video file."""
        invalid_video_file = os.path.join(self.temp_dir, "invalid_video.mov")

        # Create a fake video file with invalid content
        with open(invalid_video_file, "wb") as f:
            f.write(os.urandom(1024))  # Write random bytes to simulate a corrupt file

        with self.assertRaises(IOError):
            extract_frames(invalid_video_file)

        # Ensure the invalid output directory was NOT created
        self.assertFalse(os.path.exists(self.invalid_output_dir), "Invalid video output directory should not exist.")

    def test_extract_frames_from_directory(self):
        """Test if extract_frames_from_directory correctly processes multiple video files in a directory
        and ignores non-video files."""

        # Use the new fixture directory containing multiple videos
        self.test_input_dir = os.path.join(os.path.dirname(__file__), "fixtures", "example_input_dir")

        if not os.path.exists(self.test_input_dir):
            raise FileNotFoundError(f"Test input directory not found: {self.test_input_dir}")

        # Add a non-video file in the directory (should be ignored)
        non_video_file = os.path.join(self.test_input_dir, "random.txt")
        with open(non_video_file, "w") as f:
            f.write("This is a non-video file.")

        extract_frames_from_directory(self.test_input_dir)

        # Define expected output directories for each video
        base_name1 = "example_video_horizontal"
        base_name2 = "example_video_vertical"

        valid_output_dir1 = os.path.join(self.output_dir, f"{base_name1}__frames")
        valid_output_dir2 = os.path.join(self.output_dir, f"{base_name2}__frames")

        # Check that BOTH video files were processed
        self.assertTrue(os.path.exists(valid_output_dir1), "Frame directory for horizontal video was not created.")
        self.assertTrue(os.path.exists(valid_output_dir2), "Frame directory for vertical video was not created.")

        extracted_frames1 = [f for f in os.listdir(valid_output_dir1) if f.endswith(".jpg")]
        extracted_frames2 = [f for f in os.listdir(valid_output_dir2) if f.endswith(".jpg")]

        self.assertGreater(len(extracted_frames1), 0, "No frames were extracted for the horizontal video.")
        self.assertGreater(len(extracted_frames2), 0, "No frames were extracted for the vertical video.")

        # Ensure the non-video file did not trigger any extraction
        non_video_output_dir = os.path.join(self.output_dir, "random__frames")
        self.assertFalse(os.path.exists(non_video_output_dir), "Non-video file should not create an output directory.")

        # Clean up extracted frames and non-video file after the test
        shutil.rmtree(valid_output_dir1, ignore_errors=True)
        shutil.rmtree(valid_output_dir2, ignore_errors=True)
        os.remove(non_video_file)

