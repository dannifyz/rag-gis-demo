import argparse

from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag_gis_demo import PROJECT_ROOT
from rag_gis_demo.vectorstore import vectorstore


DATA_PATH = PROJECT_ROOT / "data"


def load_documents() -> list[Document]:
    loader = PyPDFDirectoryLoader(str(DATA_PATH), glob="**/*.pdf")
    return loader.load()


def split_documents(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=80,
        length_function=len,
        is_separator_regex=False,
    )
    return splitter.split_documents(documents)


def calculate_chunk_ids(chunks: list[Document]) -> list[Document]:
    """Give each chunk an id like "law/act/law_001.pdf:6:2" ({source}:{page}:{index})."""
    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source")
        if source:
            # Store the path relative to data/ so ids don't depend on where the
            # project lives on disk.
            source = (
                PROJECT_ROOT.joinpath(source)
                .resolve()
                .relative_to(DATA_PATH)
                .as_posix()
            )
        page = chunk.metadata.get("page")
        current_page_id = f"{source}:{page}"

        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        chunk.metadata["id"] = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id

    return chunks


def add_to_database(chunks: list[Document]) -> None:
    chunks_with_ids = calculate_chunk_ids(chunks)

    existing_ids = set(vectorstore.get(include=[])["ids"])
    print(f"Number of existing documents in DB: {len(existing_ids)}")

    # Only add documents that aren't in the DB yet.
    new_chunks: list[Document] = []
    seen_ids = set(existing_ids)
    for chunk in chunks_with_ids:
        chunk_id = chunk.metadata["id"]
        if chunk_id not in seen_ids:
            seen_ids.add(chunk_id)
            new_chunks.append(chunk)

    if not new_chunks:
        print("No new documents to add")
        return

    print(f"Adding new documents: {len(new_chunks)}")
    new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
    vectorstore.add_documents(new_chunks, ids=new_chunk_ids)


def clear_database() -> None:
    vectorstore.reset_collection()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest PDF files into the vector store."
    )
    parser.add_argument("--reset", action="store_true", help="Reset the database.")
    args = parser.parse_args()

    if args.reset:
        print("Clearing Database")
        clear_database()

    documents = load_documents()
    print(f"Loaded {len(documents)} pages from {DATA_PATH}")

    chunks = split_documents(documents)
    print(f"Split into {len(chunks)} chunks")

    add_to_database(chunks)


if __name__ == "__main__":
    main()
