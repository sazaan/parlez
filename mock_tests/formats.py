"""Versioned reference data for TEF Canada and TCF Canada formats.

All practice in Parlez is original and unofficial. Format facts are verified
against IRCC and the test owners; `verified_on` must be refreshed every 90 days
or after an owner announcement (see courses/standards.py REVIEW_CADENCE_DAYS).
"""

from dataclasses import dataclass, field
from typing import Optional


VERIFIED_ON = "2026-11-23"

SOURCE_URLS = {
    "ircc": "https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/documents/language-requirements/language-testing.html",
    "tcf": "https://www.france-education-international.fr/test/tcf-canada",
    "tef": "https://www.lefrancaisdesaffaires.fr/en/candidate/test-evaluation-francais/tef-canada/presentation/",
    "tef_attestation": "https://www.lefrancaisdesaffaires.fr/candidat/test-evaluation-francais/tef-canada/attestation",
}


@dataclass(frozen=True)
class ScoreBand:
    nclc: int
    listening: str
    reading: str
    speaking: str
    writing: str


@dataclass(frozen=True)
class ExamSectionSpec:
    id: str
    name: str
    nameFr: str
    minutes: int
    question_count: Optional[int] = None
    tasks: tuple[str, ...] = field(default_factory=tuple)
    note: str = ""


@dataclass(frozen=True)
class ExamFormatSpec:
    type: str
    name: str
    administered_by: str
    total_minutes: int
    sections: tuple[ExamSectionSpec, ...]
    score_bands: tuple[ScoreBand, ...]
    score_scale_note: str
    warnings: tuple[str, ...]
    source_urls: tuple[str, ...]
    verified_on: str = VERIFIED_ON
    format_version: str = "2026.11"


# IRCC table: TCF Canada scores -> NCLC
_TCF_BANDS = (
    ScoreBand(10, "549–699", "549–699", "16–20", "16–20"),
    ScoreBand(9, "523–548", "524–548", "14–15", "14–15"),
    ScoreBand(8, "503–522", "499–523", "12–13", "12–13"),
    ScoreBand(7, "458–502", "453–498", "10–11", "10–11"),
    ScoreBand(6, "398–457", "406–452", "7–9", "7–9"),
    ScoreBand(5, "369–397", "375–405", "6", "6"),
    ScoreBand(4, "331–368", "342–374", "4–5", "4–5"),
)

# IRCC "Équivalence ancien score" table: TEF Canada -> NCLC (Express Entry)
_TEF_EXPRESS_ENTRY_BANDS = (
    ScoreBand(9, "298+", "248+", "371+", "371+"),
    ScoreBand(8, "280–297", "233–247", "349–370", "349–370"),
    ScoreBand(7, "249–279", "207–232", "310–348", "310–348"),
    ScoreBand(6, "217–248", "181–206", "271–309", "271–309"),
    ScoreBand(5, "181–216", "151–180", "226–270", "226–270"),
    ScoreBand(4, "145–180", "121–150", "181–225", "181–225"),
)

# Test owner's /699 correspondence table (non-Express-Entry programs).
_TEF_699_BANDS = (
    ScoreBand(12, "615–699", "615–699", "642–699", "619–699"),
    ScoreBand(11, "573–614", "573–614", "592–641", "577–618"),
    ScoreBand(10, "546–572", "546–572", "556–591", "558–576"),
    ScoreBand(9, "503–545", "503–545", "518–555", "512–557"),
    ScoreBand(8, "462–502", "462–502", "494–517", "472–511"),
    ScoreBand(7, "434–461", "434–461", "456–493", "428–471"),
    ScoreBand(6, "393–433", "393–433", "422–455", "379–427"),
    ScoreBand(5, "352–392", "352–392", "387–421", "330–378"),
    ScoreBand(4, "306–351", "306–351", "328–386", "268–329"),
)

EXAM_FORMATS = {
    "tcf": ExamFormatSpec(
        type="tcf",
        name="TCF Canada",
        administered_by="France Éducation international",
        total_minutes=167,
        sections=(
            ExamSectionSpec("listening", "Listening comprehension", "Compréhension orale", 35, 39,
                            note="Recordings are played once; difficulty progresses A1→C2."),
            ExamSectionSpec("reading", "Reading comprehension", "Compréhension écrite", 60, 39),
            ExamSectionSpec("writing", "Written expression", "Expression écrite", 60, None,
                            tasks=("60–120 word message", "120–150 word article/report",
                                   "120–180 word argument comparing two viewpoints")),
            ExamSectionSpec("speaking", "Oral expression", "Expression orale", 12, None,
                            tasks=("guided interview", "role-play with 2 min preparation", "opinion defence")),
        ),
        score_bands=_TCF_BANDS,
        score_scale_note="Listening/reading 100–699; writing/speaking /20. Wrong or blank answers score 0.",
        warnings=(
            "Official samples are linked, never reproduced. Parlez practice is original and unofficial.",
            "A TCF score is valid for two years and must be valid on both profile and PR submission dates.",
        ),
        source_urls=(SOURCE_URLS["ircc"], SOURCE_URLS["tcf"]),
    ),
    "tef": ExamFormatSpec(
        type="tef",
        name="TEF Canada",
        administered_by="Le français des affaires / CCI Paris Île-de-France",
        total_minutes=175,
        sections=(
            ExamSectionSpec("reading", "Reading comprehension", "Compréhension écrite", 60, 40),
            ExamSectionSpec("listening", "Listening comprehension", "Compréhension orale", 40, 40,
                            note="Audio is played once; answers are forward-only."),
            ExamSectionSpec("writing", "Written expression", "Expression écrite", 60, None,
                            tasks=("Section A: continue a news article, ≥80 words (25 min)",
                                   "Section B: express and justify a viewpoint, ≥200 words (35 min)")),
            ExamSectionSpec("speaking", "Oral expression", "Expression orale", 15, None,
                            tasks=("obtain information, 5 min", "argue to convince, 10 min")),
        ),
        score_bands=_TEF_EXPRESS_ENTRY_BANDS,
        score_scale_note=(
            "Express Entry uses the 'Équivalence ancien score' column (speaking /450, listening /360, "
            "reading /300, writing /450). The /699 column is for other programs only."
        ),
        warnings=(
            "IRCC warns that entering scores from the wrong TEF column may cause an application to be refused.",
            "Parlez practice is original and unofficial; it never produces an attestation or score prediction.",
        ),
        source_urls=(SOURCE_URLS["ircc"], SOURCE_URLS["tef"], SOURCE_URLS["tef_attestation"]),
    ),
}


def public_format(spec: ExamFormatSpec) -> dict:
    """JSON-safe view including the honesty labels shown to learners."""
    return {
        "type": spec.type,
        "name": spec.name,
        "administeredBy": spec.administered_by,
        "totalMinutes": spec.total_minutes,
        "sections": [
            {
                "id": s.id, "name": s.name, "nameFr": s.nameFr, "minutes": s.minutes,
                "questionCount": s.question_count, "tasks": list(s.tasks), "note": s.note,
            }
            for s in spec.sections
        ],
        "scoreBands": [
            {
                "nclc": b.nclc, "listening": b.listening, "reading": b.reading,
                "speaking": b.speaking, "writing": b.writing,
            }
            for b in spec.score_bands
        ],
        "scoreScaleNote": spec.score_scale_note,
        "warnings": list(spec.warnings),
        "sourceUrls": list(spec.source_urls),
        "verifiedOn": spec.verified_on,
        "formatVersion": spec.format_version,
        "practiceNotice": "Original, unofficial practice. Not an official score or proof of readiness.",
    }
