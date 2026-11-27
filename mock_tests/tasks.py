"""Original TEF/TCF writing and speaking practice tasks.

All prompts are original Parlez writing. Task formats, timings and word counts
come from publicly published specifications (see docs/SOURCE_REGISTER.md).
No official or past-paper content is reproduced. Results are practice only.
"""

from dataclasses import dataclass, asdict

VERIFIED_ON = "2026-11-24"
NOTICE = (
    "Original unofficial practice. Not an official TEF/TCF task, not an examiner "
    "score, and not proof of CEFR/NCLC level."
)

RUBRIC = [
    "Task fulfilment — did you do everything the task asked?",
    "Clarity — is your message easy to follow?",
    "Language — are the words and structures appropriate to your level?",
    "Register — is the tone right for the situation?",
    "Development — did you give reasons or examples?",
]


@dataclass(frozen=True)
class ExamTask:
    id: str
    exam: str
    skill: str
    title: str
    instructions: str
    passage: str
    minutes: int
    word_min: int | None
    word_max: int | None
    prep_minutes: int = 0


TASKS = (
    # TEF writing
    ExamTask("TEF-EE-A-1", "TEF", "writing", "News continuation",
             "Continue the news story in at least 80 words, using several paragraphs.",
             "Yesterday afternoon in Bordeaux, a postman found a suitcase near a bus stop. "
             "No address was written on it, but a child's photo was tucked into a pocket. He decided to…",
             25, 80, None),
    ExamTask("TEF-EE-B-1", "TEF", "writing", "Letter to a newspaper",
             "Write a letter giving your opinion. Develop at least three arguments and justify your view.",
             "You read this claim in a newspaper: « Remote work makes cities less lively. » "
             "Write a letter to the editor saying what you think.",
             35, 200, None),
    # TEF speaking
    ExamTask("TEF-EO-A-1", "TEF", "speaking", "Ask for information",
             "You read the advert. Call to ask about ten pieces of information. Be polite and formal.",
             "CLUB SPORTIF LES IRIS — Receptionist wanted at weekends. Saturday and Sunday, 9 h – 13 h. "
             "Driving licence preferred. Pay: 12 €/hour. Contact: 01 42 60 18 33.",
             5, None, None),
    ExamTask("TEF-EO-B-1", "TEF", "speaking", "Persuade a friend",
             "Present the advert to a friend and persuade them to join you with a short spoken answer.",
             "A local association prepares a free meal for people without a home every Sunday at noon. "
             "They need volunteers to prepare and serve the food. Short training is provided.",
             10, None, None),
    # TCF writing
    ExamTask("TCF-EE-1", "TCF", "writing", "Reply to a neighbour",
             "Reply to your neighbour: say you are available, ask two precise questions and reassure them.",
             "« I am away for the weekend. Could you water my plants and collect my post? »",
             20, 60, 120),
    ExamTask("TCF-EE-2", "TCF", "writing", "School website article",
             "Write an article about the beach clean-up: narrate the day, describe the results and recommend it.",
             "Last Saturday your school took part in a beach clean-up organised by the city.",
             20, 120, 150),
    ExamTask("TCF-EE-3", "TCF", "writing", "Compare two viewpoints",
             "Compare the two documents, then give and justify your own opinion.",
             "For: bike-sharing is cheap, clean and frees pavements. Against: stations are often empty "
             "or full, bikes are vandalised, and the money would be better spent on public transport.",
             20, 120, 180),
    # TCF speaking
    ExamTask("TCF-EO-1", "TCF", "speaking", "Guided interview",
             "Answer the examiner about yourself, where you live, what you do, languages and why you learn French.",
             "Bonjour. Pouvez-vous vous présenter ? Où habitez-vous ? Quelles langues parlez-vous ?",
             2, None, None),
    ExamTask("TCF-EO-2", "TCF", "speaking", "Tourist information",
             "Ask your friend about the guided tours: time, meeting point, booking, places and price.",
             "Office de tourisme — Free guided tours of the old quarter, Saturdays at 10 h, "
             "departure in front of the town hall. Duration 1 h 30, maximum 15 people, online booking.",
             4, None, None, 2),
    ExamTask("TCF-EO-3", "TCF", "speaking", "Express a viewpoint",
             "Give a spontaneous, structured opinion. The examiner may ask for clarification.",
             "Do social media have more advantages or disadvantages for young people?",
             5, None, None),
)


def public_tasks(exam: str, skill: str) -> list[dict]:
    return [
        asdict(task) for task in TASKS
        if task.exam == exam.upper() and task.skill == skill.lower()
    ]


def check_response(task_id: str, text: str) -> dict:
    task = next((t for t in TASKS if t.id == task_id), None)
    if not task:
        return {"found": False}
    words = len(str(text or "").split())
    too_short = task.word_min is not None and words < task.word_min
    too_long = task.word_max is not None and words > task.word_max
    return {
        "found": True,
        "wordCount": words,
        "wordMin": task.word_min,
        "wordMax": task.word_max,
        "withinRange": not (too_short or too_long),
        "rubric": list(RUBRIC),
        "notice": NOTICE,
        "verifiedOn": VERIFIED_ON,
    }
