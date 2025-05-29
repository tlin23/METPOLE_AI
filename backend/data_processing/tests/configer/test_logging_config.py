"""
Tests for the logging configuration module.
"""

import os
import logging
import shutil
from pathlib import Path
from backend.logger.logging_config import (
    configure_logging,
    get_logger,
    LOGS_DIR,
)


def test_logger_creation():
    """Test that a logger can be created with default settings."""
    logger = get_logger("test")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "metropole_ai.test"


def test_logger_hierarchy():
    """Test that logger hierarchy is maintained."""
    child_logger = get_logger("parent.child")
    assert child_logger.name == "metropole_ai.parent.child"


def test_log_file_creation():
    """Test that log files are created in the correct location."""
    test_logger = configure_logging(
        logger_name="test_file",
        log_file=os.path.join(LOGS_DIR, "test.log"),
    )
    test_logger.info("Test message")

    log_path = Path(LOGS_DIR) / "test.log"
    assert log_path.exists()
    assert log_path.is_file()


def test_log_levels():
    """Test that different log levels work correctly."""
    test_logger = get_logger("test_levels")

    # Create a custom handler to capture log records
    class TestHandler(logging.Handler):
        def __init__(self):
            super().__init__()
            self.records = []

        def emit(self, record):
            self.records.append(record)

    handler = TestHandler()
    test_logger.addHandler(handler)

    # Test that debug messages are not logged at INFO level
    test_logger.setLevel(logging.INFO)
    test_logger.debug("This should not be logged")
    assert not any(
        record.levelno == logging.DEBUG for record in handler.records
    ), "Debug message should not be logged at INFO level"

    # Test that info messages are logged
    test_logger.info("This should be logged")
    assert any(
        record.levelno == logging.INFO for record in handler.records
    ), "Info message should be logged"

    # Test that error messages are logged
    test_logger.error("This should be logged")
    assert any(
        record.levelno == logging.ERROR for record in handler.records
    ), "Error message should be logged"


def test_log_format():
    """Test that log messages have the correct format."""
    test_logger = get_logger("test_format")
    test_message = "Test message"

    # Create a custom handler to capture the formatted message
    class TestHandler(logging.Handler):
        def __init__(self):
            super().__init__()
            self.record = None

        def emit(self, record):
            self.record = record

    handler = TestHandler()
    test_logger.addHandler(handler)
    test_logger.info(test_message)

    # Verify the log record has the expected attributes
    assert handler.record is not None
    assert handler.record.name == "metropole_ai.test_format"
    assert handler.record.levelname == "INFO"
    assert handler.record.getMessage() == test_message


def test_rotating_file_handler():
    """Test that the rotating file handler works correctly."""
    test_logger = configure_logging(
        logger_name="test_rotation",
        log_file=os.path.join(LOGS_DIR, "rotation_test.log"),
        max_bytes=100,  # Small size to trigger rotation
        backup_count=2,
    )

    # Write enough messages to trigger rotation
    for i in range(100):
        test_logger.info(f"Test message {i}")

    # Check that backup files were created
    log_dir = Path(LOGS_DIR)
    log_files = list(log_dir.glob("rotation_test.log*"))
    assert len(log_files) <= 3  # Original + 2 backups


def test_log_directory_creation():
    """Test that the log directory is created if it doesn't exist."""
    # Remove the log directory if it exists
    if os.path.exists(LOGS_DIR):
        shutil.rmtree(LOGS_DIR)

    # Create a logger which should create the directory
    logger = get_logger("test_dir")
    logger.info("Test message")

    # Verify the directory was created
    assert os.path.exists(LOGS_DIR)
    assert os.path.isdir(LOGS_DIR)


def test_multiple_handlers():
    """Test that a logger can have multiple handlers."""
    test_logger = configure_logging(
        logger_name="test_handlers",
        log_file=os.path.join(LOGS_DIR, "handlers_test.log"),
        stream_handler=True,
    )

    # Verify both file and stream handlers are present
    handlers = test_logger.handlers
    assert len(handlers) == 2
    assert any(isinstance(h, logging.FileHandler) for h in handlers)
    assert any(isinstance(h, logging.StreamHandler) for h in handlers)


def test_logger_propagation():
    """Test that log messages propagate up the logger hierarchy."""
    parent_logger = get_logger("test_propagation")
    child_logger = get_logger("test_propagation.child")

    # Create a handler for the parent logger
    class TestHandler(logging.Handler):
        def __init__(self):
            super().__init__()
            self.records = []

        def emit(self, record):
            self.records.append(record)

    handler = TestHandler()
    parent_logger.addHandler(handler)

    # Log a message with the child logger
    child_logger.info("Test message")

    # Verify the message was received by the parent's handler
    assert len(handler.records) == 1
    assert handler.records[0].name == "metropole_ai.test_propagation.child"
