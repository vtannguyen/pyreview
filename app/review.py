import json
import os
import re
import subprocess
from io import StringIO
from shutil import which

from pylint import lint
from pylint.reporters.text import TextReporter
from tabulate import tabulate

from app.config import settings
from app.logger import logger

Filename = str
ChangedLineNo = int
TargetFiles = dict[Filename, list[ChangedLineNo]]
TargetCodeFiles = TargetFiles
TargetTestFiles = TargetFiles


def tool_is_available(tool_name: str) -> bool:
    return which(tool_name) is not None


def get_current_branch() -> str | None:
    res = subprocess.run(
        "git branch --show-current",
        shell=True,
        check=True,
        capture_output=True,
        text=True,
    )
    return res.stdout.strip()


def get_all_python_files() -> tuple[TargetCodeFiles, TargetTestFiles]:
    code_files: dict[Filename, list] = {}
    test_files: dict[Filename, list] = {}
    for root, _, files in os.walk(".", topdown=True):
        if not root.startswith("./."):
            for name in files:
                if name.endswith(".py"):
                    file_path = os.path.join(root, name).removeprefix("./")
                    with open(file_path, "r", encoding="utf-8") as f:
                        line_no = len(f.readlines())
                    if "test" in file_path:
                        test_files[file_path] = list(range(1, line_no))
                    else:
                        code_files[file_path] = list(range(1, line_no))
    return {k: v for k, v in code_files.items() if v}, {
        k: v for k, v in test_files.items() if v
    }


def get_changed_python_files() -> tuple[TargetCodeFiles, TargetTestFiles]:
    diff_file_name = "/tmp/diff_code.txt"
    subprocess.run(
        f"git diff {settings.TARGET_BRANCH} -U0 > {diff_file_name}",
        shell=True,
        check=True,
    )

    with open(diff_file_name, "r", encoding="utf-8") as f:
        all_lines = f.readlines()
    code_files: dict[Filename, list] = {}
    test_files: dict[Filename, list] = {}
    current_file: str | None = None
    for line in all_lines:
        if re.match(r"^diff --git\s.*\s.*py\n$", line):
            current_file = line.split(" ")[2][2:]
        elif re.match(r"^diff --git\s.*\s.*\n$", line):
            current_file = None
        elif re.match(r"@@\s[0-9\+\-,\s]*\s@@", line) and current_file is not None:
            new_lines_no = line.split("@@")[1].split(" ")[-2][1:]
            if "," not in new_lines_no:
                new_lines = [int(new_lines_no)]
            else:
                start, length = new_lines_no.split(",")
                new_lines = list(range(int(start), int(start) + int(length)))
            if not settings.CODE_DIR or current_file.startswith(settings.CODE_DIR):
                if "test" in current_file:
                    test_files.setdefault(current_file, []).extend(new_lines)
                else:
                    code_files.setdefault(current_file, []).extend(new_lines)
    return {k: v for k, v in code_files.items() if v}, {
        k: v for k, v in test_files.items() if v
    }


def get_files_with_debug_code(files: TargetFiles) -> TargetFiles:
    files_with_debug_code: TargetFiles = {}
    for file_path in files:
        with open(file_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f.readlines()):
                line_no = i + 1
                if re.search(r"\s*print(.*)", line) and line_no in files[file_path]:
                    files_with_debug_code.setdefault(file_path, []).append(line_no)
    return files_with_debug_code


def get_files_with_commented_code(files: TargetFiles) -> TargetFiles:
    files_with_commented_code: TargetFiles = {}
    for file_path in files:
        with open(file_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f.readlines()):
                line_no = i + 1
                if (
                    re.search(r".*#.*", line)
                    and not any(
                        re.search(f"{comment}$", line)
                        for comment in settings.ACCEPTED_COMMENTS
                    )
                    and line_no in files[file_path]
                ):
                    files_with_commented_code.setdefault(file_path, []).append(line_no)
    return files_with_commented_code


def get_files_to_check() -> tuple[TargetCodeFiles, TargetTestFiles]:
    current_branch = get_current_branch()
    if current_branch != settings.TARGET_BRANCH:
        return get_changed_python_files()
    return get_all_python_files()


