"""Course catalog integrity and curriculum-structure tests."""

from courses import COURSE_CATALOG, get_course
from courses.validation import validate_catalog


def test_a1_course_exists():
    course = get_course("A1")
    assert course is not None
    assert course.level == "A1"


def test_a1_has_eight_modules():
    course = get_course("A1")
    assert len(course.units) == 8


def test_a1_module_ids_are_unique():
    course = get_course("A1")
    ids = [unit.id for unit in course.units]
    assert len(ids) == len(set(ids))


def test_a1_modules_have_original_titles():
    course = get_course("A1")
    titles = [unit.title for unit in course.units]
    assert "Module 1 — Premiers contacts" in titles
    assert "Module 2 — Mon identité" in titles
    assert "Module 3 — Ma famille et mes proches" in titles
    assert "Module 4 — Ma journée" in titles
    assert "Module 5 — En ville" in titles
    assert "Module 6 — Manger et boire" in titles
    assert "Module 7 — Chez moi" in titles
    assert "Module 8 — Projets et loisirs" in titles


def test_a1_lessons_have_required_fields():
    course = get_course("A1")
    for unit in course.units:
        assert len(unit.lessons) >= 1
        assert unit.outcomes and unit.capstone and unit.capstoneCriteria
        for lesson in unit.lessons:
            assert lesson.id
            assert lesson.title
            assert lesson.titleFr
            assert lesson.vocabulary
            assert lesson.grammar
            assert lesson.dialogue
            assert lesson.exercises
            assert lesson.culturalNote
            assert lesson.transferTask
            assert lesson.skillTags


def test_a1_each_module_has_three_lessons():
    course = get_course("A1")
    assert all(len(unit.lessons) == 3 for unit in course.units)


def test_a2_b2_are_complete_mission_led_drafts():
    for level in ("A2", "B1", "B2"):
        course = COURSE_CATALOG[level]
        assert course.contentStatus == "draft"
        assert course.version == "2026.1"
        assert len(course.units) == 8
        assert sum(len(unit.lessons) for unit in course.units) == 16
        assert all(len(unit.lessons) == 2 for unit in course.units)
        assert course.levelOutcomes
        for unit in course.units:
            assert unit.outcomes
            assert unit.skillTags
            assert unit.capstone
            assert unit.capstoneCriteria
            for lesson in unit.lessons:
                assert lesson.objectives
                assert lesson.skillTags
                assert lesson.transferTask
                assert lesson.selfCheck
                assert lesson.vocabulary
                assert lesson.grammar
                assert lesson.dialogue
                assert len(lesson.exercises) >= 3


def test_original_unit_and_lesson_ids_are_preserved():
    expected_units = {
        "A2": {"a2-u1", "a2-u2", "a2-u3", "a2-u4", "a2-u5", "a2-u6"},
        "B1": {"b1-u1", "b1-u2", "b1-u3", "b1-u4", "I am tired."},
        "B2": {"b2-u1", "b2-u2", "b2-u3", "b2-u4", "b2-u5"},
    }
    expected_lessons = {
        "A2": {"a2-u1-l1", "a2-u1-l2", "a2-u2-l1", "a2-u3-l1", "a2-u4-l1", "a2-u5-l1", "a2-u6-l1"},
        "B1": {"b1-u1-l1", "b1-u1-l2", "b1-u2-l1", "b1-u3-l1", "b1-u4-l1", "I am tired."},
        "B2": {"b2-u1-l1", "b2-u1-l2", "b2-u2-l1", "b2-u3-l1", "b2-u4-l1", "b2-u5-l1"},
    }
    for level in expected_units:
        course = COURSE_CATALOG[level]
        assert expected_units[level] <= {unit.id for unit in course.units}
        assert expected_lessons[level] <= {lesson.id for unit in course.units for lesson in unit.lessons}


def test_runtime_catalog_passes_field_aware_integrity_checks():
    assert validate_catalog(COURSE_CATALOG) == {}


def test_course_api_exposes_a1_metadata_and_keeps_drafts_unpublished(client):
    levels = client.get("/api/courses").json()
    assert [course["level"] for course in levels] == ["A1"]
    assert levels[0]["unitCount"] == 8
    assert levels[0]["lessonCount"] == 24

    course = client.get("/api/courses/A1").json()
    assert course["contentStatus"] == "published"
    assert course["levelOutcomes"]
    unit = course["units"][0]
    assert unit["outcomes"] and unit["capstone"] and unit["capstoneCriteria"]
    lesson_id = unit["lessons"][0]["id"]
    lesson = client.get(f"/api/courses/A1/lessons/{lesson_id}").json()
    assert lesson["transferTask"]
    assert lesson["selfCheck"]
    assert lesson["skillTags"]

    assert client.get("/api/courses/A2").status_code == 404
