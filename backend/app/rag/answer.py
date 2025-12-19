from rag.vectorstore import load_vectorstore
from rag.rag_chain import run_rag
from rag.llm import get_llm

#
# Загружаем вектора и на основе базы векторов спрашиваем у LLM ответ на вопрос.
#
def answer(answer: str):
    vectorstore = load_vectorstore()
    llm = get_llm()
    return run_rag(llm, vectorstore, answer)
