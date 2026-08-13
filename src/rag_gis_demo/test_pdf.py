"""Print the extracted text of a single PDF, to eyeball the cleaning pipeline."""

import argparse
import sys

from langchain_community.document_loaders import PyPDFLoader

from rag_gis_demo.ingest import DATA_PATH, clean_documents


DEFAULT_PDF = "law/min_reg/MR_No_001.pdf"


def main() -> None:
    # The Windows console defaults to cp1252, which cannot print Thai.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Print page_content of a PDF under data/."
    )
    parser.add_argument(
        "pdf",
        nargs="?",
        default=DEFAULT_PDF,
        help=f"Path relative to {DATA_PATH} (default: {DEFAULT_PDF}).",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Skip normalization/watermark stripping to compare with the raw text.",
    )
    parser.add_argument(
        "--page",
        type=int,
        help="Print only this page number (0-based, as stored in the metadata).",
    )
    args = parser.parse_args()

    path = DATA_PATH / args.pdf
    documents = PyPDFLoader(str(path)).load()
    if not args.raw:
        documents = clean_documents(documents)

    if args.page is not None:
        documents = [d for d in documents if d.metadata.get("page") == args.page]

    print(f"{path} -> {len(documents)} pages")
    for document in documents:
        print(f"\n===== page {document.metadata.get('page')} =====")
        print(document.page_content)


if __name__ == "__main__":
    main()
