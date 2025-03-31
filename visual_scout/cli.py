import argparse
from visual_scout.extract_frames import main_extract_frames
from visual_scout.extract_labels import get_labels_main
from visual_scout.generate_grids import main_generate_grids
from visual_scout.estimate_processing_cost import estimate_processing_cost

def main():
    parser = argparse.ArgumentParser(prog="visual-scout", description="Visual Scout CLI for processing video and images.")
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    # Estimate Processing Cost
    parser_cost = subparsers.add_parser("estimate-cost", help="Estimate processing cost for video/images in a directory")
    parser_cost.add_argument("input_dir", type=str, help="Path to the directory containing videos/images  (eg visual_scout/example_input)")
    parser_cost.set_defaults(func=lambda args: estimate_processing_cost(args.input_dir))

    # Extract Frames
    parser_extract = subparsers.add_parser("extract-frames", help="Extract frames for all files within input directory")
    parser_extract.add_argument("input_dir", type=str, help="Path to the video file")
    parser_extract.set_defaults(func=lambda args: main_extract_frames(args.input_dir))

    # Generate Grids
    parser_grids = subparsers.add_parser("generate-grids", help="Generate image grids from extracted frames")
    parser_grids.add_argument("--grid-size", type=int, default=3, help="Grid dimension (NxN), default is 3x3")
    parser_grids.set_defaults(func=lambda args: main_generate_grids(args.grid_size))

    # Process Visual Content (generate labels)
    parser_process = subparsers.add_parser("generate-labels", help="Process image grids to generate labels")

    # Add required OpenAI key argument
    parser_process.add_argument(
        "--open-ai-key",
        type=str,
        required=True,
        help="API key for OpenAI authentication (required)."
    )

    # Add optional OpenAI model argument with a default value
    parser_process.add_argument(
        "--open-ai-model",
        type=str,
        default="gpt-4o-mini",
        help="Specify the OpenAI model to use (default: gpt-4o-mini)."
    )

    # Ensure function gets args
    parser_process.set_defaults(func=lambda args: get_labels_main(args.open_ai_key, args.open_ai_model))
    # Parse arguments
    args = parser.parse_args()

    # If no command is given, print help
    if not args.command:
        parser.print_help()
        return

    # Call the appropriate function
    args.func(args)

if __name__ == "__main__":
    main()
