from langchain_community.vectorstores import FAISS
from rag.loaders import load_documents
from rag.embeddings import get_embeddings


def load_vectorstore():

    embeddings = get_embeddings()
    docs = load_documents()

    texts = [d.page_content for d in docs]
    metadatas = [d.metadata for d in docs]

    vectors = embeddings.embed_documents(texts)

    vectorstore = FAISS.from_embeddings(
        text_embeddings=list(zip(texts, vectors)),
        embedding=embeddings,
        metadatas=metadatas
    )

    return vectorstore
