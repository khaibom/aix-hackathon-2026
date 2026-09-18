import re
from typing import Literal

from app.models.schemas import Segment


def segment_document(text: str, doc_type: Literal["rfp", "draft"]) -> list[Segment]:
    """Parse markdown text into Segments by paragraphs, headings, and lists."""
    segments = []
    section = "preamble"
    para_idx = 0
    current_start = -1

    def flush(end_pos: int) -> None:
        nonlocal current_start, para_idx, section
        if current_start != -1:
            raw = text[current_start:end_pos]
            clean = re.sub(r"[*_#`]", "", raw).strip()
            if clean:
                segments.append(
                    Segment(
                        id=f"{doc_type}_{len(segments):03d}",
                        section=section,
                        para_idx=para_idx,
                        text=clean,
                        char_span=(current_start, end_pos),
                    )
                )
                para_idx += 1
            current_start = -1

    for m in re.finditer(r"(.*)(\n|$)", text):
        line = m.group(1)
        start = m.start()

        is_blank = not line.strip()
        is_list = re.match(r"^\s*([-*]|\d+\.)\s+", line)
        is_heading = re.match(r"^(#+)\s+(.*)", line)

        if is_blank:
            flush(start)
        elif is_heading:
            flush(start)
            current_start = start
            section = is_heading.group(2).strip()
        elif is_list:
            flush(start)
            current_start = start
        else:
            if current_start == -1:
                current_start = start

    flush(len(text))
    return segments
