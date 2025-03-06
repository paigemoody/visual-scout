import os
import shutil
import unittest
import json
from unittest.mock import patch

from visual_scout.extract_visual_content import (
    get_label_gen_prompt, 
    get_openai_labels,
    process_images
)

class TestVisualGridProcessing(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up fixture paths and mock OpenAI API globally."""
        # cls.fixture_base_dir = os.path.join(os.path.dirname(__file__), "fixtures")

        # # Input: Example grids from fixtures
        # cls.input_grids_dir = os.path.join(cls.fixture_base_dir, "example_output_grids")




        # if not cls.sample_horizontal_grids or not cls.sample_vertical_grids:
        #     raise ValueError("Fixture directories do not contain enough grids for tests.")

        # Mock OpenAI API response
        cls.mock_openai_patcher = patch("visual_scout.extract_visual_content.get_openai_labels")
        cls.mock_openai = cls.mock_openai_patcher.start()
        cls.mock_openai.return_value = {
            "labels": ["man", "sunglasses", "hat"]
        }

    @classmethod
    def tearDownClass(cls):
        """Remove temporary output directories and stop patches."""
        # if os.path.exists(cls.output_visual_content_dir):
        #     shutil.rmtree(cls.output_visual_content_dir)
        #     print(f"🗑 Deleted temporary JSON output directory: {cls.output_visual_content_dir}")

        cls.mock_openai_patcher.stop()

    def setUp(self):
        """Set up paths to fixture grids before each test."""
        self.fixture_base_dir = os.path.join(os.path.dirname(__file__), "fixtures")

        # Corrected paths based on actual structure
        self.input_grids_dir = os.path.join(self.fixture_base_dir, "example_output_grids")
        self.horizontal_grids_dir = os.path.join(self.input_grids_dir, "example_video_horizontal__frames__grids")
        self.vertical_grids_dir = os.path.join(self.input_grids_dir, "example_video_vertical__frames__grids")

        # Temporary directory for test outputs
        self.temp_output_dir = os.path.join(os.path.dirname(__file__), "tmp", "test_output_visual_content")
        os.makedirs(self.temp_output_dir, exist_ok=True)

        # Collect grid images from the fixture directory
        self.sample_horizontal_grids = sorted([
            os.path.join(self.horizontal_grids_dir, f) for f in os.listdir(self.horizontal_grids_dir)
        ])
        self.sample_vertical_grids = sorted([
            os.path.join(self.vertical_grids_dir, f) for f in os.listdir(self.vertical_grids_dir)
        ])

        # Ensure test has enough fixture images
        if not self.sample_horizontal_grids or not self.sample_vertical_grids:
            raise ValueError("Fixture directories do not contain enough grids for tests.")

    # def tearDown(self):
    #     """Clean up temporary test output directories after each test."""
    #     if os.path.exists(self.temp_output_dir):
    #         shutil.rmtree(self.temp_output_dir)
    #         print(f"🗑 Deleted temporary test directory: {self.temp_output_dir}")

    # def test_get_label_gen_prompt(self):
    #     """Test that get_label_gen_prompt correctly formats the prompt with base64-encoded image."""
    #     test_image_path = self.sample_horizontal_grids[0]  # Use a real fixture image

    #     # Run the function
    #     prompt = get_label_gen_prompt(test_image_path)

    #     # Assertions
    #     self.assertIsInstance(prompt, list, "Prompt should be a list.")
    #     self.assertEqual(prompt[0]["role"], "user", "Role should be 'user'.")
    #     self.assertIsInstance(prompt[0]["content"], list, "Content should be a list.")

    #     # Validate image encoding
    #     image_data = prompt[0]["content"][1]
    #     self.assertIn("image", image_data, "Image data should contain 'image' key.")
    #     self.assertIsInstance(image_data["image"], str, "Encoded image should be a string.")
    #     self.assertGreater(len(image_data["image"]), 0, "Encoded image should not be empty.")

    # def test_get_openai_labels_success(self):
    #     """Test get_openai_labels returns expected response format when OpenAI API succeeds."""
    #     test_image_path = self.sample_horizontal_grids[0]  # Use a real fixture image
    #     test_prompt = get_label_gen_prompt(test_image_path)

    #     response = get_openai_labels(test_prompt)

    #     self.assertIsInstance(response, dict, "Response should be a dictionary.")
    #     self.assertIn("labels", response, "Response should contain 'labels' key.")
    #     self.assertIsInstance(response["labels"], list, "'labels' should be a list.")
    #     self.assertGreater(len(response["labels"]), 0, "Labels list should not be empty.")

    # def test_get_openai_labels_failure(self):
    #     """Test get_openai_labels returns error message after repeated failures."""
    #     test_image_path = self.sample_horizontal_grids[0]  # Use a real fixture image
    #     test_prompt = get_label_gen_prompt(test_image_path)

    #     with patch("visual_scout.extract_visual_content.OPENAI_CLIENT.chat.completions.create", side_effect=Exception("API Failure")):
    #         response = get_openai_labels(test_prompt)

    #         self.assertIsInstance(response, dict, "Response should be a dictionary.")
    #         self.assertIn("labels", response, "Response should contain 'labels' key.")
    #         self.assertEqual(len(response["labels"]), 1, "Labels should contain only one error message.")
    #         self.assertTrue(response["labels"][0].startswith("Error:"), "Error message should be returned.")

    # def test_get_openai_labels_refusal(self):
    #     """Test get_openai_labels handles OpenAI refusals correctly."""
    #     test_image_path = self.sample_horizontal_grids[0]  # Use a real fixture image
    #     test_prompt = get_label_gen_prompt(test_image_path)

    #     mock_openai_response = {
    #         "choices": [
    #             {
    #                 "message": {
    #                     "refusal": "Content violates policy"
    #                 }
    #             }
    #         ]
    #     }

    #     with patch("visual_scout.extract_visual_content.OPENAI_CLIENT.chat.completions.create") as mock_create:
    #         mock_create.return_value.model_dump_json.return_value = json.dumps(mock_openai_response)

    #         response = get_openai_labels(test_prompt)

    #         self.assertIsInstance(response, dict, "Response should be a dictionary.")
    #         self.assertIn("labels", response, "Response should contain 'labels' key.")
    #         self.assertEqual(len(response["labels"]), 1, "Labels should contain only one warning message.")
    #         self.assertTrue(response["labels"][0].startswith("Warning:"), "Warning message should be returned.")


    def test_process_images_creates_json_files(self):
        """Test that process_images creates expected JSON files in the correct structure."""

        process_images(input_dir=self.input_grids_dir, output_dir=self.temp_output_dir)

        # .replace("__frames__grids", "")

        # Expected output structure
        expected_videos = ["example_video_horizontal", "example_video_vertical"]
        expected_files_per_video = {
            "example_video_horizontal__frames__grids": [
                "visual_content_0-00-00_0-00-18.json",
                "visual_content_0-00-18_0-00-28.json",
                "example_video_horizontal__visual_content.json"  # Combined JSON
            ],
            "example_video_vertical__frames__grids": [
                "visual_content_0-00-00_0-00-18.json",
                "visual_content_0-00-18_0-00-36.json",
                "visual_content_0-00-36_0-00-40.json",
                "example_video_horizontal__visual_content.json"  # Combined JSON
            ]
        }

        # Verify directories exist
        for video_name in expected_videos:
            video_output_dir = os.path.join(self.temp_output_dir, video_name)

            print("\n\n\nvideo_output_dir:", video_output_dir)
            self.assertTrue(os.path.exists(video_output_dir), f"Output directory missing: {video_output_dir}")

            # # List actual files
            # output_files = set(os.listdir(video_output_dir))
            # expected_files = set(expected_files_per_video[video_name])

            # # Debugging: print output files before asserting
            # print(f"\n📂 Output files for {video_name}: {sorted(output_files)}")

            # # Check that expected files match actual output
            # self.assertEqual(output_files, expected_files, f"Unexpected files in {video_output_dir}")

            # # Ensure combined JSON file is not empty
            # combined_json_path = os.path.join(video_output_dir, f"{video_name}.json")
            # with open(combined_json_path, "r", encoding="utf-8") as f:
            #     combined_data = json.load(f)

            # self.assertGreater(len(combined_data), 0, "Combined JSON should contain at least one timestamped entry.")
