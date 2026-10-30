import os
import tempfile

from git import Repo
from langchain_core.documents import Document
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser

SUFFEXES = {
    "python" : ".py",
    "javascript": ".js",
    "typescript": ".ts"
}

class Ingestor:
    

    def __init__(self, target_path_or_url: str):
        self.target = target_path_or_url
        self.temp_dir = None
        self.repo_path = self._prepare_repo()

    def _prepare_repo(self) -> str:
        if self.target.startswith("http://") or self.target.startswith("https://"):
            print("Cloning repository...")
            self.temp_dir = tempfile.TemporaryDirectory()
            Repo.clone_from(self.target, self.temp_dir.name)
            print(self.temp_dir.name)
            return self.temp_dir.name

        if os.path.exists(self.target):
            return self.target

        raise ValueError("URL or path is not valid")

    def ingest(self, languages: list[str] | None = None) -> list[Document]:
        """
            Analize sintax and divide code in blocks
        """
        if not languages:
            languages = ["python"]

        suffixes = [SUFFEXES[lang] for lang in languages]

        loader = GenericLoader.from_filesystem(
            self.repo_path,
            glob="**/*",
            suffixes=suffixes,
            parser=LanguageParser(language="python", parser_threshold=500)
        )

        documents = loader.load()
        print(f"Found {len(documents)} blocks of code")

        if self.temp_dir:
            self.temp_dir.cleanup()

        return documents