from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    TARGET_PROJECT: str | None = None
    TARGET_BRANCH: str = "master"
    CODE_DIR: str | None = None
    ACCEPTED_COMMENTS: list[str] = ["# Arrange", "# Act", "# Assert"]
    RESULT_FILE_NAME: str = "comments.txt"
    TEST_SETUP_COMMAND: str | None = None
    TEST_TEARDOWN_COMMAND: str | None = None
    COV_JSON_FILE_PATH: str = "cov.json"
    COV_HTML_DIR: str = "cov_html"
    PYLINT_DISABLE_OPTIONS_CODE_FILES: list[str] = [
        "line-too-long",
        "missing-function-docstring",
        "missing-module-docstring",
        "invalid-name",
        "missing-class-docstring",
        "import-error",
        "too-few-public-methods",
    ]
    PYLINT_DISABLE_OPTIONS_TEST_FILES: list[str] = [
        "line-too-long",
        "missing-function-docstring",
        "missing-module-docstring",
        "invalid-name",
        "missing-class-docstring",
        "import-error",
        "redefined-outer-name",
        "too-many-arguments",
        "unused-argument",
        "protected-access",
        "duplicate-code",
    ]
    PYLINT_EXECUTABLE_PATH: str = "pylint"
    PYTEST_EXECUTABLE_PATH: str = "pytest"
    MYPY_EXECUTABLE_PATH: str = "mypy"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
