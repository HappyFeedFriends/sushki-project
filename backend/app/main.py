"""
backend/app/main.py

FastAPI приложение с поддержкой выбора стиля общения.
Эндпоинты:
    GET  /health
    GET  /api/styles
    POST /api/chat    -> body: {"text": "...", "style": "business"}
"""

from typing import Any, Dict, List
import inspect
import asyncio

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Импорт сервиса стилей
from backend.app.services.style_service import style_service

# Попытка импортировать функцию отправки в GigaChat.
# Подставьте реальный модуль/функцию, если она в вашем проекте называется иначе.
try:
    # Ожидается функция sendMessageFromBackend(text: str) -> str | coroutine
    from backend.app.services.gigachat_service import sendMessageFromBackend  # type: ignore
except Exception:
    # Fallback заглушка, если реальная интеграция отсутствует — возвращает эхо
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

# --- Статические файлы фронтенда (проверьте путь в своем проекте) ---
# Путь здесь относительный от backend/app, корректируйте при необходимости
try:
    app.mount("/", StaticFiles(directory="../../frontend", html=True), name="static")
except Exception:
    # Если статических файлов нет — игнорируем монтирование
    pass


# --- Модели ---
class ChatMessage(BaseModel):
    text: str = Field(..., description="Запрос пользователя")
    style: str = Field("business", description="Стиль ответа: business | youth | direct | simple")


# --- Утилита для вызова sendMessageFromBackend, поддерживает sync/async funcs ---
async def _call_send_message(func, text: str) -> str:
    if inspect.iscoroutinefunction(func):
        return await func(text)
    # если функция возвращает coroutine при вызове (но не определена как coroutinefunction)
    result = func(text)
    if asyncio.iscoroutine(result):
        return await result
    # блокируемый sync вызов — выполним в пуле
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, func, text)


# --- Эндпоинты ---
@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "healthy"}


@app.get("/api/styles")
def get_styles() -> Dict[str, List[Dict[str, Any]]]:
    """Вернуть список доступных стилей для фронтенда"""
    styles = [
        {"id": "business", "name": "Деловой", "description": "Строгий, структурированный, без сленга и эмодзи", "icon": "👔"},
        {"id": "youth", "name": "Молодёжный", "description": "Сленг, эмодзи, как общение с другом", "icon": "😎"},
        {"id": "direct", "name": "Прямолинейный", "description": "Кратко, по существу, без лишних слов", "icon": "🎯"},
        {"id": "simple", "name": "Простой", "description": "Короткие предложения, простые слова, добрый тон", "icon": "🤗"},
    ]
    return {"styles": styles}


@app.post("/api/chat")
async def chat_endpoint(message: ChatMessage):
    """
    Принять user prompt -> отправить в GigaChat -> получить raw -> применить стиль -> вернуть
    """
    allowed = {"business", "youth", "direct", "simple"}
    style = message.style if isinstance(message.style, str) else "business"
    if style not in allowed:
        raise HTTPException(status_code=400, detail=f"Unknown style '{style}'")

    try:
        # 1) Посылаем в GigaChat (sync/async поддерживается)
        raw_answer = await _call_send_message(sendMessageFromBackend, message.text)

        # 2) Применяем стиль
        styled_answer = style_service.apply_style(raw_answer, style)

        return {
            "answer": styled_answer,
            "raw": raw_answer,
            "status": "success",
            "style": style
        }
    except Exception as exc:
        # Возвращаем читаемую ошибку для фронтенда (и логируйте в реальном проекте)
        raise HTTPException(status_code=500, detail=str(exc))
