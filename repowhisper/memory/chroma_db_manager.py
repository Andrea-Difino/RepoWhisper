import os

os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"  # Nasconde le barre di download dei file
os.environ["HF_HUB_VERBOSITY"] = "error"          
os.environ["TRANSFORMERS_VERBOSITY"] = "error"    

from huggingface_hub.utils import logging as hf_logging
from transformers.utils import logging as transformers_logging

hf_logging.set_verbosity_error()
transformers_logging.set_verbosity_error()
transformers_logging.disable_progress_bar()

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings


class ChromaDBManager:

    def __init__(self, docs: list[Document], embedding_model_name: str = "all-MiniLM-L6-v2"):
        self.db_dir = "./db"
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name)
        self.docs = docs
        self.db = self._create_vec_db()

    def _create_vec_db(self) -> Chroma:
        vector_db = Chroma.from_documents(
            documents=self.docs,
            embedding=self.embeddings,
            persist_directory=self.db_dir
        )
        return vector_db

    def search_code(self, query: str, top_k: int = 3):
        """
            Return the most relevant code in our vector db based on the query
        """
        results = self.db.similarity_search(query=query, k=top_k)
        return results

    