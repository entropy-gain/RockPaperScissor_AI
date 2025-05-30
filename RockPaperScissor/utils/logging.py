# RockPaperScissor/utils/logging.py
import logging
import sys

# Store the logger instance to prevent re-creation/multiple handlers
_logger_instance = None

def setup_logging(log_level_str: str = "INFO") -> logging.Logger:
    global _logger_instance
    if _logger_instance is None:
        logger = logging.getLogger("RPS_Gradio_App")
        logger.propagate = False # Prevent Gunicorn/Uvicorn from duplicating root logger's messages
        
        # Remove existing handlers if any (e.g., from previous calls or other libs)
        if logger.hasHandlers():
            logger.handlers.clear()

        log_level = getattr(logging, log_level_str.upper(), logging.INFO)
        logger.setLevel(log_level)

        handler = logging.StreamHandler(sys.stdout) # Log to stdout for HF Spaces
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        _logger_instance = logger
        print(f"Logger '{logger.name}' configured with level {log_level_str} and stream handler.")
    return _logger_instance