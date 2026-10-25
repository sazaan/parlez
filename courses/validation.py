"""Field-aware validation for course content before it is publicly served."""

from __future__ import annotations

import re
from dataclasses import fields, is_dataclass

from .types import Course, Exercise


LEGACY_UNIT_IDS = {"I am tired."}
AUTO_GRADED_TYPES = {
    "multiple_choice",
    "true_false",
    "article_choice",
    "fill_blank",
    "translate_to_fr",
    "translate_to_en",
    "conjugation",
    "word_bank",
    "reorder",
    "dictation",
    "short_answer",
    "transformation",
    "pronoun_replace",
}


def _iter_strings(value, path=""):
    if is_dataclass(value):
        for item in fields(value):
            child_path = f"{path}.{item.name}" if path else item.name
            yield from _iter_strings(getattr(value, item.name), child_path)
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            yield from _iter_strings(item, f"{path}[{index}]")
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _iter_strings(item, f"{path}[{key!r}]")
    elif isinstance(value, str):
        yield path, value


def _exercises(lesson):
    yield from lesson.exercises
    yield from lesson.activities
    if lesson.conjugation:
        yield from lesson.conjugation.practice


def validate_course(course: Course) -> list[str]:
    """Return content-integrity errors without changing learner-facing data."""
    issues: list[str] = []
    if not course.level.strip() or not course.title.strip():
        issues.append("course: missing level or title")
    if course.contentStatus not in {"draft", "published", "published_unattested"}:
        issues.append(f"course: invalid contentStatus {course.contentStatus!r}")
    if not course.units:
        issues.append("course: no units")

    for path, value in _iter_strings(course):
        if value.endswith("\\"):
            issues.append(f"{course.level}.{path}: text ends in a literal backslash")

    seen_units: set[str] = set()
    seen_lessons: set[str] = set()
    seen_exercises: set[str] = set()
    safe_id = re.compile(r"^[a-z0-9][a-z0-9._-]*$")

    for unit_index, unit in enumerate(course.units):
        unit_path = f"{course.level}.units[{unit_index}]"
        if not unit.id:
            issues.append(f"{unit_path}: missing id")
        elif unit.id in seen_units:
            issues.append(f"{unit_path}: duplicate unit id {unit.id!r}")
        elif not safe_id.fullmatch(unit.id) and unit.id not in LEGACY_UNIT_IDS:
            issues.append(f"{unit_path}: malformed unit id {unit.id!r}")
        seen_units.add(unit.id)
        if not unit.title.strip() or not unit.titleFr.strip() or not unit.description.strip():
            issues.append(f"{unit_path}: missing title or mission description")
        if not unit.outcomes:
            issues.append(f"{unit_path}: missing unit outcomes")
        if not unit.capstone or not unit.capstoneCriteria:
            issues.append(f"{unit_path}: missing capstone or success criteria")
        if not unit.lessons:
            issues.append(f"{unit_path}: no lessons")

        for lesson_index, lesson in enumerate(unit.lessons):
            lesson_path = f"{unit_path}.lessons[{lesson_index}]"
            if not lesson.id:
                issues.append(f"{lesson_path}: missing id")
            elif lesson.id in seen_lessons:
                issues.append(f"{lesson_path}: duplicate lesson id {lesson.id!r}")
            elif not safe_id.fullmatch(lesson.id) and lesson.id not in LEGACY_UNIT_IDS:
                issues.append(f"{lesson_path}: malformed lesson id {lesson.id!r}")
            seen_lessons.add(lesson.id)
            if not lesson.title.strip() or not lesson.titleFr.strip() or not lesson.description.strip():
                issues.append(f"{lesson_path}: missing title or description")
            if not lesson.objectives or any(not text.strip() for text in lesson.objectives):
                issues.append(f"{lesson_path}: missing or empty objectives")
            if not lesson.skillTags:
                issues.append(f"{lesson_path}: missing skill tags")
            if not lesson.transferTask or not lesson.selfCheck:
                issues.append(f"{lesson_path}: missing unscored transfer task or self-check")

            for vocab_index, item in enumerate(lesson.vocabulary):
                if not item.fr.strip() or not item.en.strip():
                    issues.append(f"{lesson_path}.vocabulary[{vocab_index}]: missing French or English")
            for grammar_index, rule in enumerate(lesson.grammar):
                if not rule.title.strip() or not rule.explanation.strip():
                    issues.append(f"{lesson_path}.grammar[{grammar_index}]: missing title or explanation")
            for line_index, line in enumerate(lesson.dialogue):
                if not line.fr.strip() or not line.en.strip():
                    issues.append(f"{lesson_path}.dialogue[{line_index}]: missing French or English line")

            for exercise in _exercises(lesson):
                if not isinstance(exercise, Exercise):
                    issues.append(f"{lesson_path}: exercise has an unsupported data type")
                    continue
                if not exercise.id:
                    issues.append(f"{lesson_path}: exercise missing id")
                elif exercise.id in seen_exercises:
                    issues.append(f"{lesson_path}: duplicate exercise id {exercise.id!r}")
                seen_exercises.add(exercise.id)
                if not exercise.prompt.strip():
                    issues.append(f"{lesson_path}.{exercise.id}: missing prompt")
                if exercise.type == "multiple_choice":
                    if not exercise.options or len(exercise.options) < 2:
                        issues.append(f"{lesson_path}.{exercise.id}: multiple choice needs at least two options")
                    if not isinstance(exercise.answer, int) or not exercise.options or not 0 <= exercise.answer < len(exercise.options):
                        issues.append(f"{lesson_path}.{exercise.id}: invalid multiple-choice answer index")
                elif exercise.type == "true_false":
                    if not isinstance(exercise.answer, int) or exercise.answer not in (0, 1):
                        issues.append(f"{lesson_path}.{exercise.id}: invalid true/false answer index")
                elif exercise.type in AUTO_GRADED_TYPES and exercise.type not in {"multiple_choice", "true_false"}:
                    if exercise.answer is None or not str(exercise.answer).strip():
                        issues.append(f"{lesson_path}.{exercise.id}: missing answer for {exercise.type}")

    return issues


def validate_catalog(catalog: dict[str, Course]) -> dict[str, list[str]]:
    """Validate all registered courses and return only levels with issues."""
    return {
        level: issues
        for level, course in catalog.items()
        if (issues := validate_course(course))
    }
