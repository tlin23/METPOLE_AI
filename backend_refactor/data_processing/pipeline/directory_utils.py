"""Directory utilities for the pipeline."""

import shutil
from pathlib import Path
from typing import List
from ..logger.logging_config import get_logger

logger = get_logger("pipeline.directory_utils")

# Pipeline steps in order with their directory names
PIPELINE_STEPS = {
    "crawl": "local_input_source",
    "sort": "sorted_documents",
    "parse": "json_chunks",
    "embed": "chroma_db",
}

# Allowed file extensions for sorting
ALLOWED_EXTENSIONS = [".pdf", ".docx", ".html"]


def get_base_dir(data_dir: Path, production: bool = False) -> Path:
    """Get the base directory for the current environment (dev/prod).

    Args:
        data_dir: Root data directory
        production: Whether to use production environment

    Returns:
        Path to the environment directory (dev/prod)
    """
    env = "prod" if production else "dev"
    return data_dir / env


def get_step_dir(data_dir: Path, step: str, production: bool = False) -> Path:
    """Get the directory for a specific pipeline step.

    Args:
        data_dir: Root data directory
        step: Pipeline step name (crawl, sort, parse, embed)
        production: Whether to use production environment

    Returns:
        Path to the step directory

    Raises:
        ValueError: If step is invalid
    """
    if step not in PIPELINE_STEPS:
        raise ValueError(
            f"Invalid step: {step}. Valid steps are: {list(PIPELINE_STEPS.keys())}"
        )

    base_dir = get_base_dir(data_dir, production)
    return base_dir / PIPELINE_STEPS[step]


def _ensure_directory_exists(directory: Path, clean: bool = False) -> None:
    """Ensure a directory exists, optionally cleaning it first.

    Args:
        directory: Directory to ensure exists
        clean: Whether to clean the directory if it exists
    """
    if clean and directory.exists():
        logger.info(f"Cleaning directory: {directory}")
        shutil.rmtree(directory)

    if not directory.exists():
        logger.info(f"Creating directory: {directory}")
        directory.mkdir(parents=True)
    elif not clean:
        logger.debug(f"Directory already exists: {directory}")


def clean_step(data_dir: Path, step: str, production: bool = False) -> None:
    """Clean up files for a specific pipeline step.

    Args:
        data_dir: Root data directory
        step: Pipeline step to clean
        production: Whether to clean production environment
    """
    step_dir = get_step_dir(data_dir, step, production)

    if step_dir.exists():
        # For all steps, just remove the directory and recreate it
        logger.info(f"Cleaning directory: {step_dir}")
        shutil.rmtree(step_dir)
        step_dir.mkdir(parents=True)
        logger.info(f"Created clean directory: {step_dir}")


def get_downstream_steps(start_step: str) -> List[str]:
    """Get all steps that come after the given step in the pipeline order.

    Args:
        start_step: The step to start from (inclusive)

    Returns:
        List of steps including and after the start step

    Raises:
        ValueError: If start_step is invalid
    """
    if start_step not in PIPELINE_STEPS:
        raise ValueError(
            f"Invalid step: {start_step}. Valid steps are: {list(PIPELINE_STEPS.keys())}"
        )

    steps = list(PIPELINE_STEPS.keys())
    start_idx = steps.index(start_step)
    return steps[start_idx:]


def clean_pipeline(data_dir: Path, start_step: str, production: bool = False) -> None:
    """Clean pipeline step directories starting from the given step.

    Args:
        data_dir: Root data directory
        start_step: The step to start cleaning from (inclusive)
        production: Whether to clean production environment
    """
    steps_to_clean = get_downstream_steps(start_step)
    logger.info(f"Cleaning pipeline steps: {', '.join(steps_to_clean)}")

    for step in steps_to_clean:
        logger.info(f"Cleaning step: {step}")
        clean_step(data_dir, step, production)
