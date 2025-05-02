import unittest
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch
from visual_scout.extract_frames import (
    extract_frames,
    extract_frames_from_gif,
    extract_frames_from_image,
    main_extract_frames,
    get_file_type_from_extension,
    get_valid_media_files,
    open_video,
    save_image_to_disk
)
from visual_scout.utils.frame_utils import create_output_dir


class TestExtractFrames(unittest.TestCase):
    def setUp(self):
        """Set up paths to fixture videos and create a temp output directory with 'output_frames'."""
        self.test_input_dir = os.path.join(
            os.path.dirname(__file__), "fixtures", "example_input_dir_short"
        )
        self.valid_video_name = "example_video_horizontal.mov"
        self.valid_video_path = os.path.join(self.test_input_dir, self.valid_video_name)

        # Create a temp directory
        self.temp_output_dir = tempfile.mkdtemp()

        # Create the /output_frames subdirectory inside the temp directory
        self.temp_output_frames_dir = os.path.join(
            self.temp_output_dir, "output_frames"
        )
        os.makedirs(self.temp_output_frames_dir, exist_ok=True)

        print("Temporary Output Directory:", self.temp_output_dir)
        print("Temporary Output Frames Directory:", self.temp_output_frames_dir)

        # Define expected output paths within the temp directory
        self.expected_output_dir_valid_video = os.path.join(
            self.temp_output_frames_dir,
            self.valid_video_name.replace(".mov", "__frames"),
        )

        # Patch make_output_dir to dynamically generate the correct path
        def mock_create_output_dir():
            return self.temp_output_frames_dir

        self.patcher = patch(
            "visual_scout.extract_frames.create_output_dir",
            side_effect=mock_create_output_dir,
        )
        self.mock_make_output_dir = self.patcher.start()

    def tearDown(self):
        """Remove the temp output directory after each test."""
        self.patcher.stop()
        if os.path.exists(self.temp_output_dir):
            shutil.rmtree(self.temp_output_dir)
        print(f"Deleted temporary directory: {self.temp_output_dir}")

    def test_extract_frames_invalid_video(self):
        """Test that extract_frames raises a warning when given an invalid video file."""
        video_name = "invalid_video.mov"
        invalid_video_file = os.path.join(self.test_input_dir, video_name)

        with self.assertWarns(Warning):
            extract_frames(self.temp_output_frames_dir, invalid_video_file, .6, False)

        output_path = os.path.join(
            self.temp_output_dir,
            "output_frames",
            video_name.replace(".mov", "__frames"),
        )
        output_path_exists = os.path.exists(output_path)
        self.assertFalse(output_path_exists, "Frame directory was not created.")

    def test_extract_frames_success(self):
        """Test if frames are extracted and saved correctly from a valid video file."""
        extract_frames(self.temp_output_frames_dir, self.valid_video_path, .6, False)

        self.assertTrue(
            os.path.exists(self.expected_output_dir_valid_video),
            "Frame directory was not created.",
        )
        extracted_frames = [
            f
            for f in os.listdir(self.expected_output_dir_valid_video)
            if f.endswith(".jpg")
        ]
        self.assertGreater(len(extracted_frames), 0, "No frames were extracted.")

    def test_extract_frames_file_not_found(self):
        """Test that extract_frames raises FileNotFoundError for a non-existent file."""
        with self.assertRaises(FileNotFoundError):
            extract_frames(self.temp_output_frames_dir, "non_existent_video.mov", .6, False)

    def test_extract_frames_from_directory(self):
        """Test if extract_frames_from_directory correctly processes multiple video files in a directory
        and ignores non-video files."""

        main_extract_frames(self.test_input_dir, "default", False)

        # Ensure the non-valid files did not trigger frame extraction
        expected_skipped_files = ["random.txt", "invalid_video.mov"]
        for file in expected_skipped_files:
            output_dir = os.path.join(
                self.temp_output_dir, "output_frames", f"{file}__frames"
            )
            self.assertFalse(
                os.path.exists(output_dir),
                f"Non-allowed file {file} should not create an output directory.",
            )

        # Expected output directories base names
        base_names = [
            "example_video_horizontal",
            "example_video_vertical",
            "example_image",
            "example_gif",
        ]

        expected_output_subdirs = [
            'example_video_horizontal__frames',
            'example_gif__frames',
            'example_video_vertical__frames',
            'example_image__frames'
        ]

        for output_path_name in expected_output_subdirs:
            
            valid_output_path = os.path.join(
                self.temp_output_dir, "output_frames", output_path_name
            )

            self.assertTrue(
                os.path.exists(valid_output_path),
                f"Frame directory for {output_path_name} was not created.",
            )
            extracted_frames = [
                f for f in os.listdir(valid_output_path) if f.endswith(".jpg")
            ]

            self.assertGreater(
                len(extracted_frames),
                0,
                f"No frames were extracted for {valid_output_path}.",
            )


