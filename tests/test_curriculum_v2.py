"""Curriculum v2 schema, provenance validation and exam-format reference."""

from copy import deepcopy

from courses.mission_v2_example import REFERENCE_COURSE
from courses.validation import validate_course
from mock_tests.formats import EXAM_FORMATS, public_format


def test_reference_mission_unit_validates():
    assert validate_course(REFERENCE_COURSE) == []


def test_reviewed_publication_requires_reviewer_details():
    course = deepcopy(REFERENCE_COURSE)
    course.contentStatus = "published"
    course.provenance.review_state = "reviewed"
    course.provenance.reviewer = None

    issues = validate_course(course)

    assert any("reviewed content needs reviewer" in issue for issue in issues)


def test_exam_content_requires_verified_on_date():
    course = deepcopy(REFERENCE_COURSE)
    course.units[0].title = "TEF-style practice"
    course.units[0].provenance.exam_format_version = "2026.11"
    course.units[0].provenance.verified_on = None

    issues = validate_course(course)

    assert any("verified-on" in issue for issue in issues)


def test_legacy_courses_remain_valid():
    from courses import COURSE_CATALOG
    from courses.validation import validate_catalog
    assert validate_catalog(COURSE_CATALOG) == {}


def test_exam_formats_are_sourced_and_honest():
    assert "Express Entry uses" in EXAM_FORMATS["tef"].score_scale_note
    assert any("wrong TEF column" in warning for warning in EXAM_FORMATS["tef"].warnings)
    assert EXAM_FORMATS["tcf"].verified_on == "2026-11-23"

    payload = public_format(EXAM_FORMATS["tef"])
    nclc7 = next(band for band in payload["scoreBands"] if band["nclc"] == 7)
    assert nclc7["listening"] == "249–279"
    assert nclc7["reading"] == "207–232"
    assert payload["practiceNotice"].startswith("Original, unofficial practice")
    assert payload["sourceUrls"]


def test_exam_formats_endpoint(client):
    r = client.get("/api/exam/formats")
    assert r.status_code == 200
    data = r.json()
    assert set(data["formats"]) == {"tef", "tcf"}
    assert data["formats"]["tcf"]["verifiedOn"] == "2026-11-23"
    assert "Not an official score" in data["formats"]["tcf"]["practiceNotice"]
