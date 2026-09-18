from app.agents.segmenter import segment_document


def test_segmenter():
    text = "# Main\n\nPara 1.\n\n- Bullet 1\n- Bullet 2\n\n**Bold** text."
    segments = segment_document(text, "rfp")
    assert len(segments) == 5

    # Check sections
    assert segments[0].section == "Main"
    assert segments[1].section == "Main"

    # Check char span round-trip
    first_seg_text = text[segments[0].char_span[0] : segments[0].char_span[1]]
    assert first_seg_text.startswith("# Main")

    # Check markdown stripping in parsed text
    assert segments[0].text == "Main"
    assert segments[4].text == "Bold text."
