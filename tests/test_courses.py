"""Tests for course data structure and A1 restructure completeness."""

from courses import get_course


def test_a1_course_exists():
    course = get_course('A1')
    assert course is not None
    assert course.level == 'A1'


def test_a1_has_eight_modules():
    course = get_course('A1')
    assert len(course.units) == 8


def test_a1_module_ids_are_unique():
    course = get_course('A1')
    ids = [u.id for u in course.units]
    assert len(ids) == len(set(ids))


def test_a1_modules_have_original_titles():
    course = get_course('A1')
    titles = [u.title for u in course.units]
    assert 'Module 1 — Premiers contacts' in titles
    assert 'Module 2 — Mon identité' in titles
    assert 'Module 3 — Ma famille et mes proches' in titles
    assert 'Module 4 — Ma journée' in titles
    assert 'Module 5 — En ville' in titles
    assert 'Module 6 — Manger et boire' in titles
    assert 'Module 7 — Chez moi' in titles
    assert 'Module 8 — Projets et loisirs' in titles


def test_a1_lessons_have_required_fields():
    course = get_course('A1')
    for unit in course.units:
        assert len(unit.lessons) >= 1
        for lesson in unit.lessons:
            assert lesson.id
            assert lesson.title
            assert lesson.titleFr
            assert lesson.vocabulary
            assert lesson.grammar
            assert lesson.dialogue
            assert lesson.exercises
            assert lesson.culturalNote


def test_a1_each_module_has_three_lessons():
    course = get_course('A1')
    assert all(len(unit.lessons) == 3 for unit in course.units)
