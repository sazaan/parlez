"""Curated practice resources with licence-aware usage rules.

`link_only` resources must never be mirrored into Parlez. `adapt_with_attribution`
resources may be used in original content with the exact credit line recorded.
Commercial-use limits are explicit: CC BY-NC(-SA) material is link-only for a
commercial product unless separate permission is obtained.
"""

from dataclasses import dataclass, asdict

VERIFIED_ON = "2026-11-24"


@dataclass(frozen=True)
class PracticeResource:
    id: str
    name: str
    level: str
    skill: str
    url: str
    licence: str
    mode: str            # link_only | adapt_with_attribution
    commercial_use: bool
    note: str
    verified_on: str = VERIFIED_ON


RESOURCES = (
    # ---- Official samples: LINK ONLY ----
    PracticeResource(
        "official-tcf-examples", "TCF sample items (exemples d'épreuves)", "A1–C2", "listening, reading, writing, speaking",
        "https://www.france-education-international.fr/test/exemples-epreuves-tcf?langue=fr",
        "© France Éducation international", "link_only", False,
        "Official format familiarisation. Never host or reproduce the items or audio.",
    ),
    PracticeResource(
        "official-tcf-canada", "TCF Canada — candidate handbook & preparation", "A1–C2", "format reference",
        "https://www.france-education-international.fr/en/test/tcf-canada",
        "© France Éducation international", "link_only", False,
        "Authoritative format and score tables; link with attribution.",
    ),
    PracticeResource(
        "official-tef-prep", "TEF Canada — official sample papers & audio", "A1–C1", "listening, reading, writing, speaking",
        "https://www.lefrancaisdesaffaires.fr/en/candidate/test-evaluation-francais/tef-canada/preparation/",
        "© CCI Paris Île-de-France / Le français des affaires", "link_only", False,
        "CCI states test topics are confidential; link only, do not mirror PDFs or audio.",
    ),
    PracticeResource(
        "official-tv5-tcf", "TV5MONDE TCF simulator + 17 booklets with audio", "A1–B2", "listening, reading",
        "https://apprendre.tv5monde.com/fr/tcf",
        "© TV5MONDE (free educational use, no republication right)", "link_only", False,
        "680 questions, free simulator; excellent practice but no right to republish items or audio.",
    ),
    PracticeResource(
        "official-ircc", "IRCC language test & NCLC equivalency tables", "reference", "scores",
        "https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/documents/language-requirements/language-testing.html",
        "Crown copyright — link or verbatim with full disclaimer", "link_only", False,
        "Source of truth for accepted tests and score tables; do not adapt or imply endorsement.",
    ),
    # ---- Open licence: adapt with attribution (commercial-safe: CC BY only) ----
    PracticeResource(
        "open-tex-grammar", "Tex's French Grammar — self-correcting exercises", "A1–B2", "grammar",
        "https://coerll.utexas.edu/coerll/oer/texs-french-grammar/",
        "CC BY 3.0", "adapt_with_attribution", True,
        "Credit: COERLL, University of Texas at Austin. Ideal grammar item bank.",
    ),
    PracticeResource(
        "open-francais-interactif", "Français interactif — videos, grammar exercises, diagnostics", "A1–B1", "all skills",
        "https://www.laits.utexas.edu/fi/",
        "CC BY (3.0/4.0 — check footer before adapting)", "adapt_with_attribution", True,
        "Credit: Blyth, Kelton & Guilloteau, COERLL / UT Austin. Huge open item source.",
    ),
    PracticeResource(
        "open-fi-companion", "Le Français Interactif — Activity Companion (H5P)", "A1–A2", "grammar, vocabulary",
        "https://opentextbc.ca/francaisinteractif/",
        "CC BY", "adapt_with_attribution", True,
        "Credit: Mirabelle Tinio, Langara / BCcampus. Ready-made H5P-shaped items.",
    ),
    PracticeResource(
        "open-intro-french-1", "Introduction to French Level I — 189 H5P activities", "A1–A2", "grammar, vocabulary",
        "https://pressbooks.pub/introductiontofrench1/",
        "CC BY 4.0", "adapt_with_attribution", True,
        "Credit: San Diego City College. Large ready-made item bank.",
    ),
    # ---- Open but restricted for a commercial product: link only here ----
    PracticeResource(
        "open-french-oer-2", "French OER 2 — self-graded grammar/vocab practice", "A1–A2", "grammar, vocabulary",
        "https://human.libretexts.org/Bookshelves/Languages/French/French_OER_2_(Carrasco_Zahedi_and_Parrish)",
        "CC BY-NC 4.0", "link_only", False,
        "Non-commercial licence: link only unless Parlez changes status or gets permission.",
    ),
    PracticeResource(
        "open-wikibooks-french", "Wikibooks French course — lessons and exercises", "A1–B2", "all skills",
        "https://en.wikibooks.org/wiki/French/Lessons",
        "CC BY-SA 4.0", "link_only", False,
        "Share-alike would require Parlez derivatives to be CC BY-SA; link for now.",
    ),
    PracticeResource(
        "open-enhancing-skills", "Enhancing French Skills — video-based activities", "B1–B2", "all skills",
        "https://sites.la.utexas.edu/enhancing-french-skills-new/",
        "CC BY-NC-SA", "link_only", False,
        "Best B1/B2 open set, but NC-SA prevents commercial adaptation.",
    ),
)


def public_resources() -> list[dict]:
    return [asdict(r) for r in RESOURCES]
