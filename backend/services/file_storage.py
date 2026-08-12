import os
from pathlib import Path
from pypdf import PdfReader
from ..config import settings


def ensure_upload_dir():
    Path(settings.upload_dir).mkdir(exist_ok=True)


def save_uploaded_file(file_content: bytes, filename: str) -> str:
    ensure_upload_dir()
    file_path = os.path.join(settings.upload_dir, filename)
    with open(file_path, "wb") as f:
        f.write(file_content)
    return file_path


def extract_text_from_file(file_path: str) -> str:
    if file_path.endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    else:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()


def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    try:
        with open(pdf_path, "rb") as f:
            reader = PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    return text
