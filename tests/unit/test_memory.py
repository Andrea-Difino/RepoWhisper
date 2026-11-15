from typing import cast
from unittest.mock import Mock

from langchain_core.documents import Document

from repowhisper.memory.chroma_db_manager import ChromaDBManager


def test_chroma_db_manager_creates_and_searches_vector_store(monkeypatch):
    embedding_model = Mock()
    vector_store = Mock()
    vector_store.similarity_search.return_value = ["match"]
    monkeypatch.setattr(
        "repowhisper.memory.chroma_db_manager.HuggingFaceEmbeddings",
        Mock(return_value=embedding_model),
    )
    monkeypatch.setattr(
        "repowhisper.memory.chroma_db_manager.Chroma.from_documents",
        Mock(return_value=vector_store),
    )

    manager = ChromaDBManager(
        cast(list[Document], ["document"]), embedding_model_name="test-model"
    )

    assert manager.embeddings is embedding_model
    assert manager.search_code("query", top_k=2) == ["match"]
    vector_store.similarity_search.assert_called_once_with(query="query", k=2)
