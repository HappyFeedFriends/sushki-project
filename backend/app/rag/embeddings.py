from typing import List
from langchain_core.embeddings import Embeddings
from sklearn.feature_extraction.text import TfidfVectorizer


class TfidfEmbeddings(Embeddings):
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words=None,
            max_features=2048
        )
        self.fitted = False

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        vectors = self.vectorizer.fit_transform(texts)
        self.fitted = True
        return vectors.toarray().tolist()

    def embed_query(self, text: str) -> List[float]:
        if not self.fitted:
            raise RuntimeError("❌ Сначала создайте векторстор (индексация документов)")
        return self.vectorizer.transform([text]).toarray()[0].tolist()


def get_embeddings():
    return TfidfEmbeddings()
