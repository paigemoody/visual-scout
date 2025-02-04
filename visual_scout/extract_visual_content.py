import os
import json
import time
import sys
from dotenv import load_dotenv
import openai
from visual_scout.image_utils import encode_image_to_base64, extract_timestamps, validate_filenames

# Load environment variables
load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")

if not OPENAI_KEY or not OPENAI_MODEL:
    raise ValueError("Missing required environment variables: OPENAI_KEY and OPENAI_MODEL")

openai_client = openai.OpenAI(api_key=OPENAI_KEY)

# Define directories
INPUT_DIR = "output_grids"
OUTPUT_DIR = "output_visual_content"


def get_label_gen_prompt(image_path):
    """Generate the OpenAI prompt for image labeling."""
    image_bytes = encode_image_to_base64(image_path)
    image_data = {"image": image_bytes, "resize": 768}

    prompt = """

    Analyze the provided image grid and generate detailed labels identifying all visible objects, actions, icons, and visible text. 
    This is intended to help researchers efficiently review video content and determine which segments warrant further examination.

    Core Requirements:
    1. Object Identification
    - Label all distinct visible objects individually (e.g., "man," "sunglasses," "hat," rather than "man wearing sunglasses and a hat").
    - If an object appears multiple times across different frames, label it only once.

    2. Action Recognition
    - Identify visible actions (e.g., "protesting," "speaking into microphone," "holding flag," "walking").
    - Where possible, associate actions with subjects (e.g., "man speaking into microphone").

    3. Visible Text Extraction
    - Extract all visible text using the format: "visible text: [text]".
    - If text is non-English, provide both the original and a translation using the format:
        "visible text: [original] (translation from [language]: [translation])".

    4. UI & Functional Elements
    - Label interface elements such as icons (e.g., "YouTube Like button," "Dislike button," "Subscribe button").
    - Identify platform-specific elements (e.g., "video timestamp," "news channel logo").

    Output Format:
    Return a JSON object with a single key "labels" containing an array of categorized entries.

    Example Output:
    {
    "labels": [
        "man",
        "sunglasses",
        "hat",
        "protesting",
        "crowd",
        "flag",
        "visible text: 'Leave the canal!': Panamanians protest against Trump outside US Embassy",
        "visible text: 'Panama is a sovereign territory'",
        "visible text: 'Noticias' (translation from Spanish: 'News')",
        "YouTube Like button",
        "YouTube Dislike button",
        "news channel logo"
    ]
    }
    """

    return [{"role": "user", "content": [prompt, image_data]}]


def get_openai_labels(prompt):
    """Call OpenAI API to get labels for the given image."""
    params = {
        "model": OPENAI_MODEL,
        "messages": prompt,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"}
    }

    for attempt in range(3):  # Retry up to 3 times
        try:
            response = openai_client.chat.completions.create(**params)
            response_json = json.loads(response.model_dump_json())

            if refusal := response_json["choices"][0]["message"].get("refusal"):
                return {"labels": [f"Warning: OpenAI refused processing: {refusal}"]}

            content = response_json["choices"][0]["message"]["content"]
            return json.loads(content)

        except Exception as e:
            if attempt == 2:
                return {"labels": [f"Error: OpenAI request failed after 3 attempts: {str(e)}"]}
            print(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {2 * (attempt + 1)} seconds...")
            time.sleep(2 * (attempt + 1))

    return {}


def process_images():
    """Process all images in `output_grids/` and save labeled JSONs."""
    validate_filenames(INPUT_DIR)  # Ensure filenames are correctly formatted before processing

    for root, _, files in os.walk(INPUT_DIR):
        if not files:
            continue

        video_name = os.path.basename(root) #.replace("__frames__grids", "__grids_visual_content")
        output_subdir = os.path.join(OUTPUT_DIR, video_name)

        if output_subdir != "output_visual_content/output_grids":
            os.makedirs(output_subdir, exist_ok=True)

        processed_files = []

        for file in sorted(files):
            if not file.lower().endswith((".jpg", ".jpeg", ".png")):
                continue  # Skip non-image files

            image_path = os.path.join(root, file)
            timestamps = extract_timestamps(file)

            if not timestamps:
                continue  # Skip files without correct timestamps

            start_time, end_time = timestamps

            # Get labels from OpenAI
            prompt = get_label_gen_prompt(image_path)
            response = get_openai_labels(prompt)

            # TEMP - REMOVE THIS 
            # response = {'id': 'chatcmpl-AroXsGK9OTwXE4aSVoOm5xr9TD8p8', 'choices': [{'finish_reason': 'stop', 'index': 0, 'logprobs': None, 'message': {'content': '{"labels": ["indoor soccer","players","goal","blue team","yellow team","on-screen text: ARSENAL+ 3:4 REAL+","on-screen text: 2nd","on-screen text: 00:06","on-screen text: SHORT SPORT"]}', 'refusal': None, 'role': 'assistant', 'audio': None, 'function_call': None, 'tool_calls': None}}], 'created': 1737389044, 'model': 'gpt-4o-mini-2024-07-18', 'object': 'chat.completion', 'service_tier': 'default', 'system_fingerprint': 'fp_bd83329f63', 'usage': {'completion_tokens': 60, 'prompt_tokens': 1194, 'total_tokens': 1254, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}}

            # Save JSON file
            time_key = f"{start_time}_{end_time}"
            output_filename = f"visual_content_{time_key}.json"
            output_path = os.path.join(output_subdir, output_filename)
            print(output_path)
            
            if output_subdir != "output_visual_content/output_grids":
                with open(output_path, "w", encoding="utf-8") as json_file:
                    json.dump(response, json_file, indent=2)

                print(f"✅ Processed: {image_path} → {output_path}")
                processed_files.append(output_path)

        # After processing all images for this video, combine them into one JSON
        if output_subdir != "output_visual_content/output_grids":
            combine_visual_content_json(video_name, output_subdir, processed_files)


def combine_visual_content_json(video_name, output_subdir, json_files):
    """Combine all JSON files into a single file inside the same directory as the timestamped JSONs."""
    combined_data = {}

    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                time_key = os.path.basename(json_file).replace("visual_content_", "").replace(".json", "")
                combined_data[time_key] = data.get("labels", [])
        except Exception as e:
            print(f"⚠️ Warning: Skipping {json_file} due to error: {e}")

    # Save combined JSON file next to the timestamp JSONs
    combined_output_path = os.path.join(output_subdir, f"{video_name}.json")

    with open(combined_output_path, "w", encoding="utf-8") as combined_file:
        json.dump(combined_data, combined_file, indent=2)

    print(f"📄 Combined visual content JSON saved: {combined_output_path}")


if __name__ == "__main__":
    process_images()
