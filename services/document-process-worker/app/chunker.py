import re

def split_into_sentences(text: str) -> list[str]:
    blocks = re.split(
        r"\n+",
        text
    )

    units = []

    for block in blocks:
        block = block.strip()

        if not block:
            continue

        sentences = re.split(
            r"(?<=[.!?])\s+",
            block
        )

        units.extend(
            sentence.strip()
            for sentence in sentences
            if sentence.strip()
        )

    return units

def chunk_pages(
        pages:list[dict],
        chunk_size:int = 1000,
        overlap: int = 200,
)->list[dict]:
    chunks = []

    for page in pages:
        page_number = page["page_number"]
        sentences =  split_into_sentences(page["text"])

        current_chunk = ""
        prev_sentences = []

        for sentence in sentences:

            if not current_chunk:
                current_chunk = sentence
                prev_sentences = [sentence]
                continue
            potential_chunk = f"{current_chunk} {sentence}"

            if len(potential_chunk)<= chunk_size:
                current_chunk = potential_chunk
                prev_sentences.append(sentence)
            else:
                chunks.append({
                    "page_number": page_number,
                    "text": current_chunk
                })
                overlap_text = ""
                overlap_sentences = []

                for prev_sen in reversed(prev_sentences):
                    potential_overlap = (
                        f"{prev_sen} {overlap_text}"
                    ).strip()

                    overlap_text = potential_overlap
                    overlap_sentences.insert(
                        0,
                        prev_sen
                    )

                    if len(overlap_text) >= overlap:
                        break

                current_chunk = (
                    f"{overlap_text} {sentence}"
                ).strip()

                prev_sentences = (
                    overlap_sentences+[sentence]
                )

        if current_chunk:
            chunks.append(
                {
                    "page_number": page_number,
                    "text": current_chunk
                }
            )
        
    return chunks