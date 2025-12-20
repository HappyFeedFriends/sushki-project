from rag.answer import answer
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="СБЕР AI — Backend GigaChat")

#
# Политика CORS для нашего бекенда.
#
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем обращаться к нам с любых хостов (плохой вариант, но в нашем случае самый удобный.)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#
# Хелс чекер для проверки работоспособности нашего сервера (для инфраструктуры render).
#
@app.get("/health")
def health():
    return {"status": "healthy"}

#
# Тело запроса к АПИ.
#
class ChatMessage(BaseModel):
    text: str

#
# Эндпоинт запроса ответа на вопрос в чате.
#
@app.post("/api/chat")
async def chat_endpoint(message: ChatMessage):
    try:
        return {"answer": answer(message.text), "status": "success"}
    except Exception as e:
        return {"answer": f"Ошибка: {str(e)}", "status": "error"}


#
# Статика нашего сервера.
#
app.mount("/", StaticFiles(directory="../../frontend", html=True), name="static")
