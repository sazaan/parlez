"""Reference implementation of the mission-led v2 curriculum blueprint.

This is an authoring template, NOT a published course: it is deliberately not
registered in COURSE_CATALOG. Authors copy its structure, then add original
content and a real reviewer before publishing. See docs/SOURCE_REGISTER.md.
"""

from .standards import FRAMEWORK
from .types import (
    ContentProvenance,
    Course,
    DialogueLine,
    Exercise,
    GrammarExample,
    GrammarRule,
    Lesson,
    Unit,
    VocabItem,
)


TEMPLATE_PROVENANCE = ContentProvenance(
    author="Parlez curriculum team",
    license="original",
    created="2026-11-23",
    version="1.0",
    review_state="draft",
)


def build_reference_course() -> Course:
    unit = Unit(
        id="a1-mission-greetings",
        title="Introduce yourself in French",
        titleFr="Se présenter en français",
        theme="first contacts",
        description="A newcomer at a French class introduces themselves and asks a neighbour's name.",
        outcomes=[
            "Greet someone appropriately for the time of day.",
            "Give a name and ask for another person's name.",
            "Say where you are from with a simple sentence.",
        ],
        skillTags=["interaction", "speaking", "listening"],
        capstone="Record a 30-second self-introduction: greeting, name, origin and one question for the listener.",
        capstoneCriteria=[
            "Uses an appropriate greeting for the situation.",
            "States name and origin intelligibly.",
            "Asks at least one simple question and waits for a reply.",
        ],
        descriptor_ids=["A1.1", "A1.2"],
        communicative_modes=["interaction", "production", "reception"],
        provenance=TEMPLATE_PROVENANCE,
        lessons=[
            Lesson(
                id="a1-m1-greetings",
                title="Greetings and introductions",
                titleFr="Salutations et présentations",
                description="Choose the right greeting, introduce yourself and ask a name.",
                objectives=[
                    "Distinguish bonjour, bonsoir and salut.",
                    "Use je m'appelle and comment t'appelles-tu ?",
                ],
                vocabulary=[
                    VocabItem("bonjour", "hello / good morning", "/bɔ̃.ʒuʁ/", "Bonjour, je m'appelle Ami.", "Hello, my name is Ami.", "greetings"),
                    VocabItem("bonsoir", "good evening", "/bɔ̃.swaʁ/", "Bonsoir à tous.", "Good evening everyone.", "greetings"),
                    VocabItem("je m'appelle", "my name is", "/ʒə mapɛl/", "Je m'appelle Léa.", "My name is Léa.", "identity"),
                ],
                grammar=[
                    GrammarRule(
                        title="Introducing yourself with s'appeler",
                        explanation="Je m'appelle means 'my name is'. Ask with comment t'appelles-tu ? in casual speech.",
                        examples=[GrammarExample("Je m'appelle Noah.", "My name is Noah.")],
                        tip="Use vous vous appelez ? with someone you do not know well.",
                    ),
                ],
                dialogue=[
                    DialogueLine("A", "Amie", "Bonjour, je m'appelle Amie.", "Hello, my name is Amie."),
                    DialogueLine("B", "Noah", "Bonjour Amie, moi c'est Noah.", "Hello Amie, I'm Noah."),
                ],
                exercises=[
                    Exercise(
                        "a1-m1-e1", "multiple_choice", "It is 8pm. Which greeting fits?",
                        options=["Bonjour", "Bonsoir", "Salut"], answer=1,
                        explanation="Bonsoir is used in the evening.",
                    ),
                    Exercise(
                        "a1-m1-e2", "fill_blank", "Complete: _____ m'appelle Léa.",
                        answer="Je", explanation="Je m'appelle means 'my name is'.",
                    ),
                ],
                activities=[],
                culturalNote="In France, a quick 'bonjour' when entering a shop is a basic courtesy.",
                estimatedMinutes=35,
                skillTags=["interaction", "reception"],
                transferTask="Greet three classmates in French and ask each one's name.",
                selfCheck=["I can choose bonjour or bonsoir.", "I can say my name in French."],
                descriptor_ids=["A1.1"],
                communicative_modes=["interaction", "production"],
                skill_evidence=["A short recorded self-introduction"],
                provenance=TEMPLATE_PROVENANCE,
            ),
            Lesson(
                id="a1-m1-origin",
                title="Where I am from",
                titleFr="Mon origine",
                description="Say your country and ask where someone else is from.",
                objectives=["Use je suis de + country.", "Ask d'où viens-tu ?"],
                vocabulary=[
                    VocabItem("je suis de", "I am from", None, "Je suis de France.", "I am from France.", "identity"),
                    VocabItem("d'où viens-tu ?", "where are you from?", None, "D'où viens-tu ?", "Where are you from?", "questions"),
                ],
                grammar=[
                    GrammarRule(
                        title="Asking about origin",
                        explanation="D'où viens-tu ? is casual; d'où venez-vous ? is polite.",
                        examples=[GrammarExample("Je suis du Népal.", "I am from Nepal.")],
                    ),
                ],
                dialogue=[DialogueLine("A", "Amie", "D'où viens-tu ?", "Where are you from?")],
                exercises=[
                    Exercise("a1-m1-e3", "short_answer", "How do you say 'I am from Nepal' in French?", answer="Je suis du Népal."),
                ],
                estimatedMinutes=30,
                skillTags=["production", "interaction"],
                transferTask="Ask two learners where they are from and note their answers.",
                selfCheck=["I can say where I am from.", "I can ask someone where they are from."],
                descriptor_ids=["A1.3"],
                communicative_modes=["production", "interaction"],
                skill_evidence=["A written two-line introduction"],
                provenance=TEMPLATE_PROVENANCE,
            ),
        ],
    )

    return Course(
        level="A1",
        title="Reference mission unit — first contacts",
        book="Parlez original content",
        description="Template for mission-led authoring. Not published.",
        cefrDescription="A1 can-do inspired outcomes; not a CEFR validation.",
        color="#7C2D3F",
        units=[unit],
        levelOutcomes=["Handle a first-contact exchange with simple language."],
        version="2026.11-template",
        contentStatus="draft",
        framework=FRAMEWORK,
        descriptor_ids=["A1.1", "A1.2", "A1.3"],
        provenance=TEMPLATE_PROVENANCE,
    )


REFERENCE_COURSE = build_reference_course()
