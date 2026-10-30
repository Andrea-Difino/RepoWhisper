from agents.navigator_agent import CodeNavigatorAgent
from ingestion.ingestor import Ingestor
from ingestion.source_manager import SourceManager
from langchain_core.language_models.chat_models import BaseChatModel
from memory.chroma_db_manager import ChromaDBManager


class RepoWhisper:
    """
    The main Facade for the Excode library.
    This class orchestrates the entire process from fetching the repository 
    to answering complex questions using AI agents.
    
    It follows the Dependency Inversion Principle by accepting any language 
    model that adheres to the BaseChatModel interface.
    """

    def __init__(self, source_target: str, llm: BaseChatModel):
        """
        Initializes the Excode engine.
        
        Args:
            source_target (str): The URL of the git repository or local path.
            llm (BaseChatModel): The initialized LangChain chat model.
        """
        self.source_target = source_target
        self.llm = llm
        
        # Internal state managers
        self._source_manager = SourceManager(self.source_target)
        self._memory_manager = None
        self._navigator = CodeNavigatorAgent(self.llm)
        self._is_ingested = False

    def build_knowledge_base(self) -> None:
        """
        Downloads, parses, and vectorizes the source code.
        Must be called before asking questions.
        
        Raises:
            RuntimeError: If the ingestion process fails.
        """
        try:
            repo_path = self._source_manager.get_path()
            ingestor = Ingestor(repo_path)
            docs = ingestor.ingest()
            
            if not docs:
                raise RuntimeError("No parsable code found in the target source.")
                
            self._memory_manager = ChromaDBManager(docs)
            self._is_ingested = True
            print("✅ Knowledge Base built successfully!")
            
        except Exception as e:
            self._source_manager.cleanup()
            raise RuntimeError(f"Failed to build knowledge base: {e}")

    def ask(self, query: str) -> str:
        """
        Queries the AI agent regarding the ingested source code.
        
        Args:
            query (str): The question or task for the AI.
            
        Returns:
            str: The AI's explanation based on the code context.
            
        Raises:
            ValueError: If called before build_knowledge_base().
        """
        if not self._is_ingested or not self._memory_manager:
            raise ValueError(
                "Knowledge base is empty. Call build_knowledge_base() first."
            )
            
        print(f"🔍 Searching context for: '{query}'...")

        search_results = self._memory_manager.search_code(query, top_k=3)

        context_text = "\n\n".join(
            [f"--- File: {doc.metadata.get('source', 'Unknown')} ---\n{doc.page_content}" 
             for doc in search_results]
        )
        
        print("🧠 Analyzing code logic...")
        explanation = self._navigator.analyze(query=query, context=context_text)
        
        return explanation

    def cleanup(self) -> None:
        """
        Frees up resources and temporary directories.
        """
        self._source_manager.cleanup()