class TestGetValidInputMedia(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory with mock video and non-video files."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = self.temp_dir.name  # Store path to temp directory

        # Create mock media files
        self.valid_media_files = [
            "video1.mp4",
            "video2.mov",
            "video3.avi",
            "image1.jpg",
            "gif1.gif",
        ]
        for file in self.valid_media_files:
            with open(os.path.join(self.test_dir, file), "w") as f:
                f.write("mock file content")

        # Create some non-allowed files
        self.non_allowed_media_files = ["document.txt", "audio.mp3"]
        for file in self.non_allowed_media_files:
            with open(os.path.join(self.test_dir, file), "w") as f:
                f.write("mock file content")

    def tearDown(self):
        """Clean up and remove the temporary directory."""
        self.temp_dir.cleanup()

    def test_valid_video_files_detected(self):
        """Test that only valid video files are detected."""
        video_files = get_valid_media_files(self.test_dir)
        expected_paths = [
            os.path.join(self.test_dir, v) for v in self.valid_media_files
        ]

        self.assertEqual(
            sorted(video_files),
            sorted(expected_paths),
            "Valid video files should be detected.",
        )

    def test_non_allowed_media_files_ignored(self):
        """Test that non-video files are ignored."""
        video_files = get_valid_media_files(self.test_dir)
        unexpected_paths = [
            os.path.join(self.test_dir, f) for f in self.non_allowed_media_files
        ]

        for path in unexpected_paths:
            self.assertNotIn(
                path, video_files, f"Non-video file {path} should not be detected."
            )

    def test_no_video_files_returns_none(self):
        """Test that an empty directory returns None."""
        empty_temp_dir = tempfile.TemporaryDirectory()
        self.assertIsNone(
            get_valid_media_files(empty_temp_dir.name),
            "Function should return None if no allowed media files are found.",
        )

    def test_missing_directory_raises_error(self):
        """Test that a nonexistent directory raises FileNotFoundError."""
        fake_dir = os.path.join(self.test_dir, "nonexistent_dir")
        with self.assertRaises(FileNotFoundError):
            get_valid_media_files(fake_dir)


class TestOpenVideo(unittest.TestCase):
    def setUp(self):
        self.valid_video_path = os.path.join(
            os.path.dirname(__file__),
            "fixtures",
            "example_input_dir_short",
            "example_video_horizontal.mov",
        )
        self.invalid_video_path = os.path.join(
            os.path.dirname(__file__),
            "fixtures",
            "example_input_dir_short",
            "invalid_video.mov",
        )
        self.temp_output_dir_name = "temp_output_dir"
    
    def tearDown(self):
        """Remove the temp output directory after each test."""
        if os.path.exists(self.temp_output_dir_name):
            shutil.rmtree(self.temp_output_dir_name)
        print(f"Deleted temporary directory: {self.temp_output_dir_name}")

    def test_open_video_success(self):
        cap = open_video(self.valid_video_path)
        self.assertIsNotNone(cap)
        self.assertTrue(cap.isOpened())
        cap.release()

    def test_extract_frames_invalid_video(self):
        """Test that extract_frames raises a warning when given an invalid video file."""
        with self.assertWarns(UserWarning):
            extract_frames(self.temp_output_dir_name, self.invalid_video_path, .6, False)

    def test_open_video_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            open_video("nonexistent.mov")

    @patch("cv2.VideoCapture")
    def test_open_video_opencv_failure(self, mock_capture):
        mock_capture.return_value.isOpened.return_value = False
        with self.assertWarns(Warning):
            result = open_video(self.valid_video_path)
        self.assertFalse(result)


class TestGetFileTypeFromExtension(unittest.TestCase):
    def test_file_type_detection(self):
        self.assertEqual(get_file_type_from_extension("video.mp4"), "video")
        self.assertEqual(get_file_type_from_extension("clip.MOV"), "video")
        self.assertEqual(get_file_type_from_extension("image.jpg"), "image")
        self.assertEqual(get_file_type_from_extension("pic.PNG"), "image")
        self.assertEqual(get_file_type_from_extension("animation.gif"), "gif")

    def test_unsupported_file_type(self):
        with self.assertRaises(ValueError):
            get_file_type_from_extension("file.xyz")


class TestExtractFramesFromImage(unittest.TestCase):
    def setUp(self):
        self.image_path = os.path.join(
            os.path.dirname(__file__),
            "fixtures",
            "example_input_dir_short",
            "example_image.jpg",
        )
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_extract_frames_from_image(self):
        img_lst = extract_frames_from_image(self.temp_dir, self.image_path, save_image_to_disk)
        self.assertEqual(len(img_lst), 1)
        files = os.listdir(self.temp_dir)
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].endswith(".jpg"))


class TestExtractFramesFromGif(unittest.TestCase):
    def setUp(self):
        self.gif_path = os.path.join(
            os.path.dirname(__file__),
            "fixtures",
            "example_input_dir_short",
            "example_gif.gif",
        )
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_extract_frames_from_gif(self):
        frames_lst = extract_frames_from_gif(self.temp_dir, self.gif_path, .6, False, save_image_to_disk)
        expected_frames_saved_count = len(frames_lst)
        self.assertGreater(expected_frames_saved_count, 0)
        saved_files = [f for f in os.listdir(self.temp_dir) if f.endswith(".jpg")]
        self.assertEqual(expected_frames_saved_count, len(saved_files))


class TestCreateOutputDir(unittest.TestCase):
    @patch("visual_scout.extract_frames.os.makedirs")
    @patch("visual_scout.extract_frames.os.getcwd")
    def test_create_output_dir_creates_expected_path(self, mock_getcwd, mock_makedirs):
        mock_getcwd.return_value = "/mock/project"
        output_dir = create_output_dir()
        expected_path = "/mock/project/output/output_frames"
        self.assertEqual(output_dir, expected_path)
        mock_makedirs.assert_called_once_with(expected_path, exist_ok=True)
