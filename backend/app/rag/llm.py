import os
from dotenv import load_dotenv
from langchain_gigachat import GigaChat

load_dotenv()


def get_llm():
    auth_key = os.getenv("GIGACHAT_API_KEY")

    if not auth_key:
        raise RuntimeError("❌ GIGACHAT_API_KEY не найден в .env")

    return GigaChat(
        model=os.getenv('GIGACHAT_MODEL', ''),
        credentials=auth_key,
        scope="GIGACHAT_API_PERS",
        verify_ssl_certs=False,
        temperature=0.2,
    )
