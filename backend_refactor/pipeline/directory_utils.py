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


def clean_environment(output_dir: Path, production: bool = False) -> None:
    """
    Clean all pipeline step directories within the specified environment.
    Only cleans the selected environment (dev or prod), leaving the other untouched.
    """
    env_dir = get_environment_dir(output_dir, production)

    # Ensure we're only cleaning within the output directory
    if not str(env_dir).startswith(str(output_dir)):
        raise ValueError(
            f"Attempted to clean directory outside output directory: {env_dir}"
        )

    # Clean each step directory
    for step in PIPELINE_STEPS:
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


def validate_db_path(db_path: str, output_dir: Path) -> None:
    """
    Validate that the database path is not inside the output directory.
    Raises ValueError if the path is invalid.
    """
    db_path_obj = Path(db_path)
    if db_path_obj.is_relative_to(output_dir):
        raise ValueError(
            f"Database path ({db_path}) cannot be inside the output directory ({output_dir}). "
            "Please specify a path outside the output directory."
        )
