from langchain_google_genai import ChatGoogleGenerativeAI

from rag_gis_demo import api_key


def get_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=api_key,
    )


def main() -> None:
    llm = get_llm()
    response = llm.invoke("สวัสดีครับ!")
    print(response.content)


if __name__ == "__main__":
    main()
