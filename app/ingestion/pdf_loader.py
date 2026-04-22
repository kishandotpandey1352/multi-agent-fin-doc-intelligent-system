from pathlib import Path
from typing import List

from pypdf import PdfReader


class Page:
    def __init__(self, page_number: int, text: str) -> None:
        self.page_number = page_number
        self.text = text


def load_pdf_pages(pdf_path: Path) -> List[Page]:
    reader = PdfReader(str(pdf_path))
    pages: List[Page] = []

    for idx, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        cleaned = "\n".join(line.strip() for line in text.splitlines())
        pages.append(Page(page_number=idx, text=cleaned.strip()))

    return pages
