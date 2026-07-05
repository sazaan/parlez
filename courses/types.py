from dataclasses import dataclass, field
from typing import Optional

@dataclass
class VocabItem:
    fr: str
    en: str
    ipa: Optional[str] = None
    example: Optional[str] = None
    exampleEn: Optional[str] = None
    category: Optional[str] = None

@dataclass
class GrammarExample:
    fr: str
    en: str

@dataclass
class GrammarTable:
    headers: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    caption: Optional[str] = None

@dataclass
class GrammarRule:
    title: str
    explanation: str
    examples: list[GrammarExample] = field(default_factory=list)
    table: Optional[GrammarTable] = None
    tip: Optional[str] = None

@dataclass
class DialogueLine:
    speaker: str  # 'A' or 'B'
    name: Optional[str] = None
    fr: str = ""
    en: str = ""

@dataclass
class Exercise:
    id: str
    type: str  # multiple_choice, fill_blank, translate_to_fr, etc.
    prompt: str
    promptFr: Optional[str] = None
    options: Optional[list[str]] = None
    answer: object = None
    acceptable: Optional[list[str]] = None
    explanation: Optional[str] = None
    hint: Optional[str] = None
    pairs: Optional[list[dict]] = None
    wordBank: Optional[list[str]] = None
    words: Optional[list[str]] = None
    audioText: Optional[str] = None

@dataclass
class ConjugationVerb:
    infinitive: str
    translation: str
    tense: str
    conjugations: list[dict] = field(default_factory=list)
    sentenceRule: str = ""
    sentenceExamples: list[GrammarExample] = field(default_factory=list)

@dataclass
class ConjugationData:
    verbs: list[ConjugationVerb] = field(default_factory=list)
    practice: list[Exercise] = field(default_factory=list)

@dataclass
class Lesson:
    id: str
    title: str
    titleFr: str
    description: str
    objectives: list[str] = field(default_factory=list)
    vocabulary: list[VocabItem] = field(default_factory=list)
    grammar: list[GrammarRule] = field(default_factory=list)
    conjugation: Optional[ConjugationData] = None
    dialogue: list[DialogueLine] = field(default_factory=list)
    exercises: list[Exercise] = field(default_factory=list)
    activities: list[Exercise] = field(default_factory=list)
    culturalNote: Optional[str] = None
    estimatedMinutes: int = 30

@dataclass
class Unit:
    id: str
    title: str
    titleFr: str
    theme: str
    description: str
    lessons: list[Lesson] = field(default_factory=list)

@dataclass
class Course:
    level: str  # A1, A2, B1, B2
    title: str
    book: str
    description: str
    cefrDescription: str
    color: str
    units: list[Unit] = field(default_factory=list)

@dataclass
class ScenarioTopic:
    id: str
    label: str
    labelFr: str
    description: str
    icon: str
