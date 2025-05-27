import argparse
import sys
from pathlib import Path
from typing import List, Optional
from .pipeline_orchestration import (
    crawl_content,
    sort_files,
    parse_files,
    embed_chunks_from_dir,
)
from .directory_utils import get_step_dir
from ...logger.logging_config import get_logger

# Set up logging
logger = get_logger("pipeline.cli")


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Metropole.AI Content Processing Pipeline"
    )

    # Step selection
    parser.add_argument(
        "--step",
        choices=["crawl", "sort", "parse", "embed", "all"],
        required=True,
        help="Pipeline step to execute",
    )

    # Production flag
    parser.add_argument(
        "--production",
        action="store_true",
        help="Run in production mode (outputs to prod/ subdirectory)",
    )

    # Input/output paths
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Input URL (for web crawling) or directory path (for local processing)",
    )
    parser.add_argument(
        "--output", type=str, required=True, help="Base output directory path"
    )

    # Database settings
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

    # Optional limits
    parser.add_argument(
        "--n-limit",
        type=int,
        help="Limit number of files to process (for parse/embed steps)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        help="Maximum number of pages to crawl",
    )

    return parser.parse_args(args)


def main():
    """Main entry point for the pipeline CLI."""
    parsed_args = parse_args()

    # Convert output path to Path object
    output_dir = Path(parsed_args.output)

    # Use the provided collection name directly
    collection_name = parsed_args.collection

    try:
        if parsed_args.step == "crawl":
            # Crawl content
            logger.info(f"Starting crawl step with input: {parsed_args.input}")
            crawl_content(
                parsed_args.input,  # Keep as string for URL
                output_dir,
                parsed_args.allowed_domains,
                parsed_args.production,
            )
            logger.info(
                f"Crawled content saved to {get_step_dir(output_dir, 'crawl', parsed_args.production)}"
            )

        elif parsed_args.step == "sort":
            # Sort files
            logger.info(f"Starting sort step with input: {parsed_args.input}")
            sorted_files = sort_files(
                Path(parsed_args.input),  # Use Path object
                output_dir,
                parsed_args.production,
            )
            logger.info(
                f"Sorted {len(sorted_files)} files to {get_step_dir(output_dir, 'sort', parsed_args.production)}"
            )

        elif parsed_args.step == "parse":
            # Parse files
            logger.info(f"Starting parse step with input: {parsed_args.input}")
            parsed_files, parse_errors = parse_files(
                Path(parsed_args.input),  # Use Path object
                output_dir,
                parsed_args.n_limit,
                parsed_args.production,
            )
            output_dir = get_step_dir(output_dir, "parse", parsed_args.production)
            logger.info(
                f"Parse completed. Processed {len(parsed_files)} files to {output_dir}"
            )
            if parse_errors:
                logger.warning(f"Parse completed with {len(parse_errors)} errors")

        elif parsed_args.step == "embed":
            # Embed chunks
            logger.info(f"Starting embed step with input: {parsed_args.input}")
            embedded_chunks = embed_chunks_from_dir(
                Path(parsed_args.input),  # Use Path object
                output_dir,
                collection_name,
                parsed_args.n_limit,
                parsed_args.production,
            )
            logger.info(
                f"Embedded {embedded_chunks} chunks to {get_step_dir(output_dir, 'embed', parsed_args.production)}"
            )

        elif parsed_args.step == "all":
            # Run full pipeline
            logger.info("Starting full pipeline execution")
            crawl_content(
                parsed_args.input,  # Keep as string for URL
                output_dir,
                parsed_args.allowed_domains,
                parsed_args.production,
            )
            logger.info(
                f"Crawled content saved to {get_step_dir(output_dir, 'crawl', parsed_args.production)}"
            )

            sorted_files = sort_files(
                get_step_dir(output_dir, "crawl", parsed_args.production),
                output_dir,
                parsed_args.production,
            )
            logger.info(
                f"Sorted {len(sorted_files)} files to {get_step_dir(output_dir, 'sort', parsed_args.production)}"
            )

            parsed_files = parse_files(
                get_step_dir(output_dir, "sort", parsed_args.production),
                output_dir,
                parsed_args.n_limit,
                parsed_args.production,
            )
            logger.info(
                f"Parsed {len(parsed_files)} files to {get_step_dir(output_dir, 'parse', parsed_args.production)}"
            )

            embedded_chunks = embed_chunks_from_dir(
                get_step_dir(output_dir, "parse", parsed_args.production),
                output_dir,
                collection_name,
                parsed_args.n_limit,
                parsed_args.production,
            )
            logger.info(
                f"Embedded {embedded_chunks} chunks to {get_step_dir(output_dir, 'embed', parsed_args.production)}"
            )

        else:
            logger.error(f"Unknown step: {parsed_args.step}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