def check_code_with_pylint(code_files: TargetFiles, test_files: TargetFiles) -> None:
    logger.info("CHECKING CODE USING Pylint...")
    all_files = {**code_files, **test_files}
    lint_output = StringIO()
    reporter = TextReporter(lint_output)
    if code_files:
        pylint_code_opts = [
            f"--disable={','.join(settings.PYLINT_DISABLE_OPTIONS_CODE_FILES)}",
            *code_files.keys(),
        ]
        lint.Run(pylint_code_opts, reporter=reporter, exit=False)
    if test_files:
        pylint_test_opts = [
            f"--disable={','.join(settings.PYLINT_DISABLE_OPTIONS_TEST_FILES)}",
            *test_files.keys(),
        ]
        lint.Run(pylint_test_opts, reporter=reporter, exit=False)
    related_lines = []
    for line in lint_output.getvalue().split("\n"):
        if line.startswith("****"):
            related_lines.append(line)
        else:
            for file, line_nos in all_files.items():
                if line.startswith(file):
                    line_no = line.split(":")[1]
                    if int(line_no) in line_nos:
                        related_lines.append(line)

    logger.info("\n".join(related_lines))


def check_print_debug(files: TargetFiles) -> None:
    logger.info("CHECK FOR PRINT DEBUG...")
    files_with_debug_code = get_files_with_debug_code(files)
    logger.info(tabulate((("File", "Line number"), *files_with_debug_code.items())))


def check_commented_code(files: TargetFiles) -> None:
    logger.info("CHECK FOR COMMENTED CODE...")
    files_with_commented_code = get_files_with_commented_code(files)
    logger.info(tabulate((("File", "Line number"), *files_with_commented_code.items())))


def check_code_with_mypy(files: TargetFiles) -> None:
    logger.info("CHECKING CODE USING mypy...")
    subprocess.run("mypy --install-types --non-interactive", shell=True)
    CMD = "mypy --follow-imports=skip --ignore-missing-imports " + " ".join(
        files.keys()
    )
    res = subprocess.run(CMD, shell=True, capture_output=True, text=True)
    logger.info(res.stdout)


def check_code_coverage(files: TargetFiles) -> None:
    logger.info("CHECKING CODE COVERAGE...")
    if settings.TEST_SETUP_COMMAND:
        subprocess.run(settings.TEST_SETUP_COMMAND, shell=True, check=True)
    try:
        subprocess.run(
            f"pytest --cov-report json:{settings.COV_JSON_FILE_PATH} --cov-report html:{settings.COV_HTML_DIR} --cov={settings.CODE_DIR} .",
            shell=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return
    with open(settings.COV_JSON_FILE_PATH, "r", encoding="utf-8") as f:
        cov_report = json.load(f)
        files_not_covered = []
        for file, data in cov_report["files"].items():
            if file in files:
                not_covered_lines = set(files[file]).intersection(
                    set(data["missing_lines"])
                )
                if data["missing_lines"] != 0 and not_covered_lines:
                    files_not_covered.append((file, not_covered_lines))
    files_not_covered_links = []
    for file in os.listdir(settings.COV_HTML_DIR):
        for related_file, not_covered_lines in files_not_covered:
            with open(f"{settings.COV_HTML_DIR}/{file}", "r", encoding="utf-8") as f:
                if (
                    file.endswith(
                        f"{related_file.split('/')[-1].replace('.', '_')}.html"
                    )
                    and related_file in f.read()
                ):
                    files_not_covered_links.append(
                        (
                            f"file://{os.getcwd()}/{settings.COV_HTML_DIR}/{file}",
                            not_covered_lines,
                        )
                    )
    logger.info("The following files is not fully covered by tests:")
    logger.info(tabulate((("File link", "Line number"), *files_not_covered_links)))
    if settings.TEST_TEARDOWN_COMMAND:
        subprocess.run(settings.TEST_TEARDOWN_COMMAND, shell=True, check=True)


def check_vulnerability():
    logger.info("CHECKING VULNERABILITY...")
    if not tool_is_available("trivy"):
        logger.info("Trivy is not available. Skipping vulnerability check.")
        return
    res = subprocess.run(
        "trivy fs --scanners vuln,secret,config,license .",
        shell=True,
        check=True,
        capture_output=True,
        text=True,
    )
    logger.info(res.stdout)
