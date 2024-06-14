import os
import sys

from app.config import settings
from app.logger import logger
from app.review import (
    check_code_coverage,
    check_code_with_mypy,
    check_code_with_pylint,
    check_commented_code,
    check_print_debug,
    check_vulnerability,
    get_files_to_check,
)

if __name__ == "__main__":
    current_dir = os.getcwd()
    if settings.TARGET_PROJECT:
        os.chdir(settings.TARGET_PROJECT)
    code_files, test_files = get_files_to_check()
    all_files = {**code_files, **test_files}
    if not all_files:
        logger.info("There is no python file to check!!!")
        sys.exit(0)
    try:
        check_print_debug(all_files)
        check_commented_code(all_files)
        check_code_with_pylint(code_files, test_files)
        check_code_with_mypy(all_files)
        check_code_coverage(all_files)
        check_vulnerability()
    finally:
        os.chdir(current_dir)
