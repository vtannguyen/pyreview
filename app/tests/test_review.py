import os
import re
import subprocess
from unittest.mock import MagicMock

import pytest

from app.review import (
    check_code_coverage,
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
            "src/items.py": list(range(1, len(UPDATED_CODE_CONTENT.splitlines()))),
            "src/schema.py": list(range(1, 6)),
        },
        "test_files": {
            "src/tests/test_items.py": list(
                range(1, len(UPDATED_TEST_CONTENT.splitlines()))
            ),
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
    mocker.patch("app.review.settings.TARGET_BRANCH", "master")
    mocker.patch("app.review.settings.CODE_DIR", "src")
    # Act
    result = get_files_to_check()
    # Assert
    assert result == (
        {
            "src/items.py": [2, *range(7, 12), *range(16, 26), 27, *range(32, 37)],
            "src/schema.py": list(range(1, 7)),
        },
        {"src/tests/test_items.py": [2, 4, 11, *range(14, 29), 39]},
    )


def test_check_commented_code(mock_code_directory, mocker, caplog):
    # Arrange
    mocker.patch("app.review.settings.ACCEPTED_COMMENTS", ["# Accepted comment"])
    mocker.patch("app.review.settings.TARGET_BRANCH", "master")
    mocker.patch("app.review.settings.CODE_DIR", "src")
    expected_log = """CHECK FOR COMMENTED CODE...
------------  -----------
File          Line number
src/items.py  [7, 8]
------------  -----------"""
    code_files, _ = get_files_to_check()
    # Act
    check_commented_code(code_files)
    # Assert
    assert expected_log == "\n".join(caplog.messages)


def test_check_print_debug(mock_code_directory, mocker, caplog):
    # Arrange
    mocker.patch("app.review.settings.TARGET_BRANCH", "master")
    mocker.patch("app.review.settings.CODE_DIR", "src")
    expected_log = """CHECK FOR PRINT DEBUG...
------------  -----------
File          Line number
src/items.py  [27]
------------  -----------"""
    code_files, _ = get_files_to_check()
    # Act
    check_print_debug(code_files)
    # Assert
    assert expected_log == "\n".join(caplog.messages)


def test_check_code_with_pylint(mock_code_directory, mocker, caplog):
    # Arrange
    mocker.patch("app.review.settings.TARGET_BRANCH", "master")
    mocker.patch("app.review.settings.CODE_DIR", "src")

    def mock_run(*args, **kwargs):
        res = MagicMock()
        if "test" in args[0]:
            res.stdout = """************* Module src.tests.test_items
src/tests/test_items.py:1:0: C0114: Missing module docstring (missing-module-docstring)
src/tests/test_items.py:7:0: C0116: Missing function or method docstring (missing-function-docstring)
src/tests/test_items.py:18:0: C0116: Missing function or method docstring (missing-function-docstring)
src/tests/test_items.py:31:0: C0116: Missing function or method docstring (missing-function-docstring)"""
        else:
            res.stdout = """************* Module src.items
src/items.py:1:0: C0114: Missing module docstring (missing-module-docstring)
src/items.py:5:0: C0116: Missing function or method docstring (missing-function-docstring)
src/items.py:16:0: C0116: Missing function or method docstring (missing-function-docstring)
src/items.py:26:0: C0116: Missing function or method docstring (missing-function-docstring)
************* Module src.schema
src/schema.py:1:0: C0114: Missing module docstring (missing-module-docstring)
src/schema.py:4:0: C0115: Missing class docstring (missing-class-docstring)"""
        return res

    expected_log = """CHECKING CODE USING Pylint...
************* Module src.items
src/items.py:16:0: C0116: Missing function or method docstring (missing-function-docstring)
************* Module src.schema
src/schema.py:1:0: C0114: Missing module docstring (missing-module-docstring)
src/schema.py:4:0: C0115: Missing class docstring (missing-class-docstring)
************* Module src.tests.test_items
src/tests/test_items.py:18:0: C0116: Missing function or method docstring (missing-function-docstring)"""

    mocker.patch("app.review.subprocess.run", side_effect=mock_run)
    code_files, test_files = get_files_to_check()
    # Act
    check_code_with_pylint(code_files=code_files, test_files=test_files)
    # Assert
    assert expected_log == "\n".join(caplog.messages)


def test_check_code_coverage(mock_code_directory, mocker, caplog):
    # Arrange
    mocker.patch("app.review.settings.TARGET_BRANCH", "master")
    mocker.patch("app.review.settings.CODE_DIR", "src")
    code_files, _ = get_files_to_check()
    # Act
    check_code_coverage(code_files)
    # Assert
    assert re.search(r"file:///[0-9a-zA-Z/_-]*items_py.html\s*\{36\}", caplog.text)
    assert re.search(
        r"file:///[0-9a-zA-Z/_-]*schema_py.html\s*\{1, 4, 5, 6\}", caplog.text
    )
