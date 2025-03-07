import argparse
from visual_scout.extract_frames import main_extract_frames
from visual_scout.extract_visual_content import process_images
from visual_scout.generate_grids import main_generate_grids

def main():
    parser = argparse.ArgumentParser(prog="visual-scout", description="Visual Scout CLI for processing video and images.")
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    # Extract Frames
    parser_extract = subparsers.add_parser("extract-frames", help="Extract frames for all files within input directory")
    parser_extract.add_argument("input_dir", type=str, help="Path to the video file")
    parser_extract.set_defaults(func=lambda args: main_extract_frames(args.input_dir))

    # Generate Grids
    parser_grids = subparsers.add_parser("generate-grids", help="Generate image grids from extracted frames")
    parser_grids.add_argument("--grid-size", type=int, default=3, help="Grid dimension (NxN), default is 3x3")
    parser_grids.set_defaults(func=lambda args: main_generate_grids(args.grid_size))

    # # Process Visual Content
    # parser_process = subparsers.add_parser("process-images", help="Process image grids and generate labels")
    # parser_process.add_argument("--input-dir", type=str, default="output_grids", help="Input directory for image grids")
    # parser_process.add_argument("--output-dir", type=str, default="output_visual_content", help="Output directory for JSON results")
    # parser_process.set_defaults(func=lambda args: process_images(args.input_dir, args.output_dir))

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
