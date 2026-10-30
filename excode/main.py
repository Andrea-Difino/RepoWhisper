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
            results = memory_man.search_code("How is the model initialized?", top_k=1)

            print("\n📝 Extracted Block Example:")
            print(f"Metadata: {docs[0].metadata}") 
            print(f"Code Preview:\n{docs[0].page_content[:250]}...")
            print(f"Query result preview:\n{results[0]}...")
    
    except Exception as e:
        print(f"\n❌ Application Error: {e}")
    finally:
        source_manager.cleanup()


if __name__ == "__main__":
    main()
    
