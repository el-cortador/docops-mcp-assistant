# app/core/models.py

# Модели данных

from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class ProjectInfo(BaseModel):
    # Модель данных для предоставления информации

    slug: str
    name: Optional[str] = None
    description: Optional[str] = None

class SourceReference(BaseModel):
    # Модель данных для ссылки на источник
    
    path: str
    snippet: str


class QAResponse(BaseModel):
    # Модель данных для вывода вопроса-ответа со ссылкой на источник
    
    answer: str
    sources: List[SourceReference]


class ErrorResponse(BaseModel):
    # Модель данных для вывода ошибки ответа
    
    detail: str
    info: Optional[Dict[str, Any]] = None