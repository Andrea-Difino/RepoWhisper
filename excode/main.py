from ingestion.ingestor import Ingestor
from ingestion.source_manager import SourceManager
from memory.chroma_db_manager import ChromaDBManager


def main():
    target_url = "https://github.com/nsidnev/fastapi-realworld-example-app"

    source_manager = SourceManager(target=target_url)

    try:
        repo_path = source_manager.get_path()

        ingestor = Ingestor(repo_path)
        docs = ingestor.ingest()

        if docs:
            memory_man = ChromaDBManager(docs)
            results = memory_man.search_code("How is the database connection established?", top_k=1)

            if results:
                print(f"\n📝 Extracted Block Example for query: '{"How is the database connection established?"}'")
                print(f"Metadata: {results[0].metadata}") 
                print(f"Code Preview:\n{results[0].page_content[:300]}...")
    
    except Exception as e:
        print(f"\n❌ Application Error: {e}")
    finally:
        source_manager.cleanup()


if __name__ == "__main__":
    main()
    
