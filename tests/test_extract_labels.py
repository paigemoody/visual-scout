import os
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from visual_scout.extract_labels import (
    process_images,
    get_openai_labels,
    get_labels_main,
)
from visual_scout.image_utils import extract_timestamps


class TestExtractLabels(unittest.TestCase):
    def setUp(self):
        """Set up test input and temporary output directories."""
        self.fixture_dir = os.path.join(
            os.path.dirname(__file__), "fixtures", "output", "example_output_grids"
        )

        # Create a temporary directory for storing output JSONs
        self.temp_output_dir = tempfile.TemporaryDirectory()

        # Ensure the fixture directory exists
        if not os.path.exists(self.fixture_dir):
            raise FileNotFoundError(
                f"Test fixture directory not found: {self.fixture_dir}"
            )

        # Mock OpenAI API key and model
        self.open_ai_key = "test-key"
        self.open_ai_model = "test-model"

    def tearDown(self):
        """Clean up temporary directories after each test."""
        self.temp_output_dir.cleanup()

    @patch("visual_scout.extract_labels.openai.OpenAI")
    def test_get_openai_labels_success(self, mock_openai):
        """Test that get_openai_labels returns expected response when OpenAI API succeeds."""

        # Create a mock OpenAI response
        mock_response = MagicMock()
        mock_response.model_dump_json.return_value = json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps({"labels": ["person", "sunglasses", "hat"]})
                        }
                    }
                ]
            }
        )

        # Mock the OpenAI API call
        mock_openai.return_value.chat.completions.create.return_value = mock_response

        test_prompt = [{"role": "user", "content": ["test image data"]}]
        response = get_openai_labels(
            test_prompt, self.open_ai_key, self.open_ai_model
        )

        # Assertions
        self.assertIsInstance(response, dict, "Response should be a dictionary.")
        self.assertIn("labels", response, "Response should contain 'labels' key.")
        self.assertGreater(len(response["labels"]), 0, "Labels list should not be empty.")
        self.assertEqual(response["labels"], ["person", "sunglasses", "hat"])

    @patch("visual_scout.extract_labels.openai.OpenAI")
    def test_get_openai_labels_failure(self, mock_openai):
        """Test get_openai_labels handles API failures gracefully."""
        
        # Mock OpenAI failure by raising an Exception
        mock_openai.return_value.chat.completions.create.side_effect = Exception("API Failure")

        test_prompt = [{"role": "user", "content": ["test image data"]}]
        response = get_openai_labels(
            test_prompt, self.open_ai_key, self.open_ai_model
        )

        # Assertions
        self.assertIn("labels", response, "Response should contain 'labels' key.")
        self.assertEqual(
            len(response["labels"]), 1, "Labels should contain only one error message."
        )
        self.assertTrue(
            response["labels"][0].startswith("Error:"),
            "Error message should be returned.",
        )

    @patch("visual_scout.extract_labels.openai.OpenAI")
    def test_get_openai_labels_refusal(self, mock_openai):
        """Test get_openai_labels handles OpenAI refusals correctly."""

        # Create a mock OpenAI response that simulates a refusal
        mock_response = MagicMock()
        mock_response.model_dump_json.return_value = json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "refusal": "Content violates policy"
                        }
                    }
                ]
            }
        )

        mock_openai.return_value.chat.completions.create.return_value = mock_response

        test_prompt = [{"role": "user", "content": ["test image data"]}]
        response = get_openai_labels(
            test_prompt, self.open_ai_key, self.open_ai_model
        )

        # Assertions
        self.assertIsInstance(response, dict, "Response should be a dictionary.")
        self.assertIn("labels", response, "Response should contain 'labels' key.")
        self.assertEqual(len(response["labels"]), 1, "Labels should contain only one warning message.")
        self.assertTrue(
            response["labels"][0].startswith("Warning:"),
            "Warning message should be returned."
        )

    # @patch("visual_scout.extract_labels.process_images")
    # def test_get_labels_main_raises_error_for_missing_input(self, mock_process_images):
    #     """Test get_labels_main raises error when input directory does not exist."""
    #     with self.assertRaises(FileNotFoundError):
    #         get_labels_main(self.open_ai_key, self.open_ai_model)

    # @patch("visual_scout.extract_labels.process_images")
    # def test_get_labels_main_runs_successfully(self, mock_process_images):
    #     """Test get_labels_main runs when input grids exist."""
    #     # Create mock input directory
    #     temp_input_dir = tempfile.TemporaryDirectory()
    #     os.makedirs(os.path.join(temp_input_dir.name, "example_video_frames"))

    #     # Run main label extraction
    #     with patch("visual_scout.extract_labels.os.getcwd", return_value=temp_input_dir.name):
    #         get_labels_main(self.open_ai_key, self.open_ai_model)

    #     mock_process_images.assert_called()

    #     temp_input_dir.cleanup()

