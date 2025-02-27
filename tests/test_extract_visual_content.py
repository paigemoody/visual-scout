import pytest
import os
import json
import tempfile
from unittest import mock
from visual_scout.extract_visual_content import (
    get_label_gen_prompt,
    get_openai_labels,
    process_images,
    combine_visual_content_json
)


@pytest.fixture
def temp_image():
    """
    Creates a temporary image file to simulate an input frame.
    """
    temp_dir = tempfile.mkdtemp()
    image_path = os.path.join(temp_dir, "frame_00-00-02_00-00-04.jpg")
    
    with open(image_path, "wb") as img:
        img.write(os.urandom(1024))  # Fake image data
    
    yield image_path
    os.remove(image_path)


@pytest.fixture
def temp_json_file():
    """
    Creates a temporary JSON file to test JSON processing.
    """
    temp_dir = tempfile.mkdtemp()
    json_path = os.path.join(temp_dir, "frame_00-00-02_00-00-04.json")
    
    sample_data = {"labels": ["man", "crowd", "visible text: 'Hello World'"]}
    
    with open(json_path, "w", encoding="utf-8") as json_file:
        json.dump(sample_data, json_file)
    
    yield json_path
    os.remove(json_path)


def test_get_label_gen_prompt(temp_image):
    """
    Tests if `get_label_gen_prompt` correctly generates an OpenAI prompt.
    """
    prompt = get_label_gen_prompt(temp_image)
    
    assert isinstance(prompt, list), "Prompt should be a list."
    assert "role" in prompt[0] and prompt[0]["role"] == "user", "Prompt should have a 'user' role."
    assert isinstance(prompt[0]["content"], list), "Content should be a list."
    assert "image" in prompt[0]["content"][1], "Image data should be in content."


@mock.patch("visual_scout.extract_visual_content.openai_client.chat.completions.create")
def test_get_openai_labels(mock_openai_call):
    """
    Tests if `get_openai_labels` properly handles an OpenAI response.
    """
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({"labels": ["man", "car", "tree"]})
                }
            }
        ]
    }
    
    mock_openai_call.return_value.model_dump_json.return_value = json.dumps(mock_response)

    prompt = [{"role": "user", "content": ["Test Prompt", {"image": "base64data"}]}]
    labels = get_openai_labels(prompt)
    
    assert "labels" in labels, "Output should have 'labels' key."
    assert isinstance(labels["labels"], list), "Labels should be a list."
    assert "man" in labels["labels"], "Expected label 'man' missing."


@mock.patch("visual_scout.extract_visual_content.get_openai_labels")
def test_process_images(mock_get_labels, temp_image):
    """
    Tests if `process_images` correctly processes image grids and generates JSON output.
    """
    temp_input_dir = tempfile.mkdtemp()
    temp_output_dir = tempfile.mkdtemp()
    os.makedirs(os.path.join(temp_input_dir, "video1"))

    # Create a test image
    image_path = os.path.join(temp_input_dir, "video1", "frame_00-00-02_00-00-04.jpg")
    with open(image_path, "wb") as img:
        img.write(os.urandom(1024))  # Fake image data

    # Mock OpenAI response
    mock_get_labels.return_value = {"labels": ["man", "tree", "building"]}

    # Run the function
    process_images()

    # Check if JSON output exists
    output_json_path = os.path.join(temp_output_dir, "video1", "visual_content_00-00-02_00-00-04.json")
    assert os.path.exists(output_json_path), "Output JSON file was not created."

    # Load and check JSON content
    with open(output_json_path, "r", encoding="utf-8") as json_file:
        data = json.load(json_file)
        assert "labels" in data, "JSON output should contain 'labels'."
        assert "man" in data["labels"], "Expected label 'man' missing."


def test_combine_visual_content_json(temp_json_file):
    """
    Tests if `combine_visual_content_json` merges multiple JSON files correctly.
    """
    temp_dir = tempfile.mkdtemp()
    video_name = "test_video"
    json_files = [temp_json_file]

    combine_visual_content_json(video_name, temp_dir, json_files)

    combined_path = os.path.join(temp_dir, f"{video_name}.json")
    assert os.path.exists(combined_path), "Combined JSON file was not created."

    with open(combined_path, "r", encoding="utf-8") as file:
        data = json.load(file)
        assert "00-00-02_00-00-04" in data, "Timestamp key missing in combined JSON."
        assert "man" in data["00-00-02_00-00-04"], "Expected label missing in combined JSON."
