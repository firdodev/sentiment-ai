"""AI për tekst, dokumente dhe imazhe: nxjerr komentet nga skedarë të ndryshëm.

- .txt  -> një koment për rresht
- .csv  -> kolona 'koment' (ose kolona e parë tekstuale)
- .pdf  -> kërkon `pypdf` (opsionale)
- .png/.jpg -> OCR me `pytesseract` + Tesseract (opsionale), p.sh. screenshot komentesh
"""
import io
from pathlib import Path

import pandas as pd

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}


def _lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if len(line.strip()) >= 2]


def from_csv(data: bytes, column: str | None = None) -> list[str]:
    df = pd.read_csv(io.BytesIO(data))
    if column is None:
        column = next((c for c in df.columns if c.lower() in {"koment", "komenti", "text", "comment"}),
                      None) or df.select_dtypes(exclude="number").columns[0]
    return [str(t) for t in df[column].dropna() if str(t).strip()]


def from_pdf(data: bytes) -> list[str]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("Për PDF instalo: pip install pypdf") from exc
    reader = PdfReader(io.BytesIO(data))
    return _lines("\n".join(page.extract_text() or "" for page in reader.pages))


def from_image(data: bytes) -> list[str]:
    try:
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Për OCR instalo: pip install pytesseract pillow + Tesseract OCR") from exc
    image = Image.open(io.BytesIO(data)).convert("L")  # gri -> OCR më i saktë
    try:
        text = pytesseract.image_to_string(image, lang="sqi+eng")
    except pytesseract.TesseractError:
        text = pytesseract.image_to_string(image)  # paketa e gjuhës shqipe mungon
    return _lines(text)


def extract_comments(filename: str, data: bytes, column: str | None = None) -> list[str]:
    ext = Path(filename).suffix.lower()
    if ext == ".csv":
        return from_csv(data, column)
    if ext == ".pdf":
        return from_pdf(data)
    if ext in IMAGE_EXT:
        return from_image(data)
    return _lines(data.decode("utf-8", errors="replace"))
