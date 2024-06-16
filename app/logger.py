import logging
import os

from app.config import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

terminal_handler = logging.StreamHandler()
log_file_path = (
    os.path.join(settings.TARGET_PROJECT, settings.RESULT_FILE_NAME)
    if settings.TARGET_PROJECT
    else settings.RESULT_FILE_NAME
)
file_handler = logging.FileHandler(log_file_path, mode="w")

logger.addHandler(terminal_handler)
logger.addHandler(file_handler)
