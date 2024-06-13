CURRENT_BRANCH = "feature/feature-1"

CODE_CONTENT = """import json


def get_items() -> list[dict]:
    with open("items.json", "r", encoding="utf-8") as f:
        return json.load(f)


def create_item(name: str, description: str) -> None:
    items = get_items()
    items.append({"name": name, "description": description})
    with open("items.json", "w", encoding="utf-8") as f:
        json.dump(f, items)
"""

TEST_CONTENT = """import json

from src.items import create_item, get_items


def test_get_items():
    # Arrange
    data = [{"name": "test_name", "description": "test_description"}]
    with open("items.json", "w", encoding="utf-8") as f:
        json.dump(f, data)
    # Act
    res = get_items()
    # Assert
    assert res == data


def test_create_item():
    # Arrange
    item = {"name": "test_name", "description": "test_description"}
    # Act
    create_item(**item)
    # Assert
    with open("items.json", "r", encoding="utf-8") as f:
        assert [item] == json.load(f)
"""

CONFIG_CONTENT = """from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    TARGET_REPO: str = ""

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
"""

SCHEMA_CONTENT = """from pydantic import BaseModel


class Item(BaseModel):
    name: str
    description: str
"""

UPDATED_CODE_CONTENT = """import json


def get_items() -> list[dict]:
    print("GETTING ITEMS...")
    with open("items.json", "r", encoding="utf-8") as f:
        return json.load(f)


def update_item(name: str, description: str) -> None:
    items = get_items()
    for item in items:
        if item["name"] == name:
            item["description"] = description
            break
    with open("items.json", "w", encoding="utf-8") as f:
        json.dump(f, items)


def create_item(name: str, description: str) -> None:
    print("CREATING ITEM...")
    items = get_items()
    items.append({"name": name, "description": description})
    with open("items.json", "w", encoding="utf-8") as f:
        json.dump(f, items)
"""

UPDATED_TEST_CONTENT = """import json

from src.items import create_item, get_items, update_item


def test_get_items():
    # Arrange
    data = [{"name": "test_name", "description": "test_description"}]
    with open("items.json", "w", encoding="utf-8") as f:
        json.dump(f, data)
    # Act
    # Assert
    assert data == get_items()


def test_update_item():
    # Arrange
    item = {"name": "test_name", "description": "test_description"}
    updated_item = {"name": "test_name", "description": "updated_description"}
    create_item(**item)
    # Act
    update_item(**updated_item)
    # Assert
    with open("items.json", "r", encoding="utf-8") as f:
        assert [updated_item] == json.load(f)


def test_create_item():
    # Arrange
    item = {"name": "test_name", "description": "test_description"}
    # Act
    create_item(**item)
    # Assert
    with open("items.json", "r", encoding="utf-8") as f:
        assert [item] == json.load(f)
"""
