import shutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Define the pipeline steps
PIPELINE_STEPS = ["crawled", "parsed", "embedded"]


def get_environment_dir(output_dir: Path, production: bool = False) -> Path:
    """Get the environment directory (dev or prod) within the output directory."""
    env = "prod" if production else "dev"
    return output_dir / env


def get_step_dir(output_dir: Path, step: str, production: bool = False) -> Path:
    """Get the directory for a specific pipeline step within the environment."""
    env_dir = get_environment_dir(output_dir, production)
    return env_dir / step


def clean_environment(
    output_dir: Path, steps_to_clean: list[str], production: bool = False
) -> None:
    """
    Clean specific pipeline step directories within the specified environment.
    Only cleans the selected steps and environment (dev or prod), leaving others untouched.

    Args:
        output_dir: The root output directory
        steps_to_clean: List of pipeline steps to clean (e.g. ["crawled", "parsed"])
        production: Whether to clean production or development environment
    """
    env_dir = get_environment_dir(output_dir, production)

    # Ensure we're only cleaning within the output directory
    if not str(env_dir).startswith(str(output_dir)):
        raise ValueError(
            f"Attempted to clean directory outside output directory: {env_dir}"
        )

    # Validate that all requested steps are valid pipeline steps
    invalid_steps = [step for step in steps_to_clean if step not in PIPELINE_STEPS]
    if invalid_steps:
        raise ValueError(
            f"Invalid pipeline steps requested for cleaning: {invalid_steps}. "
            f"Valid steps are: {PIPELINE_STEPS}"
        )

    # Clean each requested step directory
    for step in steps_to_clean:
        step_dir = env_dir / step
        if step_dir.exists():
            logger.info(f"Cleaning {step_dir}")
            shutil.rmtree(step_dir)
        step_dir.mkdir(parents=True, exist_ok=True)


def ensure_directory_structure(output_dir: Path, production: bool = False) -> None:
    """
    Ensure the pipeline directory structure exists for the specified environment.
    Creates all necessary directories if they don't exist.
    """
    env_dir = get_environment_dir(output_dir, production)

    # Create environment directory
    env_dir.mkdir(parents=True, exist_ok=True)

    # Create step directories
    for step in PIPELINE_STEPS:
        step_dir = env_dir / step
        step_dir.mkdir(parents=True, exist_ok=True)
