"""
Application Logger for Enterprise Data Collector
Unicode support and structured logging
Author: MiniMax Agent
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional
import sys


def setup_logger(
    name: str = "EnterpriseDataCollector",
    level: str = "INFO",
    log_dir: str = "Logs",
    console_output: bool = True,
    file_output: bool = True,
    max_files: int = 5
) -> logging.Logger:
    """
    Thiết lập logger cho ứng dụng
    
    Args:
        name: Tên logger
        level: Mức độ log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Thư mục chứa log files
        console_output: Có xuất ra console không
        file_output: Có ghi vào file không
        max_files: Số file log tối đa giữ lại
        
    Returns:
        Logger instance
    """
    
    # Tạo logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Xóa các handler cũ (nếu có)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Formatter với Unicode support
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(getattr(logging, level.upper()))
        logger.addHandler(console_handler)
    
    # File handler
    if file_output:
        # Tạo thư mục logs nếu chưa có
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # Tên file log với timestamp
        log_filename = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_enterprise_collector.log"
        log_file_path = log_path / log_filename
        
        # File handler với UTF-8 encoding
        file_handler = logging.FileHandler(
            log_file_path, 
            mode='w', 
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, level.upper()))
        logger.addHandler(file_handler)
        
        # Cleanup old log files
        _cleanup_old_logs(log_path, max_files)
        
        logger.info(f"Log file created: {log_file_path}")
    
    logger.info(f"Logger '{name}' initialized with level {level}")
    return logger


def get_logger(name: str = "EnterpriseDataCollector") -> logging.Logger:
    """
    Lấy logger đã được thiết lập
    
    Args:
        name: Tên logger
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def _cleanup_old_logs(log_dir: Path, max_files: int):
    """
    Dọn dẹp các file log cũ
    
    Args:
        log_dir: Thư mục chứa log files
        max_files: Số file tối đa giữ lại
    """
    try:
        # Lấy tất cả các file log
        log_files = list(log_dir.glob("*_enterprise_collector.log"))
        
        # Sắp xếp theo thời gian tạo (mới nhất trước)
        log_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        
        # Xóa các file cũ vượt quá giới hạn
        for old_file in log_files[max_files:]:
            try:
                old_file.unlink()
                print(f"Deleted old log file: {old_file.name}")
            except Exception as e:
                print(f"Failed to delete old log file {old_file.name}: {e}")
                
    except Exception as e:
        print(f"Failed to cleanup old logs: {e}")


class DatabaseLogHandler(logging.Handler):
    """
    Custom log handler để ghi log vào database
    """
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
    
    def emit(self, record):
        """
        Emit log record to database
        """
        try:
            log_entry = self.format(record)
            self.db_manager.log_message(record.levelname, log_entry)
        except Exception:
            # Không được raise exception từ log handler
            pass


def setup_dual_logger(
    name: str = "EnterpriseDataCollector",
    level: str = "INFO",
    log_dir: str = "Logs",
    db_manager=None
) -> logging.Logger:
    """
    Thiết lập logger ghi vào cả file và database
    
    Args:
        name: Tên logger
        level: Mức độ log
        log_dir: Thư mục chứa log files
        db_manager: DatabaseManager instance
        
    Returns:
        Logger instance
    """
    
    logger = setup_logger(name, level, log_dir)
    
    # Thêm database handler nếu có
    if db_manager:
        db_handler = DatabaseLogHandler(db_manager)
        db_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        db_handler.setFormatter(db_formatter)
        logger.addHandler(db_handler)
        
        logger.info("Database logging enabled")
    
    return logger


class ColoredConsoleHandler(logging.StreamHandler):
    """
    Console handler với màu sắc cho các level khác nhau
    """
    
    # Màu sắc cho các level
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    
    RESET = '\033[0m'  # Reset color
    
    def emit(self, record):
        try:
            message = self.format(record)
            
            # Thêm màu sắc nếu hỗ trợ
            if hasattr(self.stream, 'isatty') and self.stream.isatty():
                color = self.COLORS.get(record.levelname, '')
                message = f"{color}{message}{self.RESET}"
            
            self.stream.write(message + '\n')
            self.flush()
            
        except Exception:
            self.handleError(record)


def setup_colored_logger(
    name: str = "EnterpriseDataCollector",
    level: str = "INFO",
    log_dir: str = "Logs"
) -> logging.Logger:
    """
    Thiết lập logger với console output có màu sắc
    
    Args:
        name: Tên logger
        level: Mức độ log
        log_dir: Thư mục chứa log files
        
    Returns:
        Logger instance
    """
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Xóa các handler cũ
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Colored console handler
    console_handler = ColoredConsoleHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (không màu)
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    log_filename = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_enterprise_collector.log"
    log_file_path = log_path / log_filename
    
    file_handler = logging.FileHandler(log_file_path, mode='w', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    logger.info(f"Colored logger initialized: {log_file_path}")
    return logger