import os
import tempfile

from git import Repo
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from langchain_core.documents import Document
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter

SUFFEXES = {
    "python" : ".py",
    "javascript": ".js",
    "typescript": ".ts"
}

class Ingestor:
    """
        Responsible for parsing and splitting source code into structured, semantically meaningful documents.
    """

    def __init__(self, source_path: str):
        self.source_path = source_path

    def ingest(self, languages: list[str] | None = None) -> list[Document]:
        """
        Analyzes syntax and divides the code into logical blocks.
        
        Args:
            languages (list[str] | None): A list of programming languages to parse.
                                          Defaults to ["python"].
                                          
        Returns:
            list[Document]: A list of chunked documents ready for vectorization.
        """
        if not languages:
            languages = ["python"]

        suffixes = [SUFFEXES[lang] for lang in languages]

        loader = GenericLoader.from_filesystem(
            self.source_path,
            glob="**/*",
            suffixes=suffixes,
            parser=LanguageParser(language="python", parser_threshold=500),
            parser_kwargs={
                "autodetect_encoding": True
            }
        )

        raw_docs = loader.load()

        python_splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON,
            chunk_size=1000,
            chunk_overlap=150
        )
        structured_docs = python_splitter.split_documents(raw_docs)

        print(f"Found {len(structured_docs)} fragmented blocks of code")

        return structured_docs