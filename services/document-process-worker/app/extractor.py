import fitz
from app.normaliser import normalize_text

def extract_text(data:bytes)-> list[dict]:
    document = fitz.open(stream=data,filetype="pdf")

    pages = []

    for page_number,page in enumerate(document,start=1):
        page_text = normalize_text(page.get_text())
        if page_text:
            pages.append(
                {
                    "page_number":page_number,
                    "text": page_text
                }
            )

    document.close()
    return pages