import argparse
import sys
from pathlib import Path
from typing import List, Optional
from .pipeline_orchestration import (
    run_pipeline,
    crawl_content,
    parse_files,
    embed_chunks_from_dir,
)
from .directory_utils import ensure_directory_structure


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Metropole.AI Content Processing Pipeline"
    )

    # Step selection
    parser.add_argument(
        "--step",
        choices=["crawl", "parse", "embed", "crawl_and_parse", "all"],
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
    parser.add_argument(
        "--allowed-extensions",
        type=str,
        nargs="+",
        help="List of allowed file extensions for local processing",
    )

    # Optional limits
    parser.add_argument(
        "--n-limit",
        type=int,
        help="Limit number of files to process (for parse/embed steps)",
    )

    return parser.parse_args(args)


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the pipeline CLI."""
    try:
        parsed_args = parse_args(args)
        output_dir = Path(parsed_args.output)

        # Ensure directory structure exists
        ensure_directory_structure(output_dir, parsed_args.production)

        # Get collection name based on production mode
        collection_name = (
            f"{parsed_args.collection}_{'prod' if parsed_args.production else 'dev'}"
        )

        if parsed_args.step == "crawl":
            crawled_files, errors = crawl_content(
                input_source=parsed_args.input,
                output_dir=output_dir,
                allowed_domains=parsed_args.allowed_domains,
                allowed_extensions=parsed_args.allowed_extensions,
                production=parsed_args.production,
            )
            if errors:
                print(f"Warning: Crawl completed with {len(errors)} errors")
            print(f"Crawled {len(crawled_files)} files")

        elif parsed_args.step == "parse":
            parsed_files, errors = parse_files(
                input_dir=Path(parsed_args.input),
                output_dir=output_dir,
                allowed_extensions=parsed_args.allowed_extensions,
                n_limit=parsed_args.n_limit,
                production=parsed_args.production,
            )
            if errors:
                print(f"Warning: Parse completed with {len(errors)} errors")
            print(f"Parsed {len(parsed_files)} files")

        elif parsed_args.step == "embed":
            n_embedded, errors = embed_chunks_from_dir(
                input_dir=Path(parsed_args.input),
                output_dir=output_dir,
                collection_name=collection_name,
                n_limit=parsed_args.n_limit,
                production=parsed_args.production,
            )
            if errors:
                print(f"Warning: Embed completed with {len(errors)} errors")
            print(f"Embedded {n_embedded} files")

        elif parsed_args.step == "crawl_and_parse":
            # First crawl
            crawled_files, crawl_errors = crawl_content(
                input_source=parsed_args.input,
                output_dir=output_dir,
                allowed_domains=parsed_args.allowed_domains,
                allowed_extensions=parsed_args.allowed_extensions,
                production=parsed_args.production,
            )
            if crawl_errors:
                print(f"Warning: Crawl completed with {len(crawl_errors)} errors")
            print(f"Crawled {len(crawled_files)} files")

            # Then parse the crawled files
            parsed_files, parse_errors = parse_files(
                input_dir=output_dir
                / ("prod" if parsed_args.production else "dev")
                / "crawled",
                output_dir=output_dir,
                allowed_extensions=parsed_args.allowed_extensions,
                n_limit=parsed_args.n_limit,
                production=parsed_args.production,
            )
            if parse_errors:
                print(f"Warning: Parse completed with {len(parse_errors)} errors")
            print(f"Parsed {len(parsed_files)} files")

        elif parsed_args.step == "all":
            result = run_pipeline(
                input_source=parsed_args.input,
                output_dir=output_dir,
                collection_name=collection_name,
                allowed_domains=parsed_args.allowed_domains,
                allowed_extensions=parsed_args.allowed_extensions,
                production=parsed_args.production,
            )
            print(f"Pipeline completed. Results saved to: {result['output_dir']}")
            if result.get("web_crawled_files"):
                print(f"Web content: {result['web_crawled_files']} files crawled")
            if result.get("local_crawled_files"):
                print(f"Local content: {result['local_crawled_files']} files processed")
            print(f"Total files parsed: {result['parsed_files']}")
            print(f"Total files embedded: {result['embedded_files']}")

        return 0

    except Exception as e:
        print(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
