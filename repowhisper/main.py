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
        engine.build_knowledge_base()

        architecture = engine.get_architect_overview()
        print("\nANSWER:\n", architecture)
        
    finally:
        engine.cleanup()

if __name__ == "__main__":
    main()