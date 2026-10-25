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


def test_a2_b2_are_expanded_mission_led_drafts():
    for level in ("A2", "B1", "B2"):
        course = COURSE_CATALOG[level]
        assert course.contentStatus == "draft"
        assert course.version == "2026.2"
        assert len(course.units) == 8
        assert sum(len(unit.lessons) for unit in course.units) == 24
        assert all(len(unit.lessons) == 3 for unit in course.units)
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


def test_expansion_adds_four_gradable_practice_items_per_unit():
    from engine.exercises import check_answer

    for level in ("A2", "B1", "B2"):
        course = COURSE_CATALOG[level]
        assert "24 original practice lessons" in course.description
        for unit in course.units:
            lesson = unit.lessons[2]
            assert lesson.id.endswith("-l3")
            assert len(lesson.exercises) == 4
            assert {exercise.type for exercise in lesson.exercises} == {
                "multiple_choice", "fill_blank", "translate_to_fr", "dictation"
            }
            for exercise in lesson.exercises:
                is_correct, _ = check_answer(exercise, exercise.answer)
                assert is_correct, f"{level}.{lesson.id}.{exercise.id} answer key did not grade as correct"


def test_2026_2_corrects_existing_french_and_translation_examples():
    a2_lesson = next(
        lesson for unit in COURSE_CATALOG["A2"].units for lesson in unit.lessons
        if lesson.id == "a2-u7-l1"
    )
    scheduling_item = next(item for item in a2_lesson.vocabulary if item.fr == "convenir")
    assert scheduling_item.example == "Dix heures me conviennent."

    b2_lesson = next(
        lesson for unit in COURSE_CATALOG["B2"].units for lesson in unit.lessons
        if lesson.id == "b2-u4-l1"
    )
    translated_example = next(
        example for rule in b2_lesson.grammar for example in rule.examples
        if example.fr.startswith("La fréquentation a augmenté")
    )
    assert translated_example.en.startswith("Attendance increased")


def test_original_unit_and_lesson_ids_are_preserved():
    expected_units = {
        "A2": {f"a2-u{unit}" for unit in range(1, 9)},
        "B1": {"b1-u1", "b1-u2", "b1-u3", "b1-u4", "I am tired.", "b1-u6", "b1-u7", "b1-u8"},
        "B2": {f"b2-u{unit}" for unit in range(1, 9)},
    }
    expected_original_lessons = {
        "A2": {f"a2-u{unit}-l{lesson}" for unit in range(1, 9) for lesson in (1, 2)},
        "B1": {
            f"b1-u{unit}-l{lesson}"
            for unit in (1, 2, 3, 4, 6, 7, 8)
            for lesson in (1, 2)
        } | {"b1-u5-l2", "I am tired."},
        "B2": {f"b2-u{unit}-l{lesson}" for unit in range(1, 9) for lesson in (1, 2)},
    }
    expected_additions = {
        level: {f"{prefix}-u{unit}-l3" for unit in range(1, 9)}
        for level, prefix in (("A2", "a2"), ("B1", "b1"), ("B2", "b2"))
    }
    for level in expected_units:
        course = COURSE_CATALOG[level]
        lesson_ids = {lesson.id for unit in course.units for lesson in unit.lessons}
        assert expected_units[level] == {unit.id for unit in course.units}
        assert expected_original_lessons[level] | expected_additions[level] == lesson_ids


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
