// Types for French proficiency mock tests (TEF & TCF)

export type TestType = 'TEF' | 'TCF';
export type TestSection = 'reading' | 'listening' | 'vocabulary_grammar' | 'speaking' | 'writing';

export interface TestQuestion {
  id: string;
  type: 'multiple_choice';
  prompt: string;
  promptFr?: string;
  options: string[];
  answer: number; // index of correct option
  explanation?: string;
  audioText?: string; // text for TTS playback (for listening section)
  level: 'A1' | 'A2' | 'B1' | 'B2' | 'C1' | 'C2';
}

export interface TestSectionData {
  id: TestSection;
  title: string;
  titleFr: string;
  description: string;
  icon: string;
  questionCount: number;
  durationMinutes: number;
  questions: TestQuestion[];
}

export interface MockTest {
  type: TestType;
  name: string;
  fullName: string;
  description: string;
  administeredBy: string;
  usedFor: string;
  sections: TestSectionData[];
  color: string;
}

export interface TestResult {
  testType: TestType;
  section: TestSection;
  score: number;
  total: number;
  correctCount: number;
  totalQuestions: number;
  durationSec: number;
  takenAt: string;
  level?: string;
}
