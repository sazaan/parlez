// Course curriculum types for Parlez French learning app

export type CourseLevel = 'A1' | 'A2' | 'B1' | 'B2';

export interface VocabItem {
  fr: string;
  en: string;
  ipa?: string;
  example?: string;
  exampleEn?: string;
  category?: string;
}

export interface GrammarExample {
  fr: string;
  en: string;
}

export interface GrammarTable {
  caption?: string;
  headers: string[];
  rows: string[][];
}

export interface GrammarRule {
  title: string;
  explanation: string;
  examples: GrammarExample[];
  table?: GrammarTable;
  tip?: string;
}

export interface DialogueLine {
  speaker: 'A' | 'B' | 'N';
  name?: string;
  fr: string;
  en: string;
}

// Activity types — extended for comprehensive workbook sections
export type ExerciseType =
  | 'multiple_choice'        // pick the correct option
  | 'fill_blank'             // type the missing word
  | 'translate_to_fr'        // English → French
  | 'translate_to_en'        // French → English
  | 'true_false'             // binary choice
  | 'reorder'                // reorder words to form a sentence
  | 'matching'               // match French ↔ English pairs
  | 'word_bank'              // pick words from a bank to fill blanks
  | 'dictation'              // listen and type what you hear
  | 'conjugation'            // type the conjugated verb form
  | 'article_choice'         // pick le/la/les, un/une/des, du/de la/des
  | 'pronoun_replace'        // replace a noun with the correct pronoun
  | 'transformation'         // transform a sentence (negate, question, etc.)
  | 'short_answer';          // open-ended (auto-graded loosely)

export interface Exercise {
  id: string;
  type: ExerciseType;
  prompt: string;
  promptFr?: string;
  options?: string[];
  answer: string | number | number[] | Record<string, string>; // depends on type
  acceptable?: string[];
  explanation?: string;
  hint?: string;
  // For matching exercises: list of {left, right} pairs and we shuffle
  pairs?: { left: string; right: string }[];
  // For word_bank exercises: the available words
  wordBank?: string[];
  // For reorder: the words in correct order (we shuffle display)
  words?: string[];
  // For dictation: the text to be spoken
  audioText?: string;
}

export interface ConjugationVerb {
  infinitive: string;          // e.g. "être"
  translation: string;         // e.g. "to be"
  tense: string;               // e.g. "Présent"
  conjugations: { pronoun: string; form: string; }[];
  sentenceRule: string;        // rule for making sentences with this verb
  sentenceExamples: GrammarExample[];
}

export interface ConjugationPractice {
  id: string;
  type: ExerciseType;
  prompt: string;
  promptFr?: string;
  options?: string[];
  answer: string | number;
  acceptable?: string[];
  explanation?: string;
}

export interface ConjugationData {
  verbs: ConjugationVerb[];
  practice: ConjugationPractice[];
}

export interface Lesson {
  id: string;
  title: string;
  titleFr: string;
  description: string;
  objectives: string[];
  vocabulary: VocabItem[];
  grammar: GrammarRule[];
  conjugation?: ConjugationData;
  dialogue: DialogueLine[];
  exercises: Exercise[];
  // Workbook activity section — additional practice, separate from core exercises
  activities?: Exercise[];
  culturalNote?: string;
  estimatedMinutes: number;
}

export interface Unit {
  id: string;
  title: string;
  titleFr: string;
  theme: string;
  description: string;
  lessons: Lesson[];
}

export interface Course {
  level: CourseLevel;
  title: string;
  book: string;
  description: string;
  cefrDescription: string;
  color: string;
  units: Unit[];
}

export interface ScenarioTopic {
  id: string;
  label: string;
  labelFr: string;
  description: string;
  icon: string;
}
