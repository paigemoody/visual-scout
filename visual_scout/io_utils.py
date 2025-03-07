import os

def make_output_dir(filepath, processing_step):
    """
    Create an output directory for a specific video processing step.

    This function generates a structured output directory path based on the input video file 
    and the specified processing step (e.g., "frames", "grids", "visual_content"). 
    If the directory does not exist, it is created.

    Args:
        filepath (str): The path to the input file.
        processing_step (str): The processing step name (e.g., "frames", "grids", "visual_content").

    Returns:
        str: The full path of the created output directory.
    """
    base_name = os.path.basename(filepath)
    name_without_ext = os.path.splitext(base_name)[0]
    output_dir = os.path.join("output", f"output_{processing_step}", f"{name_without_ext}__{processing_step}")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir
