import os
import subprocess
from unittest.mock import MagicMock

import pytest
from pylint.reporters.text import TextReporter

from app.review import (
    check_code_with_pylint,
    check_commented_code,
    check_print_debug,
    get_files_to_check,
)
from app.tests.const import (
    CODE_CONTENT,
    CONFIG_CONTENT,
    CURRENT_BRANCH,
    SCHEMA_CONTENT,
    TEST_CONTENT,
    UPDATED_CODE_CONTENT,
    UPDATED_TEST_CONTENT,
)


@pytest.fixture
def mock_terminal_commands(mocker):

    def mock_bash(command, *args, **kwargs):
        mock_result = MagicMock()
        if command == "git branch":
            mock_result.stdout = f"  main\n* {CURRENT_BRANCH}\n  feature/feature-2"
        elif command.startswith("git diff"):
            with open("/tmp/diff_code.txt", "w", encoding="utf-8") as f:
                f.write(GIT_DIFF_RESULT)
        return mock_result

    mocker.patch("subprocess.run", side_effect=mock_bash)
    yield


@pytest.fixture
def mock_code_directory(tmp_path):
    directories = ["src", "src/tests"]
    for directory in directories:
        (tmp_path / directory).mkdir()

    files = {
        "src/items.py": CODE_CONTENT,
        "src/tests/test_items.py": TEST_CONTENT,
        "src/__init__.py": "",
        "src/tests/__init__.py": "",
        "src/config.py": CONFIG_CONTENT,
        "README.md": "dummy content",
        ".gitignore": "dummy",
    }
    for file_path, content in files.items():
        (tmp_path / file_path).write_text(content)

    current_dir = os.getcwd()
    os.chdir(tmp_path)
    subprocess.run("git init", shell=True, check=True)
    subprocess.run("git add .", shell=True, check=True)
    subprocess.run('git commit -m "initial commit"', shell=True, check=True)
    subprocess.run(f"git branch {CURRENT_BRANCH}", shell=True, check=True)
    subprocess.run(f"git checkout {CURRENT_BRANCH}", shell=True, check=True)
    updated_files = {
        "src/items.py": UPDATED_CODE_CONTENT,
        "src/tests/test_items.py": UPDATED_TEST_CONTENT,
        "src/__init__.py": "",
        "src/tests/__init__.py": "",
        "src/schema.py": SCHEMA_CONTENT,
        "README.md": "updated content",
    }
    for file_path in files:
        if file_path not in updated_files:
            os.remove(tmp_path / file_path)
    for file_path, content in updated_files.items():
        (tmp_path / file_path).write_text(content)
    subprocess.run("git add .", check=True, shell=True)
    subprocess.run('git commit -m "make some changes"', shell=True, check=True)
    yield {
        "code_files": {
            "src/items.py": list(range(1, 29)),
            "src/schema.py": list(range(1, 6)),
        },
        "test_files": {
            "src/tests/test_items.py": list(range(1, 35)),
        },
    }
    os.chdir(current_dir)


def test_get_files_to_check__check_all(mock_code_directory, mocker):
    # Arrange
    mocker.patch("app.review.settings.TARGET_BRANCH", CURRENT_BRANCH)
    # Act
    result = get_files_to_check()
    # Assert
    assert result == (
        mock_code_directory["code_files"],
        mock_code_directory["test_files"],
    )


def test_get_files_to_check__only_diff_files(mock_code_directory, mocker):
    # Arrange
    mocker.patch("app.review.settings.CODE_DIR", "src")
    # Act
    result = get_files_to_check()
    # Assert
    assert result == (
        {
            "src/items.py": [*range(6, 9), *range(13, 23), 24],
            "src/schema.py": list(range(1, 7)),
        },
        {"src/tests/test_items.py": [3, *range(13, 26)]},
    )


def test_check_commented_code(mock_code_directory, mocker, caplog):
    # Arrange
    mocker.patch("app.review.settings.ACCEPTED_COMMENTS", ["# Accepted comment"])
    mocker.patch("app.review.settings.CODE_DIR", "src")
    expected_log = """CHECK FOR COMMENTED CODE...
------------  -----------
File          Line number
src/items.py  [6, 7]
------------  -----------"""
    code_files, _ = get_files_to_check()
    # Act
    res = check_commented_code(code_files)
    # Assert
    assert expected_log == "\n".join(caplog.messages)


def test_check_print_debug(mock_code_directory, mocker, caplog):
    # Arrange
    mocker.patch("app.review.settings.CODE_DIR", "src")
    expected_log = """CHECK FOR PRINT DEBUG...
------------  -----------
File          Line number
src/items.py  [24]
------------  -----------"""
    code_files, _ = get_files_to_check()
    # Act
    check_print_debug(code_files)
    # Assert
    assert expected_log == "\n".join(caplog.messages)
    # Assert
