# app/config/settings.py

# Модуль настроек приложения на Pydantic: хранит и валидирует параметры конфигурации

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class PathsConfig(BaseModel):
    # Пути файловой системы: корень проекта, демо-данные, демо-репа, БД и векторное хранилище

    # Корневой путь проекта (по умолчанию на 2 уровня выше app/)
    project_root: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2]
    )

    # Путь до демо-данных/
    demo_data_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2] / "demo_data"
    )

    # Путь до демо-репы: demo_data/demo_repos/
    demo_repos_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2]
        / "demo_data"
        / "demo_repos"
    )

    # Путь до демо-БД
    demo_db_path: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2]
        / "demo_data"
        / "demo.db"
    )

    # Путь до векторного хранилища
    vector_store_path: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2]
        / "demo_data"
        / "vector_store"
        / "documents.jsonl"
    )


class LLMConfig(BaseModel):
    # Выбор модели и загрузка настроек из окружения

    model: str = Field(default="gpt-4o-mini")

    @field_validator("model", mode="before")
    @classmethod
    def load_model_from_env(cls, v: str) -> str:
        # Загружает название модели из переменной окружения DOCOPS_MODEL

        env_val = os.getenv("DOCOPS_MODEL")
        return env_val or v


class ConfluenceConfig(BaseModel):
    # Интеграция с Confluence

    base_url: Optional[str] = None
    email: Optional[str] = None
    api_token: Optional[str] = None

    @field_validator("base_url", mode="before")
    @classmethod
    def load_base_url(cls, v: Optional[str]) -> Optional[str]:
        # Загружает базовый URL Confluence из переменной окружения CONFLUENCE_BASE_URL

        return v or os.getenv("CONFLUENCE_BASE_URL")

    @field_validator("email", mode="before")
    @classmethod
    def load_email(cls, v: Optional[str]) -> Optional[str]:
        # Загружкает email из переменной окружения CONFLUENCE_EMAIL
        
        return v or os.getenv("CONFLUENCE_EMAIL")

    @field_validator("api_token", mode="before")
    @classmethod
    def load_token(cls, v: Optional[str]) -> Optional[str]:
        # Загружает API-токен Confluence из переменной окружения CONFLUENCE_API_TOKEN
        
        return v or os.getenv("CONFLUENCE_API_TOKEN")


class GitHubConfig(BaseModel):
    # Класс для настройки интеграции с GitHub
    
    token: Optional[str] = None
    api_base_url: str = Field(default="https://api.github.com")

    @field_validator("token", mode="before")
    @classmethod
    def load_gh_token(cls, v: Optional[str]) -> Optional[str]:
        # Загружает GitHub-токен из переменной окружения GITHUB_TOKEN
        
        return v or os.getenv("GITHUB_TOKEN")

    @field_validator("api_base_url", mode="before")
    @classmethod
    def load_gh_base(cls, v: str) -> str:
        # Загружает базовый URL GitHub API из переменной окружения GITHUB_API_BASE_URL
        
        return os.getenv("GITHUB_API_BASE_URL", v)


class MCPConfig(BaseModel):
    # Класс для настройки MCP-серверов
    
    git_server_entry: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2]
        / "mcp-servers"
        / "git-mcp-server"
        / "mcp_git"
        / "server.py"
    )
    confluence_server_entry: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2]
        / "mcp-servers"
        / "confluence-mcp-server"
        / "mcp_confluence"
        / "server.py"
    )
    vector_server_entry: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2]
        / "mcp-servers"
        / "vector-mcp-server"
        / "mcp_vector"
        / "server.py"
    )


class Settings(BaseModel):
    # Основной класс, объединяющий все конфигурационные блоки

    paths: PathsConfig = Field(default_factory=PathsConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    confluence: ConfluenceConfig = Field(default_factory=ConfluenceConfig)
    github: GitHubConfig = Field(default_factory=GitHubConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)

    environment: str = Field(default_factory=lambda: os.getenv("DOCOPS_ENV", "development"))

    @field_validator("environment", mode="before")
    @classmethod
    def load_env(cls, v: str) -> str:
        # Загружает переменную DOCOPS_ENV из окружения
        
        return os.getenv("DOCOPS_ENV", v)

settings = Settings()