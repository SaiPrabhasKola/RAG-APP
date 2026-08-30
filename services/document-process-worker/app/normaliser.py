import re
import unicodedata


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)

    text = text.replace("\u00ad", "")

    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    text = re.sub(r"[ \t]+", " ", text)

    text = re.sub(r"\n{3,}", "\n\n", text)

    text = re.sub(r" *\n *", "\n", text)

    return text.strip()