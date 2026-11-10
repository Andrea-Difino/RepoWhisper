from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from langchain_core.documents import Document
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter

LANGUAGE_MAP: dict[str, dict] = {
    "python" : {"extension": ".py", "enum": Language.PYTHON},
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

        all_docs = []

        for lang_key in languages:
            lang_key = lang_key.lower()
            
            if lang_key not in LANGUAGE_MAP:
                print(f"⚠️ Warning: language '{lang_key}' not supported by the Ingestor. It will be ignored.")
                continue

            config = LANGUAGE_MAP[lang_key]
            suffix: str = config["extension"]
            lang_enum: Language = config["enum"]

            loader = GenericLoader.from_filesystem(
                self.source_path,
                glob="**/*",
                suffixes=[suffix],
                parser=LanguageParser(language=lang_key, parser_threshold=500), #type: ignore
                parser_kwargs={
                    "autodetect_encoding": True
                }
            )

            raw_docs = loader.load()

            if not raw_docs:
                continue

            python_splitter = RecursiveCharacterTextSplitter.from_language(
                language=lang_enum,
                chunk_size=1000,
                chunk_overlap=150
            )
            structured_docs = python_splitter.split_documents(raw_docs)
            all_docs.extend(structured_docs)

        return all_docs