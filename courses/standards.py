"""Curriculum standards for Parlez's mission-led v2 content.

This module is an authoring reference, not a certification scheme. Outcome text
here is original Parlez wording inspired by the CEFR Companion Volume (2020);
the Council of Europe does not validate third-party CEFR claims. Link to the
source rather than copying descriptor blocks. See docs/SOURCE_REGISTER.md.
"""

FRAMEWORK = "mission-v2"

# Rules of thumb, not CEFR workload guarantees. Item-level SRS is separate.
REVIEW_INTERVAL_DAYS = (1, 3, 7, 30)
REVIEW_CADENCE_DAYS = 90  # re-verify exam-format facts with the test owners

COMMUNICATIVE_MODES = ("reception", "production", "interaction", "mediation")
SKILLS = ("listening", "speaking", "reading", "writing")

REVIEW_STATES = ("draft", "practice", "reviewed")

# Short, original can-do statements. `ref` is an internal authoring key; it is
# not a Council-of-Europe descriptor code and must not be shown as one.
DESCRIPTORS = {
    "A1.1": "Can say hello, give a name and ask simple personal questions.",
    "A1.2": "Can understand familiar words and short instructions with visual support.",
    "A1.3": "Can write a short postcard or form with simple phrases.",
    "A2.1": "Can handle a short routine exchange such as shopping or booking.",
    "A2.2": "Can describe a familiar place, routine or recent event in simple terms.",
    "A2.3": "Can write a short message of 60–120 words about a familiar topic.",
    "B1.1": "Can understand the main points of clear speech on familiar matters.",
    "B1.2": "Can give reasons for an opinion in a short connected text.",
    "B1.3": "Can take part in a prepared discussion and defend a point of view.",
    "B2.1": "Can understand the main ideas of a complex text on a familiar topic.",
    "B2.2": "Can interact with enough fluency to work with a speaker on a task.",
    "B2.3": "Can write a clear, detailed argument with advantages and disadvantages.",
}

LEVEL_SCOPES = {
    "A1": {
        "can_do": "Handle immediate, familiar situations with simple language.",
        "grammar": "être/avoir, -er verbs, articles, gender/number, adjectives, negation, question forms",
        "themes": "greetings, identity, family, routine, food, shopping, directions, numbers",
        "skills": "listening with visuals, short spoken exchanges, forms and postcards",
    },
    "A2": {
        "can_do": "Understand high-frequency expressions and manage routine tasks.",
        "grammar": "passé composé, futur proche, reflexive verbs, object pronouns, partitives, comparatives",
        "themes": "housing, transport, health, work, clothes, weather, leisure, email",
        "skills": "short messages, information-gathering role-plays, simple narratives",
    },
    "B1": {
        "can_do": "Deal with most travel situations and produce connected text on familiar topics.",
        "grammar": "imparfait, conditionnel présent, core subjonctif, relative pronouns, passive, si clauses",
        "themes": "travel, media, environment, education, employment, Canadian life",
        "skills": "opinion texts, defended viewpoints, authentic video, note-taking",
    },
    "B2": {
        "can_do": "Understand complex texts and interact with fluency on a wider range of topics.",
        "grammar": "subjunctive consolidation, plus-que-parfait, conditionnel passé, nominalisation, register",
        "themes": "current affairs, migration, workplace, technology, francophone culture",
        "skills": "argumentation, sustained debate, press texts, timed exam tasks",
    },
}

# Analytic feedback bands used by capstones and unscored transfer tasks.
RUBRIC_BANDS = (
    "Task fulfilment — did the learner produce the requested artefact?",
    "Comprehensibility — can a sympathetic listener/reader follow it?",
    "Range and accuracy — are the forms appropriate to the level?",
    "Interaction and repair — can the learner ask for clarification and recover?",
)

LESSON_RHYTHM = (
    ("Retrieve", "Spaced recall of earlier language, no notes."),
    ("Understand", "Graded input: gist first, detail second, transcript late."),
    ("Notice", "Find the target form in the input, then one clear rule."),
    ("Practise", "Interleaved exercises with an explanation for every answer."),
    ("Act", "A real-world task with a non-linguistic outcome."),
    ("Return", "CAF feedback, SRS export and a can-do self-check."),
)
