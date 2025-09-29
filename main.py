"""
Enterprise Data Collector v2.0 - Enhanced
Main entry point for the application
Author: MiniMax Agent
"""

import sys
import os
import asyncio
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Set asyncio event loop policy for Windows
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Import after path setup
from src.ui.main_window import main
from src.logger import setup_logger


def setup_application():
    """
    Setup application environment
    """
    # Create necessary directories
    directories = ["Database", "Outputs", "Logs", "docs", "samples"]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    # Setup main logger
    logger = setup_logger(
        name="EnterpriseDataCollector",
        level="INFO",
        log_dir="Logs",
        console_output=True,
        file_output=True
    )
    
    logger.info("Enterprise Data Collector v2.0 - Enhanced starting up...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    return logger


if __name__ == "__main__":
    try:
        # Setup application
        logger = setup_application()
        
        # Start GUI application
        logger.info("Starting GUI application...")
        main()
        
    except Exception as e:
        print(f"Failed to start application: {e}")
        sys.exit(1)