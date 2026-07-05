from dataclasses import dataclass, field
from typing import Optional

@dataclass
class TestQuestion:
    id: str
    type: str = 'multiple_choice'
    prompt: str = ''
    promptFr: Optional[str] = None
    options: list[str] = field(default_factory=list)
    answer: int = 0
    explanation: Optional[str] = None
    audioText: Optional[str] = None
    level: str = 'A1'

@dataclass
class TestSectionData:
    id: str
    title: str
    titleFr: str
    description: str
    icon: str
    questionCount: int
    durationMinutes: int
    questions: list[TestQuestion] = field(default_factory=list)

@dataclass
class MockTest:
    type: str
    name: str
    fullName: str
    description: str
    administeredBy: str
    usedFor: str
    sections: list[TestSectionData] = field(default_factory=list)
    color: str = '#333'

@dataclass
class ExamSection:
    id: str
    title: str
    titleFr: str
    description: str
    icon: str
    questionCount: int
    durationMinutes: int

@dataclass
class ExamFormat:
    type: str
    name: str
    fullName: str
    color: str
    description: str
    administeredBy: str
    usedFor: str
    sections: list[ExamSection] = field(default_factory=list)
