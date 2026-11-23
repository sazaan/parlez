"""Writing feedback must never embed user/AI text as executable HTML."""


from engine.writing import format_correction_for_display


def test_writing_feedback_escapes_dynamic_text():
    html = format_correction_for_display({
        "score": 80,
        "level_assessment": "<b>B1</b>",
        "original": "<script>alert(1)</script>",
        "corrected": "<img src=x onerror=alert(1)>",
        "corrections": [{
            "original": "<b>x</b>",
            "corrected": "<i>y</i>",
            "explanation": "<svg onload=alert(1)>",
        }],
        "strengths": ["<script>ok</script>"],
        "improvements": ["<em>more</em>"],
        "summary": "<script>bye</script>",
    })

    assert "<script>" not in html
    assert "<img" not in html
    assert "<svg" not in html
    assert "&lt;script&gt;" in html
    assert "&lt;img" in html
