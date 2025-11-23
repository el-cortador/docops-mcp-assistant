# app/core/logging.py

# Модуль настройки и управления логированием

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.config.settings import settings


# Местоположение лог-файла из настроек проекта
LOG_FILE = settings.paths.project_root / "logs" / "app.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def setup_logging(level: int = logging.INFO) -> None:
    # Настраивает логирование приложения: вывод в консоль и файл с ротацией (уровень — по умолчанию INFO)

    logger = logging.getLogger()
    logger.setLevel(level)

    # Формат логов
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Обработка консоль логов
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    # Файловый лог-хендлер с ротацией
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.info("Logging successfully initialized.")

setup_logging()