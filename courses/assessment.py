"""Honest, informal placement check built from original practice items.

This is NOT a CEFR test, an exam score, or an NCLC estimate. It gives a rough
level band from a short grammar/vocabulary sample and explicitly reports that
listening, speaking and writing are not assessed by it.
"""

from dataclasses import dataclass

VERIFIED_ON = "2026-11-24"
NOTICE = (
    "Informal practice estimate only. This is not a CEFR or NCLC certification, "
    "not a TEF/TCF score, and does not assess listening, speaking or writing."
)


@dataclass(frozen=True)
class PlacementItem:
    id: str
    band: str          # A1 | A2 | B1 | B2
    skill: str
    prompt: str
    options: tuple[str, ...]
    answer_index: int
    explanation: str


ITEMS = (
    PlacementItem("P-A1-1", "A1", "grammar", "Je _____ Léa.", ("m'appelle", "appelle", "m'appel"), 0, "Je m'appelle = my name is."),
    PlacementItem("P-A1-2", "A1", "vocabulary", "« Bonsoir » is used…", ("in the morning", "in the evening", "at noon"), 1, "Bonsoir is an evening greeting."),
    PlacementItem("P-A1-3", "A1", "grammar", "Il y a _____ livre sur la table.", ("une", "un", "des"), 1, "livre is masculine singular: un."),
    PlacementItem("P-A2-1", "A2", "grammar", "Hier, je _____ au marché.", ("vais", "suis allé", "irai"), 1, "Hier calls for the past tense."),
    PlacementItem("P-A2-2", "A2", "grammar", "Le train est _____ rapide que le bus.", ("plus", "plus que", "très que"), 0, "Comparative: plus + adj + que."),
    PlacementItem("P-A2-3", "A2", "vocabulary", "« le loyer » means…", ("rent", "receipt", "ticket"), 0, "loyer = rent."),
    PlacementItem("P-B1-1", "B1", "grammar", "Il faut que tu _____ à l'heure.", ("arrives", "arriveses", "arrivais"), 1, "Il faut que takes the subjunctive."),
    PlacementItem("P-B1-2", "B1", "grammar", "Si nous prenons le train, nous _____ moins.", ("dépenserons", "dépensons", "dépenserions"), 0, "si + present → future in the main clause."),
    PlacementItem("P-B1-3", "B1", "vocabulary", "« pourtant » means…", ("however", "therefore", "because"), 0, "pourtant = however."),
    PlacementItem("P-B2-1", "B2", "grammar", "Malgré les critiques, cette politique _____ utile.", ("reste", "restait", "restera"), 0, "Malgré + noun; present tense states the current view."),
    PlacementItem("P-B2-2", "B2", "grammar", "La _____ en œuvre a été critiquée.", ("mise", "mettre", "mets"), 0, "Nominalisation: mise en œuvre."),
    PlacementItem("P-B2-3", "B2", "vocabulary", "« éthique » means…", ("ethics", "ethnic", "aesthetic"), 0, "éthique = ethics."),
)

BANDS = ("A1", "A2", "B1", "B2")


def public_items() -> list[dict]:
    return [
        {
            "id": item.id, "band": item.band, "skill": item.skill,
            "prompt": item.prompt, "options": list(item.options),
        }
        for item in ITEMS
    ]


def evaluate(answers: dict) -> dict:
    """Return an informal level band and per-skill coverage, with honest limits."""
    by_band = {band: {"correct": 0, "total": 0} for band in BANDS}
    by_skill = {}
    for item in ITEMS:
        bucket = by_band[item.band]
        bucket["total"] += 1
        if answers.get(item.id) == item.answer_index:
            bucket["correct"] += 1
        skill = by_skill.setdefault(item.skill, {"correct": 0, "total": 0})
        skill["total"] += 1
        if answers.get(item.id) == item.answer_index:
            skill["correct"] += 1

    reached = "A1"
    for band in BANDS:
        ratio = by_band[band]["correct"] / by_band[band]["total"] if by_band[band]["total"] else 0
        if ratio >= 0.67:
            reached = band

    return {
        "levelEstimate": reached,
        "byBand": by_band,
        "bySkill": by_skill,
        "unassessedSkills": ["listening", "speaking", "writing"],
        "notice": NOTICE,
        "verifiedOn": VERIFIED_ON,
    }
