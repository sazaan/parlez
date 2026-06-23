// Real exam format configuration for TEF and TCF
// Based on official exam specifications (2024-2025)
// Sources: lefrancaisdesaffaires.fr (TEF), france-education-international.fr (TCF)

export interface ExamSection {
  id: string;
  title: string;
  titleFr: string;
  description: string;
  icon: string;
  questionCount: number;
  durationMinutes: number;
  sections?: string[];
}

export interface ExamFormat {
  type: string;
  name: string;
  fullName: string;
  color: string;
  description: string;
  administeredBy: string;
  usedFor: string;
  sections: ExamSection[];
}

// TEF Canada: Reading 50Q/60min, Listening 60Q/40min, Vocab+Grammar 40Q/30min
export const TEF_FORMAT: ExamFormat = {
  type: 'TEF',
  name: 'TEF',
  fullName: "Test d'Évaluation de Français",
  color: '#1D4ED8',
  description:
    "The TEF is an international reference test that measures French language proficiency. Officially recognized by Immigration, Refugees and Citizenship Canada (IRCC) for Express Entry and by the French government for citizenship applications.",
  administeredBy: 'Paris Île-de-France CCI (CCIP)',
  usedFor: 'Canada immigration (Express Entry, Quebec CSQ), French citizenship, university admission',
  sections: [
    {
      id: 'reading',
      title: 'Reading Comprehension',
      titleFr: 'Compréhension écrite',
      description: '50 questions in 3 sections: A (signs/announcements Q1-15), B (short texts Q16-35), C (longer texts Q36-50). 60 minutes.',
      icon: '📖',
      questionCount: 50,
      durationMinutes: 60,
      sections: ['Section A: Signs & Announcements (Q1-15)', 'Section B: Short Texts (Q16-35)', 'Section C: Longer Texts (Q36-50)'],
    },
    {
      id: 'listening',
      title: 'Listening Comprehension',
      titleFr: 'Compréhension orale',
      description: '60 questions: announcements (Q1-15), conversations (Q16-35), radio/interviews (Q36-60). Audio played once. 40 minutes.',
      icon: '🎧',
      questionCount: 60,
      durationMinutes: 40,
      sections: ['Announcements (Q1-15)', 'Conversations (Q16-35)', 'Radio/Interviews (Q36-60)'],
    },
    {
      id: 'vocabulary_grammar',
      title: 'Vocabulary & Grammar',
      titleFr: 'Lexique et structure',
      description: '40 questions: vocabulary (Q1-20) and grammar (Q21-40). 30 minutes.',
      icon: '✏️',
      questionCount: 40,
      durationMinutes: 30,
      sections: ['Vocabulary (Q1-20)', 'Grammar (Q21-40)'],
    },
  ],
};

// TCF Tout Public (standard): Listening 29Q/25min, Grammar 18Q/15min, Reading 29Q/45min = 76 questions
// Source: france-education-international.fr
export const TCF_FORMAT: ExamFormat = {
  type: 'TCF',
  name: 'TCF',
  fullName: 'Test de Connaissance du Français',
  color: '#B91C1C',
  description:
    "The TCF is the French Ministry of Education's test for non-native speakers. The TCF Tout Public has 3 mandatory sections: Listening (29Q/25min), Language Structures (18Q/15min), and Reading (29Q/45min) = 76 questions total. The TCF Canada variant has 39Q listening + 39Q reading. Officially recognized for French nationality, residency, and Canadian immigration.",
  administeredBy: 'France Éducation International (FEI)',
  usedFor: 'French nationality/citizenship (B1 required), residency card (A2 required), Quebec CSQ, French university admission',
  sections: [
    {
      id: 'listening',
      title: 'Listening Comprehension',
      titleFr: 'Compréhension orale',
      description: '29 questions with PROGRESSIVE difficulty (A1→C2). Audio played once. 25 minutes. Questions get harder as you progress.',
      icon: '🎧',
      questionCount: 29,
      durationMinutes: 25,
      sections: ['Q1-6: A1', 'Q7-12: A2', 'Q13-18: B1', 'Q19-24: B2', 'Q25-29: C1-C2'],
    },
    {
      id: 'language_structures',
      title: 'Language Structures',
      titleFr: 'Maîtrise des structures de la langue',
      description: '18 questions on grammar, conjugation, and vocabulary. 15 minutes. Tests your knowledge of French language mechanics.',
      icon: '✏️',
      questionCount: 18,
      durationMinutes: 15,
      sections: ['Grammar & Conjugation (Q1-12)', 'Vocabulary (Q13-18)'],
    },
    {
      id: 'reading',
      title: 'Reading Comprehension',
      titleFr: 'Compréhension écrite',
      description: '29 questions with PROGRESSIVE difficulty (A1→C2). 45 minutes. Texts get longer and more complex as you progress.',
      icon: '📖',
      questionCount: 29,
      durationMinutes: 45,
      sections: ['Q1-6: A1', 'Q7-12: A2', 'Q13-18: B1', 'Q19-24: B2', 'Q25-29: C1-C2'],
    },
  ],
};

export const EXAM_FORMATS: Record<string, ExamFormat> = {
  TEF: TEF_FORMAT,
  TCF: TCF_FORMAT,
};

export const PRACTICE_SETS_COUNT = 5;
