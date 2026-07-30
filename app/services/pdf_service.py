import os

import re

import shutil

import pdfplumber

from fastapi import UploadFile


LIGATURES = {
    "ﬁ": "fi",
    "ﬂ": "fl",
    "ﬀ": "ff",
    "ﬃ": "ffi",
    "ﬄ": "ffl",
    "\u2019": "'",
    "\u2018": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2014": "—",
    "\u2013": "-",
}


def save_pdf(file: UploadFile, upload_dir: str) -> str:
    os.makedirs(upload_dir, exist_ok=True)

    if file.filename is None:
        raise ValueError("Uploaded PDF must have a filename")

    file_path = os.path.join(upload_dir, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)


    return file_path

def clean_text(text: str) -> str:
    for li, rep in LIGATURES.items():
        text = text.replace(li, rep)

    text = re.sub(r"-\n", "", text)

    lines = text.split("\n")

    paragraphs: list[str] = []
    current_paragraph: list[str] = []

    for line in lines:
        stripped = line.strip()

        if not stripped:
            if current_paragraph:
                paragraphs.append(" ".join(current_paragraph))

            continue

        if re.fullmatch(r"\d+", stripped):
            continue

        current_paragraph.append(stripped)

    if current_paragraph:
        paragraphs.append(" ".join(current_paragraph))

    return "\n\n".join(paragraphs)


def extract_pages_from_pdf(file_path: str) -> list[dict[str, int | str]]:
    pages: list[dict[str, int | str]] = []

    with pdfplumber.open(file_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            raw_text = page.extract_text(x_tolerance=3, y_tolerance=3)

            if not raw_text:
                continue

            cleaned = clean_text(raw_text)

            if cleaned:
                pages.append(
                    {
                        "page_number": page_number,
                        "text": cleaned
                    }
                )

    return pages