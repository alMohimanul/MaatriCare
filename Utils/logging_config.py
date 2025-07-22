# ============= Logging Configuration Module =============
"""
Centralized logging configuration for MaatriCare Agent system.
This module sets up file-based logging with rotation and console output.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from Utils.constants import LoggingConfig


def setup_logging() -> logging.Logger:
    """
    Set up comprehensive logging for the MaatriCare Agent system.

    Creates:
    - File handler with rotation (app.log)
    - Console handler for immediate feedback
    - Proper formatting and log levels

    Returns:
        logging.Logger: Configured root logger for the application
    """

    # Create logs directory if it doesn't exist
    log_dir = Path(LoggingConfig.LOG_DIR)
    log_dir.mkdir(exist_ok=True)

    # Full path to log file
    log_file_path = log_dir / LoggingConfig.LOG_FILE_NAME

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LoggingConfig.DEFAULT_LEVEL))

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        fmt=LoggingConfig.LOG_FORMAT, datefmt=LoggingConfig.DATE_FORMAT
    )

    # File handler with rotation
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_file_path),
            maxBytes=LoggingConfig.MAX_FILE_SIZE_MB
            * 1024
            * 1024,  # Convert MB to bytes
            backupCount=LoggingConfig.BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(getattr(logging, LoggingConfig.DEFAULT_LEVEL))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        # Log the setup success
        logging.info(f"✅ Logging initialized - File: {log_file_path}")

    except Exception as e:
        print(f"❌ Failed to set up file logging: {e}")
        # Continue without file logging if there's an issue

    # Console handler (optional)
    if LoggingConfig.ENABLE_CONSOLE_OUTPUT:
        try:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, LoggingConfig.CONSOLE_LEVEL))
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

        except Exception as e:
            print(f"❌ Failed to set up console logging: {e}")

    return root_logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name (str, optional): Logger name, usually __name__. If None, returns root logger.

    Returns:
        logging.Logger: Logger instance for the specified module
    """
    if name:
        return logging.getLogger(name)
    return logging.getLogger()


def log_system_info():
    """Log basic system information at startup."""
    logger = get_logger("MaatriCare.SystemInfo")
    logger.info("=" * 60)
    logger.info("🏥 MaatriCare Agent System Starting Up")
    logger.info("=" * 60)
    logger.info(f"📁 Working Directory: {os.getcwd()}")
    logger.info(
        f"📝 Log File: {Path(LoggingConfig.LOG_DIR) / LoggingConfig.LOG_FILE_NAME}"
    )
    logger.info(f"🔧 Log Level: {LoggingConfig.DEFAULT_LEVEL}")
    logger.info(f"💾 Max File Size: {LoggingConfig.MAX_FILE_SIZE_MB}MB")
    logger.info(f"🔄 Backup Count: {LoggingConfig.BACKUP_COUNT}")
    logger.info("=" * 60)


def log_shutdown():
    """Log system shutdown information."""
    logger = get_logger("MaatriCare.SystemInfo")
    logger.info("=" * 60)
    logger.info("🏥 MaatriCare Agent System Shutting Down")
    logger.info("=" * 60)


# Module-level function for easy import
def init_logging() -> logging.Logger:
    """
    Initialize logging and return the root logger.
    This is the main function to call when setting up the application.

    Returns:
        logging.Logger: Configured root logger
    """
    logger = setup_logging()
    log_system_info()
    return logger


# For backward compatibility and easy access
def get_app_logger() -> logging.Logger:
    """Get the main application logger."""
    return get_logger("MaatriCare.Agent")


if __name__ == "__main__":
    # Test the logging setup
    test_logger = init_logging()
    test_logger.info("🧪 Testing logging configuration")
    test_logger.warning("🟡 This is a warning message")
    test_logger.error("🔴 This is an error message")
    test_logger.critical("🚨 This is a critical message")

    # Test module-specific logger
    module_logger = get_logger("TestModule")
    module_logger.info("📦 Module-specific logger test")

    log_shutdown()
    print("✅ Logging test completed. Check the logs directory.")
