import os
import json
import time
from dotenv import load_dotenv
import openai
import warnings 
from visual_scout.image_utils import extract_timestamps, validate_filenames
from visual_scout.openai_utils import get_label_gen_prompt


def get_openai_labels(prompt, open_ai_key, open_ai_model):
    """
    Call the OpenAI API to generate labels for a given image based on the provided prompt.

    This function sends a request to OpenAI's chat completion model, processes the response, 
    and extracts structured labels for objects, actions, and visible text in the image.

    Args:
        prompt (dict): A dictionary containing the message structure required for the OpenAI API.

    Returns:
        dict: A dictionary with a single key `"labels"`, containing an array of generated labels. 
              If the API refuses processing, returns a warning message inside the labels array.
              If the request fails after 3 attempts, returns an error message inside the labels array.

    Error Handling:
        - Retries up to 3 times in case of API failure, with exponential backoff.
        - Captures OpenAI refusals and includes a warning in the output.
        - Logs errors and provides feedback if the request ultimately fails.

    Example Output:
        {
            "labels": [
                "man",
                "sunglasses",
                "hat",
                "protesting",
                "crowd",
                "visible text: 'Leave the canal!': Panamanians protest against Trump outside US Embassy"
            ]
        }
    
    """
    openai_client, open_ai_model = get_open_ai_client_model(open_ai_key, open_ai_model)

    params = {
        "model": open_ai_model,
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

            token_data = response.usage
            input_tokens = token_data.prompt_tokens
            output_tokens = token_data.completion_tokens
            print(f"input_tokens: \n{input_tokens}")
            print(f"output_tokens: \n{output_tokens}")
            return json.loads(content)

        except Exception as e:
            if attempt == 2:
                return {"labels": [f"Error: OpenAI request failed after 3 attempts: {str(e)}"]}
            print(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {2 * (attempt + 1)} seconds...")
            time.sleep(2 * (attempt + 1))

    return {}


def process_images(input_dir, output_dir, open_ai_key, open_ai_model): 
    """
    """
    validate_filenames(input_dir)  # Ensure input filenames are correctly formatted before processing

    for root, _, files in os.walk(input_dir):
        if not files:
            continue

        video_name = os.path.basename(root)
        output_subdir = os.path.join(output_dir, video_name)

        if output_subdir != "output_visual_content/output_grids":
            os.makedirs(output_subdir, exist_ok=True)

        processed_files = []

        for file in sorted(files):
            if not file.lower().endswith((".jpg", ".jpeg", ".png")):
                warnings.warn("")
                continue  # Skip non-image files

            image_path = os.path.join(root, file)
            print(f"\n\nimage_path: {image_path}")
            timestamps = extract_timestamps(file)

            if not timestamps:
                continue  # Skip files without correct timestamps

            start_time, end_time = timestamps

            # Get labels from OpenAI
            prompt = get_label_gen_prompt(image_path)

            # TEMP - USE TEST THIS TO TEST without sending API requests
            response = get_openai_labels(prompt, open_ai_key, open_ai_model)
            # response = {'labels': ['man', 'woman', 'flags', 'crowd', 'banner', "visible text: 'PANAMA CITY'", "visible text: 'MI PAÍS, MI SOBERANÍA, MI CANAL' (translation from Spanish: 'MY COUNTRY, MY SOVEREIGNTY, MY CANAL')", "visible text: 'ASOPROF'", "visible text: 'SINDICATO PÚBLICO' (translation from Spanish: 'PUBLIC UNION')", 'hat', 'sunglasses', 'blue shirt', 'red shirt']}

            # Save JSON file
            time_key = f"{start_time}_{end_time}"
            output_filename = f"visual_content_{time_key}.json"
            output_path = os.path.join(output_subdir, output_filename)
            
            if output_subdir != "output_visual_content/output_grids":
                with open(output_path, "w", encoding="utf-8") as json_file:
                    json.dump(response, json_file, indent=2)

                print(f"\n✅ Processed: {image_path} → {output_path}")
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
    combined_video_json_name = video_name.replace("__frames__grids", "__visual_content")
    combined_output_path = os.path.join(output_subdir, f"{combined_video_json_name}.json")

    with open(combined_output_path, "w", encoding="utf-8") as combined_file:
        json.dump(combined_data, combined_file, indent=2)

    print(f"📄 Combined visual content JSON saved: {combined_output_path}")


def get_open_ai_client_model(open_ai_key, open_ai_model):
    if not open_ai_model:
        open_ai_model = os.getenv("OPENAI_MODEL")

    if not open_ai_key:
        # If not called from cli with api key, get from env
        # Load environment variables
        load_dotenv()

        open_ai_key = os.getenv("OPENAI_KEY")

    if not open_ai_key or not open_ai_model:
        raise ValueError("Missing required environment variables: open_ai_key and openai_model")

    openai_client = openai.OpenAI(api_key=open_ai_key)

    return openai_client, open_ai_model


def get_labels_main(open_ai_key, open_ai_model):

    base_dir = os.getcwd()
    
    # Define input and output directories
    input_directory = os.path.join(base_dir, "output", "output_grids")
    output_directory = os.path.join(base_dir, "output", "output_labels")
    
    print(f"\nChecking input frames from: {input_directory}")

    # Ensure input grid directory exists and is not empty
    if not os.path.exists(input_directory) or not os.listdir(input_directory):
        raise FileNotFoundError(f"❌ Error: Input grids directory '{input_directory}' does not exist or exists but is empty - be sure to generate frames before generating grids.")

    # Create output directory to hold output jsons
    os.makedirs(output_directory, exist_ok=True)
    print(f"\nOutput label jsons will be saved to: {output_directory}")

    # Proceed with label generation
    process_images(input_directory, output_directory, open_ai_key, open_ai_model)


if __name__ == "__main__":
    print("\nStarting extraction of visual content...")
    process_images()
