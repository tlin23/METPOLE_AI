import shutil
import logging
from pathlib import Path
from typing import List, Dict, Optional
import chromadb

logger = logging.getLogger(__name__)

# Define the pipeline steps in order
PIPELINE_STEPS = ["crawled", "parsed", "embedded"]

# Map steps to their corresponding DB collections (if any)
STEP_DB_COLLECTIONS: Dict[str, Optional[str]] = {
    "crawled": None,  # No DB collection for crawled step
    "parsed": None,  # No DB collection for parsed step
    "embedded": "chroma",  # ChromaDB collection for embedded step
}


def get_environment_dir(output_dir: Path, production: bool = False) -> Path:
    """Get the environment directory (dev or prod) within the output directory."""
    env = "prod" if production else "dev"
    return output_dir / env


def get_step_dir(output_dir: Path, step: str, production: bool = False) -> Path:
    """Get the directory for a specific pipeline step within the environment."""
    env_dir = get_environment_dir(output_dir, production)
    return env_dir / step


def get_downstream_steps(start_step: str) -> List[str]:
    """
    Get all steps that come after the given step in the pipeline order.

    Args:
        start_step: The step to start from (inclusive)

    Returns:
        List of steps including and after the start step
    """
    try:
        start_idx = PIPELINE_STEPS.index(start_step)
        return PIPELINE_STEPS[start_idx:]
    except ValueError:
        raise ValueError(
            f"Invalid pipeline step: {start_step}. Valid steps are: {PIPELINE_STEPS}"
        )


def clean_db_collection(collection_name: str, db_path: Path) -> None:
    """
    Clean a ChromaDB collection by deleting and recreating it.

    Args:
        collection_name: Name of the collection to clean
        db_path: Path to the ChromaDB database
    """
    try:
        client = chromadb.PersistentClient(path=str(db_path))
        # Delete collection if it exists
        try:
            client.delete_collection(name=collection_name)
            logger.info(f"Deleted ChromaDB collection: {collection_name}")
        except ValueError:
            # Collection doesn't exist, which is fine
            pass
        # Create new empty collection
        client.create_collection(name=collection_name)
        logger.info(f"Created new ChromaDB collection: {collection_name}")
    except Exception as e:
        logger.error(f"Failed to clean ChromaDB collection {collection_name}: {str(e)}")
        raise


def clean_environment(
    output_dir: Path,
    start_step: str,
    production: bool = False,
    collection_name: Optional[str] = None,
) -> None:
    """
    Clean pipeline step directories and DB collections starting from the given step.
    Cleans the specified step and all downstream steps.

    Args:
        output_dir: The root output directory
        start_step: The step to start cleaning from (inclusive)
        production: Whether to clean production or development environment
        collection_name: Name of the ChromaDB collection to clean (if cleaning embedded step)
    """
    env_dir = get_environment_dir(output_dir, production)

    # Ensure we're only cleaning within the output directory
    if not str(env_dir).startswith(str(output_dir)):
        raise ValueError(
            f"Attempted to clean directory outside output directory: {env_dir}"
        )

    # Get all steps to clean
    steps_to_clean = get_downstream_steps(start_step)

    # Clean each step directory
    for step in steps_to_clean:
        step_dir = env_dir / step
        if step_dir.exists():
            logger.info(f"Cleaning directory: {step_dir}")
            shutil.rmtree(step_dir)
        step_dir.mkdir(parents=True, exist_ok=True)

        # Clean associated DB collection if this step has one
        if STEP_DB_COLLECTIONS[step] and collection_name:
            clean_db_collection(collection_name, env_dir)


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
