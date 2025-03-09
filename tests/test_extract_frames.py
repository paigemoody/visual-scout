import unittest
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch
from visual_scout.extract_frames import extract_frames, main_extract_frames, get_valid_input_videos


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


class TestGetValidInputVideos(unittest.TestCase):
    
    def setUp(self):
        """Set up a temporary directory with mock video and non-video files."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = self.temp_dir.name  # Store path to temp directory

        # Create mock video files
        self.valid_videos = ["video1.mp4", "video2.mov", "video3.avi"]
        for video in self.valid_videos:
            with open(os.path.join(self.test_dir, video), "w") as f:
                f.write("mock video content")

        # Create some non-video files
        self.non_video_files = ["image.jpg", "document.txt", "audio.mp3"]
        for file in self.non_video_files:
            with open(os.path.join(self.test_dir, file), "w") as f:
                f.write("mock file content")

    def tearDown(self):
        """Clean up and remove the temporary directory."""
        self.temp_dir.cleanup()

    def test_valid_video_files_detected(self):
        """Test that only valid video files are detected."""
        video_files = get_valid_input_videos(self.test_dir)
        expected_paths = [os.path.join(self.test_dir, v) for v in self.valid_videos]

        self.assertEqual(sorted(video_files), sorted(expected_paths), "Valid video files should be detected.")

    def test_non_video_files_ignored(self):
        """Test that non-video files are ignored."""
        video_files = get_valid_input_videos(self.test_dir)
        unexpected_paths = [os.path.join(self.test_dir, f) for f in self.non_video_files]

        for path in unexpected_paths:
            self.assertNotIn(path, video_files, f"Non-video file {path} should not be detected.")

    def test_no_video_files_returns_none(self):
        """Test that an empty directory or no valid videos returns None."""
        empty_temp_dir = tempfile.TemporaryDirectory()
        self.assertIsNone(get_valid_input_videos(empty_temp_dir.name), "Function should return None if no videos are found.")

    def test_missing_directory_raises_error(self):
        """Test that a nonexistent directory raises FileNotFoundError."""
        fake_dir = os.path.join(self.test_dir, "nonexistent_dir")
        with self.assertRaises(FileNotFoundError):
            get_valid_input_videos(fake_dir)
