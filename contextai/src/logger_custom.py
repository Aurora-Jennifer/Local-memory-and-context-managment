import logging
from pathlib import Path
from datetime import datetime

def setup_logger(name: str, log_dir="~/.contextai/logs", level=logging.INFO):
    log_dir = Path(log_dir).expanduser()
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"

    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # avoid duplicates
    if not logger.handlers:
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger