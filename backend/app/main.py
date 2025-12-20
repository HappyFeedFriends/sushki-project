# backend/app/main.py
"""
FastAPI приложение с поддержкой выбора стиля общения.
Простой патч: добавляем проектный корень в sys.path, чтобы абсолютные импорты
типа 'backend.app.services.style_service' работали даже при запуске скрипта.
"""

import os
import sys
import inspect
import asyncio
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# --- Небольшой патч для корректной работы абсолютных импортов ---
# Это позволит запускать main.py как скрипт (python backend/app/main.py)
# и одновременно работать в среде, где модуль запускается как пакет (uvicorn backend.app.main:app).
CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))      # .../backend/app
BACKEND_DIR = os.path.dirname(CURRENT_DIR)                    # .../backend
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)                   # корень проекта
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# --- Импорты сервисов (абсолютные, как у вас в проекте) ---
# Если у вас другой путь — поправьте его.
try:
    from backend.app.services.style_service import style_service
except Exception:
    # Падение импорта — выдадим понятное сообщение при старте
    style_service = None

# Попытка импортировать реальную функцию отправки в GigaChat
try:
    from backend.app.services.gigachat_service import sendMessageFromBackend  # type: ignore
except Exception:
    # Заглушка: если реальная интеграция отсутствует, возвращаем эхо
    async def sendMessageFromBackend(text: str) -> str:
        return f"[GigaChat stub] Echo: {text}"


app = FastAPI(title="СБЕР AI — Backend GigaChat")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # при необходимости ограничьте
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Статические файлы (проверьте путь) ---
try:
    app.mount("/", StaticFiles(directory="../../frontend", html=True), name="static")
except Exception:
    # Игнорируем, если нет статических файлов по указанному пути
    pass


# --- Модели ---
class ChatMessage(BaseModel):
    text: str = Field(..., description="Запрос пользователя")
    style: str = Field("business", description="Стиль ответа: business | youth | direct | simple")


# --- Утилита для вызова sendMessageFromBackend (sync/async поддержка) ---
async def _call_send_message(func, text: str) -> str:
    if inspect.iscoroutinefunction(func):
        return await func(text)
    result = func(text)
    if asyncio.iscoroutine(result):
        return await result
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, func, text)


# --- Эндпоинты ---
@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "healthy"}


@app.get("/api/styles")
def get_styles() -> Dict[str, List[Dict[str, Any]]]:
    styles = [
        {"id": "business", "name": "Деловой", "description": "Строгий, структурированный, без сленга и эмодзи", "icon": "👔"},
        {"id": "youth", "name": "Молодёжный", "description": "Сленг, эмодзи, как общение с другом", "icon": "😎"},
        {"id": "direct", "name": "Прямолинейный", "description": "Кратко, по существу, без лишних слов", "icon": "🎯"},
        {"id": "simple", "name": "Простой", "description": "Короткие предложения, простые слова, добрый тон", "icon": "🤗"},
    ]
    return {"styles": styles}


@app.post("/api/chat")
async def chat_endpoint(message: ChatMessage):
    allowed = {"business", "youth", "direct", "simple"}
    style = message.style if isinstance(message.style, str) else "business"
    if style not in allowed:
        raise HTTPException(status_code=400, detail=f"Unknown style '{style}'")

    if style_service is None:
        raise HTTPException(status_code=500, detail="StyleService not available (import failed)")

    try:
        raw_answer = await _call_send_message(sendMessageFromBackend, message.text)
        styled_answer = style_service.apply_style(raw_answer, style)
        return {
            "answer": styled_answer,
            "raw": raw_answer,
            "status": "success",
            "style": style
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# Для удобного запуска через `python backend/app/main.py`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
