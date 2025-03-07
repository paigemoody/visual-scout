import unittest
import os
import shutil
import tempfile
from unittest.mock import patch
from visual_scout.extract_frames import extract_frames, main_extract_frames


class TestExtractFrames(unittest.TestCase):
    def setUp(self):
        """Set up paths to fixture videos and create a temp output directory with 'output_frames'."""
        self.test_input_dir = os.path.join(os.path.dirname(__file__), "fixtures", "example_input_dir")
        self.valid_video_name = "example_video_horizontal.mov"
        self.valid_video_path = os.path.join(self.test_input_dir, self.valid_video_name)

        # Create a temp directory
        self.temp_output_dir = tempfile.mkdtemp()
        
        # Create the /output_frames subdirectory inside the temp directory
        self.temp_output_frames_dir = os.path.join(self.temp_output_dir, "output_frames")
        os.makedirs(self.temp_output_frames_dir, exist_ok=True)

        print("Temporary Output Directory:", self.temp_output_dir)
        print("Temporary Output Frames Directory:", self.temp_output_frames_dir)

        # Define expected output paths within the temp directory
        self.expected_output_dir_valid_video = os.path.join(
            self.temp_output_frames_dir, self.valid_video_name.replace(".mov", "__frames")
        )

        # Patch make_output_dir to dynamically generate the correct path
        def mock_create_output_dir():
            return self.temp_output_frames_dir

        self.patcher = patch("visual_scout.extract_frames.create_output_dir", side_effect=mock_create_output_dir)
        self.mock_make_output_dir = self.patcher.start()

    def tearDown(self):
        """Remove the temp output directory after each test."""
        self.patcher.stop()
        if os.path.exists(self.temp_output_dir):
            shutil.rmtree(self.temp_output_dir)
        print(f"Deleted temporary directory: {self.temp_output_dir}")

    def test_extract_frames_invalid_video(self):
        """Test that extract_frames raises an IOError when given an invalid video file."""
        video_name = "invalid_video.mov"
        invalid_video_file = os.path.join(self.test_input_dir, video_name)

        with self.assertWarns(Warning):
            extract_frames(self.temp_output_frames_dir, invalid_video_file)
        
        output_path = os.path.join(self.temp_output_dir, "output_frames", video_name.replace(".mov", "__frames"))

        self.assertFalse(os.path.exists(output_path), "Frame directory was not created.")

    def test_extract_frames_success(self):
        """Test if frames are extracted and saved correctly from a valid video file."""
        extract_frames(self.temp_output_frames_dir, self.valid_video_path)

        self.assertTrue(os.path.exists(self.expected_output_dir_valid_video), "Frame directory was not created.")
        extracted_frames = [f for f in os.listdir(self.expected_output_dir_valid_video) if f.endswith(".jpg")]
        self.assertGreater(len(extracted_frames), 0, "No frames were extracted.")

    def test_extract_frames_file_not_found(self):
        """Test that extract_frames raises FileNotFoundError for a non-existent file."""
        with self.assertRaises(FileNotFoundError):
            extract_frames(self.temp_output_frames_dir, "non_existent_video.mov")

    def test_extract_frames_from_directory(self):
        """Test if extract_frames_from_directory correctly processes multiple video files in a directory
        and ignores non-video files."""

        # Ensure that invalid video isn't processed
        with self.assertWarns(Warning):
            main_extract_frames(self.test_input_dir)

        # Expected output directories base names
        base_name1 = "example_video_horizontal"
        base_name2 = "example_video_vertical"

        valid_output_dir1 = os.path.join(self.temp_output_dir, "output_frames", f"{base_name1}__frames")
        valid_output_dir2 = os.path.join(self.temp_output_dir, "output_frames", f"{base_name2}__frames")

        print("valid_output_dir1", valid_output_dir1)
        print("valid_output_dir2", valid_output_dir2)

        # Check that BOTH video files were processed
        self.assertTrue(os.path.exists(valid_output_dir1), "Frame directory for horizontal video was not created.")
        self.assertTrue(os.path.exists(valid_output_dir2), "Frame directory for vertical video was not created.")

        extracted_frames1 = [f for f in os.listdir(valid_output_dir1) if f.endswith(".jpg")]
        extracted_frames2 = [f for f in os.listdir(valid_output_dir2) if f.endswith(".jpg")]

        self.assertGreater(len(extracted_frames1), 0, "No frames were extracted for the horizontal video.")
        self.assertGreater(len(extracted_frames2), 0, "No frames were extracted for the vertical video.")

        # Ensure the non-video files did not trigger frame extraction
        expected_skipped_files = ["example_image.jpg", "invalid_video.mov"]
        for file in expected_skipped_files:
            output_dir = os.path.join(self.temp_output_dir, "output_frames", f"{file}__frames")
            self.assertFalse(os.path.exists(output_dir), f"Non-video file {file} should not create an output directory.")
