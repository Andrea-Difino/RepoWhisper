import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pydantic import SecretStr

from repowhisper import RepoWhisper

load_dotenv()

def main():
    api_key = SecretStr(os.environ.get("GROQ_API_KEY", ""))
    my_llm = ChatGroq(
        api_key=api_key, 
        model="openai/gpt-oss-120b"
    )
    
    engine = RepoWhisper(
        source_target="https://github.com/Andrea-Difino/WaveRedact",
        llm=my_llm
    )
    
    try:
        json_file = engine.generate_documentation()
        output_filepath = "repowhisper_analysis.json"

        with open(output_filepath, "w", encoding="utf-8") as file:
            file.write(json_file)

    except Exception as e:
        print(f"❌ Si è verificato un errore durante l'analisi: {e}")

if __name__ == "__main__":
    main()