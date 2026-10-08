"""
CLI for ingesting SOP documents into the vector store.
Usage: python -m app.rag.ingest --dir /data/sops --vertical flight
"""

import argparse
import os
import hashlib
from pathlib import Path
from typing import List
import pypdf
from docx import Document as DocxDocument
from app.rag.store import upsert_sop_chunks, SopStore
from app.schemas.enums import Vertical


def extract_text_from_pdf(file_path: Path) -> List[Tuple[str, int]]:
    """
    Extract text from PDF file, returning list of (text, page_number) tuples.
    """
    text_by_page = []
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            for page_num, page in enumerate(pdf_reader.pages, start=1):
                text = page.extract_text()
                if text.strip():  # Only include pages with text
                    text_by_page.append((text.strip(), page_num))
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
    return text_by_page


def extract_text_from_docx(file_path: Path) -> List[Tuple[str, int]]:
    """
    Extract text from DOCX file, returning list of (text, page_number) tuples.
    Note: DOCX doesn't have inherent page numbers, so we'll approximate.
    """
    text_by_page = []
    try:
        doc = DocxDocument(file_path)
        full_text = []
        current_page_text = []
        PAGE_SIZE_WORDS = 500  # Approximate words per page
        word_count = 0
        page_num = 1

        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if text:
                words = text.split()
                word_count += len(words)
                current_page_text.append(text)

                # If we've exceeded approx page size, create a "page"
                if word_count >= PAGE_SIZE_WORDS:
                    page_text = ' '.join(current_page_text)
                    text_by_page.append((page_text, page_num))
                    current_page_text = []
                    word_count = 0
                    page_num += 1

        # Add remaining text as final page
        if current_page_text:
            page_text = ' '.join(current_page_text)
            text_by_page.append((page_text, page_num))

    except Exception as e:
        print(f"Error reading DOCX {file_path}: {e}")
    return text_by_page


def chunk_text(text: str, chunk_size: int = 700, overlap: int = 120) -> List[str]:
    """
    Split text into chunks with specified size and overlap.
    """
    if not text.strip():
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]

        # Try to break at sentence boundary if possible
        if end < text_length:
            # Look for sentence ending near the end
            last_period = chunk.rfind('.')
            last_exclamation = chunk.rfind('!')
            last_question = chunk.rfind('?')
            break_point = max(last_period, last_exclamation, last_question)

            if break_point > chunk_size * 0.8:  # Only break if we're not losing too much
                chunk = text[start:start + break_point + 1]
                end = start + break_point + 1

        chunks.append(chunk.strip())
        start = end - overlap

        # Prevent infinite loop
        if start >= text_length - overlap:
            break

    return [chunk for chunk in chunks if chunk.strip()]


def process_sop_file(file_path: Path, vertical: Vertical) -> List[dict]:
    """
    Process a single SOP file (PDF or DOCX) and return chunk dicts ready for upserting.
    """
    chunks = []

    # Determine file type and extract text
    if file_path.suffix.lower() == '.pdf':
        pages_text = extract_text_from_pdf(file_path)
    elif file_path.suffix.lower() in ['.docx', '.doc']:
        pages_text = extract_text_from_docx(file_path)
    else:
        print(f"Unsupported file type: {file_path}")
        return chunks

    # Process each page
    for text, page_num in pages_text:
        # Create chunks from this page's text
        text_chunks = chunk_text(text)

        for i, chunk_text in enumerate(text_chunks):
            # Generate deterministic ID based on source, page, and chunk index
            id_string = f"{file_path.name}_{page_num}_{i}"
            chunk_id = hashlib.sha1(id_string.encode()).hexdigest()

            chunk_data = {
                "id": chunk_id,
                "text": chunk_text,
                "source": file_path.name,
                "page": page_num,
                "vertical": vertical.value,
                "sop_version": "v1",  # Could be extracted from filename or metadata
                "section_title": f"Page {page_num}, Chunk {i+1}"  # Simple section title
            }
            chunks.append(chunk_data)

    return chunks


def ingest_sop_directory(directory_path: str, vertical: str):
    """
    Ingest all supported SOP files from a directory.
    """
    # Convert vertical string to enum
    try:
        vertical_enum = Vertical(vertical.lower())
    except ValueError:
        print(f"Error: Invalid vertical '{vertical}'. Valid options are: {[v.value for v in Vertical]}")
        return

    directory = Path(directory_path)
    if not directory.exists():
        print(f"Error: Directory '{directory_path}' does not exist")
        return

    # Find all supported files
    supported_extensions = {'.pdf', '.docx', '.doc'}
    files_to_process = []

    for ext in supported_extensions:
        files_to_process.extend(directory.glob(f"*{ext}"))

    if not files_to_process:
        print(f"No supported files found in {directory_path}")
        return

    print(f"Found {len(files_to_process)} files to process for vertical '{vertical}'")

    total_chunks = 0
    for file_path in files_to_process:
        print(f"Processing {file_path.name}...")
        chunks = process_sop_file(file_path, vertical_enum)
        if chunks:
            upserted = upsert_sop_chunks(chunks)
            total_chunks += upserted
            print(f"  -> Added {upserted} chunks from {file_path.name}")
        else:
            print(f"  -> No chunks extracted from {file_path.name}")

    print(f"\nIngestion complete. Total chunks added: {total_chunks}")

    # Show collection stats
    store = SopStore()
    print(f"Total chunks in collection: {store.count()}")


def main():
    parser = argparse.ArgumentParser(description="Ingest SOP documents into vector store")
    parser.add_argument("--dir", required=True, help="Directory containing SOP files (PDF/DOCX)")
    parser.add_argument("--vertical", required=True, choices=[v.value for v in Vertical],
                       help="Vertical category for the SOP files")
    parser.add_argument("--clear", action="store_true",
                       help="Clear existing collection before ingesting")

    args = parser.parse_args()

    if args.clear:
        print("Clearing existing collection...")
        store = SopStore()
        store.clear()
        print("Collection cleared.")

    ingest_sop_directory(args.dir, args.vertical)


if __name__ == "__main__":
    main()