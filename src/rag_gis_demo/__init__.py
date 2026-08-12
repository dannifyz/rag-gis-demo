import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")


def get_llm() -> ChatGoogleGenerativeAI:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            f"GOOGLE_API_KEY not set. Add it to {PROJECT_ROOT / '.env'}"
        )

    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=api_key,
    )


def main() -> None:
    llm = get_llm()
    response = llm.invoke("วันนี้กินอะไรดี!")
    print(response.content)


if __name__ == "__main__":
    main()
