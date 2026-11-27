"""Editorial enrichment for the attributed curriculum.

Turns the compact unit specs into fuller lessons: generated recall, matching,
dictation and translation items derived from each lesson's own vocabulary,
grammar and dialogue, with hints and explanations. No outside copyrighted
content is copied; source links are attached for attribution.
"""

from dataclasses import replace

from .types import ContentProvenance, Exercise

SOURCES = [
    "https://coerll.utexas.edu/coerll/oer/francais-interactif/",
    "https://coerll.utexas.edu/coerll/oer/texs-french-grammar/",
    "https://enseigner.tv5monde.com/fiches-pedagogiques-fle",
]


def enrich_lesson(lesson) -> None:
    exercises = list(lesson.exercises or [])
    seen = {e.id for e in exercises}

    def add(exercise: Exercise):
        if exercise.id not in seen:
            exercises.append(exercise)
            seen.add(exercise.id)

    for index, word in enumerate((lesson.vocabulary or [])[:4]):
        if word.example and word.fr and word.fr.lower() in word.example.lower():
            prompt = word.example.lower().replace(word.fr.lower(), "_____")
            add(Exercise(
                id=f"{lesson.id}-gen-fb-{index + 1}",
                type="fill_blank",
                prompt=f"Complétez : {prompt}",
                answer=word.fr,
                acceptable=[word.fr.capitalize()],
                explanation=f"{word.fr} = {word.en}",
                hint=word.en,
            ))

    pairs = [{"left": w.fr, "right": w.en} for w in (lesson.vocabulary or [])[:5] if w.fr and w.en]
    if len(pairs) >= 2:
        add(Exercise(
            id=f"{lesson.id}-gen-match",
            type="matching",
            prompt="Reliez le français à l'anglais.",
            pairs=pairs,
            explanation="Révision du vocabulaire de la leçon.",
        ))

    if lesson.dialogue:
        first = lesson.dialogue[0]
        add(Exercise(
            id=f"{lesson.id}-gen-dict",
            type="dictation",
            prompt="Écoutez et écrivez la phrase.",
            audioText=first.fr,
            answer=first.fr,
            explanation=first.en,
            hint=first.en,
        ))

    for index, rule in enumerate((lesson.grammar or [])[:1]):
        if rule.examples:
            example = rule.examples[0]
            add(Exercise(
                id=f"{lesson.id}-gen-tr-{index + 1}",
                type="translate_to_en",
                prompt=f"Traduisez : {example.fr}",
                answer=example.en,
                explanation=rule.title,
            ))

    lesson.exercises = exercises


def enrich_provenance(provenance: ContentProvenance) -> ContentProvenance:
    links = list(dict.fromkeys([*(provenance.source_links or []), *SOURCES]))
    return replace(
        provenance,
        source_links=links,
        attribution=(provenance.attribution or "") +
        " Open components: COERLL Français interactif / Tex's French Grammar (CC BY); "
        "TV5MONDE pedagogical fiches credited at point of use.",
    )


def enrich_course(course) -> None:
    course.provenance = enrich_provenance(course.provenance)
    for unit in course.units:
        unit.provenance = enrich_provenance(unit.provenance)
        for lesson in unit.lessons:
            enrich_lesson(lesson)
            lesson.provenance = enrich_provenance(lesson.provenance)
