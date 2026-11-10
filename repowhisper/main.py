import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pydantic import SecretStr

from repowhisper import RepoWhisper, UserLevel

load_dotenv()

def main():
    api_key = SecretStr(os.environ.get("GROQ_API_KEY", ""))
    my_llm = ChatGroq(
        api_key=api_key, 
        model="openai/gpt-oss-120b",
        max_tokens=6000,
        max_retries=6,
    )

    engine = RepoWhisper(
        source_target="https://github.com/Andrea-Difino/WaveRedact",
        llm=my_llm,
        user_level=UserLevel.JUNIOR
    )

    try:
        engine.serve_ui()
    except Exception as e:
        print(f"An error occured during the analysis: {e}")

if __name__ == "__main__":
    main()