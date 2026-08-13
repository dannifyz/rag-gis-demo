import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from rag_gis_demo import PROJECT_ROOT, api_key
from rag_gis_demo.vectorstore import vectorstore


RESULT_PATH = PROJECT_ROOT / "result"

PROMPT_TEMPLATE = """ตอบคำถามโดยอ้างอิงจากบริบทต่อไปนี้เท่านั้น:

{context}

---

ตอบคำถามนี้จากบริบทด้านบน: {question}
ถ้าบริบทไม่มีข้อมูลเพียงพอ ให้ตอบว่าไม่พบข้อมูลในเอกสาร
"""


def get_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=api_key,
    )


def format_sources(documents: list[Document]) -> list[str]:
    """Turn chunk ids like "law/act/law_001.pdf:6:2" into
    "[1] law/act/law_001.pdf (หน้า 7)".

    The path is kept relative to data/, so documents with the same file name in
    different folders stay distinguishable. Chunks from the same document are
    merged into one numbered entry, in the order they were retrieved.
    """
    pages_by_source: dict[str, list[int]] = {}
    for document in documents:
        chunk_id = document.metadata.get("id")
        source = chunk_id.rsplit(":", 2)[0] if chunk_id else "unknown"

        pages = pages_by_source.setdefault(source, [])
        page = document.metadata.get("page")
        if page is not None and page + 1 not in pages:
            # Chroma stores 0-based page numbers.
            pages.append(page + 1)

    sources = []
    for index, (source, pages) in enumerate(pages_by_source.items(), start=1):
        entry = f"[{index}] {source}"
        if pages:
            entry += f" (หน้า {', '.join(str(page) for page in sorted(pages))})"
        sources.append(entry)

    return sources


def build_result_path(now: datetime) -> Path:
    """Return result/yyyymmdd-hhmmss-result.md."""
    RESULT_PATH.mkdir(parents=True, exist_ok=True)

    stem = now.strftime("%Y%m%d-%H%M%S")
    path = RESULT_PATH / f"{stem}-result.md"

    return path


def save_result(question: str, answer: str, sources: list[str]) -> Path:
    # Local time, so the file name matches the clock the user is looking at.
    path = build_result_path(datetime.now(tz=UTC).astimezone())
    source_lines = "\n".join(sources) if sources else "ไม่มี"

    path.write_text(
        f"# คำถาม\n\n{question}\n\n# คำตอบ\n\n{answer}\n\n# อ้างอิง\n\n{source_lines}\n",
        encoding="utf-8",
    )

    return path


def query_rag(query_text: str, k: int = 5) -> str:
    results = vectorstore.similarity_search_with_score(query_text, k=k)
    documents = [document for document, _score in results]

    context_text = "\n\n---\n\n".join(document.page_content for document in documents)
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE).format(
        context=context_text, question=query_text
    )

    response = get_llm().invoke(prompt)
    answer = str(response.content)

    sources = format_sources(documents)
    path = save_result(query_text, answer, sources)

    print(f"Response: {answer}")
    print(f"Sources: {' '.join(sources)}")
    print(f"Saved to: {path}")

    return answer


def main() -> None:
    # The default Windows console encoding (cp1252) can't print Thai.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Ask a question about the documents.")
    parser.add_argument("query_text", type=str, help="The query text.")
    parser.add_argument(
        "-k", type=int, default=5, help="Number of chunks to retrieve (default: 5)."
    )
    args = parser.parse_args()

    query_rag(args.query_text, k=args.k)


if __name__ == "__main__":
    main()
