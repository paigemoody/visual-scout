from visual_scout.utils.image_utils import encode_image_to_base64

PROMPT = """

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


def get_label_gen_prompt(image_path):
    """Generate the OpenAI prompt for image labeling."""
    image_bytes = encode_image_to_base64(image_path)
    image_data = {"image": image_bytes, "resize": 768}

    return [{"role": "user", "content": [PROMPT, image_data]}]
