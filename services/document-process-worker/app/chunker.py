from langchain_text_splitters import RecursiveCharacterTextSplitter


# ---------------------------------------------------------------------------
# Heading / subsection detection
# ---------------------------------------------------------------------------

_COMMON_HEADINGS = {
    "summary",
    "objective",
    "profile",
    "experience",
    "work experience",
    "professional experience",
    "employment history",
    "projects",
    "skills",
    "technical skills",
    "core competencies",
    "education",
    "certifications",
    "achievements",
    "publications",
    "interests",
    "references",
    "awards",
    "contact",
}


def looks_like_heading(line: str) -> bool:
    """
    Conservatively detect likely top-level section headings from
    plain extracted PDF text.
    """

    line = line.strip()

    if not line or len(line) > 80:
        return False

    normalized = line.rstrip(":").strip()
    words = normalized.split()

    if not words or len(words) > 6:
        return False

    # Markdown-style heading
    if normalized.startswith("#"):
        return True

    # Known section heading
    if normalized.lower() in _COMMON_HEADINGS:
        return True

    # Uppercase section heading such as:
    # EXPERIENCE
    # PROJECTS
    # TECHNICAL SKILLS
    if normalized.isupper() and 2 <= len(words) <= 5:
        return True

    return False


def looks_like_subheading(line: str) -> bool:
    """
    Detect subsection/project titles.

    Resume PDFs often flatten a hyperlink into text, producing lines such as:

        Distributed Real-time Chat System GitHub
        Financial Records Backend GitHub
        DevDuel — Dynamic Code Judge Platform GitHub
        Braino — Knowledge Repository GitHub

    These are treated as subsection boundaries.
    """

    line = line.strip()

    if not line or len(line) > 100:
        return False

    normalized = line.rstrip(":").strip()

    # Never classify a top-level section as a subsection.
    if normalized.lower() in _COMMON_HEADINGS:
        return False

    # Project/link title pattern produced by PDF extraction.
    if normalized.lower().endswith(" github"):
        return True

    return False


def clean_subheading(line: str) -> str:
    """
    Remove the flattened GitHub link text from a subsection title.
    """

    line = line.strip()

    if line.lower().endswith(" github"):
        line = line[:-len(" github")].rstrip()

    return line


# ---------------------------------------------------------------------------
# Recursive character splitting
# ---------------------------------------------------------------------------

_SECTION_SEPARATORS = [
    "\n\n",

    # Preserve line boundaries.
    "\n",

    # Common PDF bullet characters.
    "\uf0b7",  # Wingdings / private-use bullet
    "\u25cf",  # ●
    "\u2022",  # •
    "\u2023",  # ‣
    "\u25aa",  # ▪

    # Sentence boundaries.
    ". ",
    "! ",
    "? ",
    "; ",

    # Last-resort fallbacks.
    ", ",
    " ",
    "",
]


def _make_splitter(
    chunk_size: int,
    overlap: int,
) -> RecursiveCharacterTextSplitter:

    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=_SECTION_SEPARATORS,
        keep_separator=True,
    )


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def chunk_pages(
    pages: list[dict],
    chunk_size: int = 700,
    overlap: int = 150,
) -> list[dict]:
    """
    Convert extracted PDF pages into section/subsection-aware chunks.

    Input:

        [
            {
                "page_number": 1,
                "text": "..."
            }
        ]

    Output:

        [
            {
                "page_number": 1,
                "chunk_index": 0,
                "section": "PROJECTS",
                "subsection": "Distributed Real-time Chat System",
                "text": "...",
                "char_count": 650
            }
        ]

    Important properties:

    - Top-level sections create hard chunk boundaries.
    - Subsections/projects create hard chunk boundaries.
    - Chunks never cross from one project into another.
    - RecursiveCharacterTextSplitter handles size-bounded splitting.
    - Paragraphs, lines, bullets and sentences are preferred boundaries.
    - Overlap is preserved within the same section/subsection.
    - Section/subsection metadata is included in the chunk text.
    """

    chunks: list[dict] = []
    chunk_index = 0

    current_section: str | None = None
    current_subsection: str | None = None

    current_lines: list[str] = []
    current_page: int | None = None

    def flush_group() -> None:
        nonlocal chunk_index
        nonlocal current_lines

        if not current_lines or current_page is None:
            current_lines = []
            return

        group_text = "\n".join(current_lines).strip()

        if not group_text:
            current_lines = []
            return

        # ---------------------------------------------------------------
        # Build contextual header.
        #
        # Example:
        #
        # PROJECTS
        #
        # Distributed Real-time Chat System
        # ---------------------------------------------------------------

        header_parts = [
            value
            for value in (
                current_section,
                current_subsection,
            )
            if value
        ]

        header = "\n\n".join(header_parts)

        if header:
            header += "\n\n"

        # Leave room for the metadata header.
        body_budget = max(
            chunk_size - len(header),
            chunk_size // 2,
        )

        splitter = _make_splitter(
            body_budget,
            min(overlap, body_budget // 2),
        )

        pieces = splitter.split_text(group_text)

        for piece in pieces:
            piece = piece.strip()

            if not piece:
                continue

            text = f"{header}{piece}".strip()

            chunks.append(
                {
                    "page_number": current_page,
                    "chunk_index": chunk_index,
                    "section": current_section,
                    "subsection": current_subsection,
                    "text": text,
                    "char_count": len(text),
                }
            )

            chunk_index += 1

        current_lines = []

    # -------------------------------------------------------------------
    # Process pages
    # -------------------------------------------------------------------

    for page in pages:

        page_number = page["page_number"]
        text = page["text"]

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        for line in lines:

            # -----------------------------------------------------------
            # Top-level section boundary
            # -----------------------------------------------------------

            if looks_like_heading(line):

                flush_group()

                current_section = (
                    line.rstrip(":").strip()
                )

                current_subsection = None
                current_page = page_number

                continue

            # -----------------------------------------------------------
            # Subsection / project boundary
            # -----------------------------------------------------------

            if looks_like_subheading(line):

                flush_group()

                current_subsection = clean_subheading(line)

                current_page = page_number

                continue

            # -----------------------------------------------------------
            # Normal content
            # -----------------------------------------------------------

            if current_page is None:
                current_page = page_number

            current_lines.append(line)

    # Flush final section/subsection.
    flush_group()

    return chunks