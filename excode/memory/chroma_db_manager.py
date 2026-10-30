from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings


class ChromaDBManager:

    def __init__(self, docs: list[Document], embedding_model_name: str = "all-MiniLM-L6-v2"):
        self.db_dir = "./excode_db"
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

    