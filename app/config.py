from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    TARGET_PROJECT: str = ""
    TARGET_BRANCH: str = "master"
    CODE_DIR: str = "app"
    ACCEPTED_COMMENTS: list[str] = ["# Arrange", "# Act", "# Assert"]
    RESULT_FILE_NAME: str = "comments.txt"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
