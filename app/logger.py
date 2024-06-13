import logging
import os

from app.config import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

terminal_handler = logging.StreamHandler()
file_handler = logging.FileHandler(
    os.path.join(settings.TARGET_PROJECT, settings.RESULT_FILE_NAME), mode="w"
)

logger.addHandler(terminal_handler)
logger.addHandler(file_handler)
