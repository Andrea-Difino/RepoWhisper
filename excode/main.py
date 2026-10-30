from ingestion.ingestor import Ingestor


def main():
    ingestor = Ingestor("https://github.com/Andrea-Difino/WaveRedact")
    docs = ingestor.ingest()

    if docs:
        print("\n📝 Esempio di cosa è stato estratto (Primo Blocco):")
        print(f"Metadati: {docs[0].metadata}") 
        print(f"Anteprima Codice:\n{docs[0].page_content[:250]}...")


if __name__ == "__main__":
    main()
    
