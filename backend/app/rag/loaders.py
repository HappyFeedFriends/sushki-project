import os
from langchain_core.documents import Document
from pypdf import PdfReader

DATA_DIR = "data/docs"


def load_documents():
    docs = []

    for filename in os.listdir(DATA_DIR):
        path = os.path.join(DATA_DIR, filename)

        if filename.endswith(".pdf"):
            reader = PdfReader(path)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            docs.append(Document(page_content=text, metadata={"source": filename}))

        elif filename.endswith(".txt"):
            with open(path, "r", encoding="utf-8") as f:
                docs.append(Document(page_content=f.read(), metadata={"source": filename}))

    return docs
