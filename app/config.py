from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    TARGET_PROJECT: str = ""
    TARGET_BRANCH: str = "master"
    CODE_DIR: str = "app"
    ACCEPTED_COMMENTS: list[str] = ["# Arrange", "# Act", "# Assert"]
    RESULT_FILE_NAME: str = "comments.txt"
    TEST_SETUP_COMMAND: str | None = None
    TEST_TEARDOWN_COMMAND: str | None = None
    COV_JSON_FILE_PATH: str = "cov.json"
    COV_HTML_DIR: str = "cov_html"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
