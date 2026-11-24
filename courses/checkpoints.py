"""Server-graded lesson checkpoints.

A checkpoint re-tests the lesson's vocabulary, grammar and exercises. Question
payloads sent to the browser never contain the answer key; grading happens on
the server against the lesson data. Passing a checkpoint unlocks the next
lesson (and, at the end of a level, the next level).
"""

from __future__ import annotations

from .types import Course, Lesson, Unit

PASS_PERCENT = 70
NOTICE = "Practice checkpoint — not a CEFR/NCLC test, exam score, or certification."


def _options(correct: str, distractors: list[str]) -> list[str]:
    picked = []
    for item in distractors:
        if item and item != correct and item not in picked and len(picked) < 3:
            picked.append(item)
    while len(picked) < 3:
        picked.append("—")
    result = [correct] + picked[:3]
    return result[:4]


def build_checkpoint(lesson: Lesson, unit: Unit, course: Course) -> list[dict]:
    """Client-safe questions with no answers."""
    questions = []
    en_words = [v.en for v in lesson.vocabulary if v.en.strip()]
    for index, item in enumerate(lesson.vocabulary[:6]):
        options = _options(item.en, en_words[index + 1:] + en_words[:index])
        questions.append({
            "id": f"cp-{lesson.id}-v{index + 1}",
            "kind": "vocabulary",
            "prompt": f"Que signifie « {item.fr} » ?",
            "options": options,
        })

    for index, rule in enumerate(lesson.grammar[:2]):
        examples = [e.fr for e in rule.examples if e.fr.strip()]
        if not examples:
            continue
        others = [e.fr for other in course.units if other.id != unit.id
                  for l in other.lessons for g in l.grammar for e in g.examples if e.fr.strip()]
        questions.append({
            "id": f"cp-{lesson.id}-g{index + 1}",
            "kind": "grammar",
            "prompt": f"Choisissez un exemple correct pour : {rule.title}",
            "options": _options(examples[0], others),
        })

    for index, exercise in enumerate(lesson.exercises[:4]):
        if exercise.type == "multiple_choice" and exercise.options and isinstance(exercise.answer, int):
            questions.append({
                "id": f"cp-{lesson.id}-e{exercise.id}",
                "kind": "exercise",
                "prompt": exercise.prompt,
                "options": list(exercise.options),
            })
    return questions


def _answers(course: Course, unit: Unit, lesson: Lesson) -> dict[str, tuple[int, str]]:
    key: dict[str, tuple[int, str]] = {}
    en_words = [v.en for v in lesson.vocabulary if v.en.strip()]
    for index, item in enumerate(lesson.vocabulary[:6]):
        options = _options(item.en, en_words[index + 1:] + en_words[:index])
        key[f"cp-{lesson.id}-v{index + 1}"] = (options.index(item.en), item.en)
    for index, rule in enumerate(lesson.grammar[:2]):
        examples = [e.fr for e in rule.examples if e.fr.strip()]
        if not examples:
            continue
        others = [e.fr for other in course.units if other.id != unit.id
                  for l in other.lessons for g in l.grammar for e in g.examples if e.fr.strip()]
        options = _options(examples[0], others)
        key[f"cp-{lesson.id}-g{index + 1}"] = (options.index(examples[0]), examples[0])
    for exercise in lesson.exercises[:4]:
        if exercise.type == "multiple_choice" and exercise.options and isinstance(exercise.answer, int):
            key[f"cp-{lesson.id}-e{exercise.id}"] = (
                exercise.answer, str(exercise.options[exercise.answer]),
            )
    return key


def grade_checkpoint(lesson: Lesson, unit: Unit, course: Course, answers: dict) -> dict:
    key = _answers(course, unit, lesson)
    review = []
    correct = 0
    for question_id, (answer_index, answer_text) in key.items():
        given = answers.get(question_id)
        ok = isinstance(given, int) and given == answer_index
        correct += 1 if ok else 0
        review.append({
            "id": question_id, "correct": ok,
            "correctAnswer": answer_text if not ok else None,
        })
    total = len(key)
    percent = round((correct / total) * 100) if total else 0
    return {
        "score": correct,
        "total": total,
        "percent": percent,
        "passed": total > 0 and percent >= PASS_PERCENT,
        "passPercent": PASS_PERCENT,
        "review": review,
        "notice": NOTICE,
    }
