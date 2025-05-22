import argparse
import sys
from pathlib import Path
from typing import List, Optional
from .pipeline_runner import run_web_pipeline, run_local_pipeline


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Metropole.AI Content Processing Pipeline"
    )

    # Mode selection
    parser.add_argument(
        "--mode",
        choices=["web", "local", "all"],
        required=True,
        help="Processing mode: web (URL crawling), local (file processing), or all",
    )

    # Production flag
    parser.add_argument(
        "--production",
        action="store_true",
        help="Run in production mode with additional logging and error handling",
    )

    # Input/output paths
    parser.add_argument(
        "--input",
        type=str,
        help="Input URL (for web mode) or directory path (for local mode)",
    )
    parser.add_argument(
        "--output", type=str, required=True, help="Output directory path"
    )

    # Database settings
    parser.add_argument(
        "--db-path", type=str, required=True, help="Path to ChromaDB database"
    )
    parser.add_argument(
        "--collection", type=str, required=True, help="ChromaDB collection name"
    )

    # Optional filters
    parser.add_argument(
        "--allowed-domains",
        type=str,
        nargs="+",
        help="List of allowed domains for web crawling",
    )
    parser.add_argument(
        "--allowed-extensions",
        type=str,
        nargs="+",
        help="List of allowed file extensions for local processing",
    )

    return parser.parse_args(args)


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the pipeline CLI."""
    try:
        parsed_args = parse_args(args)
        output_dir = Path(parsed_args.output)
        output_dir.mkdir(parents=True, exist_ok=True)

        if parsed_args.production:
            # TODO: Add production-specific logging and error handling
            pass

        if parsed_args.mode in ["web", "all"]:
            if not parsed_args.input:
                print("Error: --input URL is required for web mode")
                return 1

            print(f"Running web pipeline for URL: {parsed_args.input}")
            result = run_web_pipeline(
                url=parsed_args.input,
                output_dir=output_dir / "web",
                db_path=parsed_args.db_path,
                collection_name=parsed_args.collection,
                allowed_domains=parsed_args.allowed_domains,
            )
            print(f"Web pipeline completed. Results saved to: {result['parsed_json']}")

        if parsed_args.mode in ["local", "all"]:
            if not parsed_args.input:
                print("Error: --input directory is required for local mode")
                return 1

            input_dir = Path(parsed_args.input)
            if not input_dir.exists():
                print(f"Error: Input directory does not exist: {input_dir}")
                return 1

            print(f"Running local pipeline for directory: {input_dir}")
            result = run_local_pipeline(
                input_dir=input_dir,
                output_dir=output_dir / "local",
                db_path=parsed_args.db_path,
                collection_name=parsed_args.collection,
                allowed_extensions=parsed_args.allowed_extensions,
            )
            print(
                f"Local pipeline completed. Results saved to: {result['parsed_json']}"
            )

        return 0

    except Exception as e:
        print(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
