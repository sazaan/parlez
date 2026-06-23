// Client-side Zustand store for Parlez app state
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { CourseLevel } from './courses/types';

export type AppView =
  | { kind: 'dashboard' }
  | { kind: 'courses' }
  | { kind: 'lesson'; level: CourseLevel; unitId: string; lessonId: string }
  | { kind: 'conversation' }
  | { kind: 'translate' }
  | { kind: 'mock-tests' }
  | { kind: 'test-runner'; testType: 'TEF' | 'TCF'; section: string }
  | { kind: 'progress' };

interface CompletedLesson {
  lessonId: string;
  level: CourseLevel;
  unitId: string;
  score: number; // 0-100
  completedAt: string;
}

interface TestResultRecord {
  id: string;
  testType: 'TEF' | 'TCF';
  section: string;
  score: number;
  total: number;
  correctCount: number;
  totalQuestions: number;
  durationSec: number;
  takenAt: string;
}

interface AppState {
  // Navigation
  view: AppView;
  setView: (view: AppView) => void;

  // User settings (these are per-browser, not per-account; account data is server-side)
  voiceRate: number;
  setVoiceRate: (rate: number) => void;

  // Local progress (also mirrored to server via /api/progress)
  xp: number;
  completedLessons: CompletedLesson[];
  testResults: TestResultRecord[];
  streakDays: number;
  lastActiveDate: string;

  // Hydration from server
  hydratedFromServer: boolean;
  hydrateFromServer: (data: { completedLessons: CompletedLesson[]; testResults: TestResultRecord[] }) => void;

  markLessonComplete: (lesson: CompletedLesson) => void;
  recordTestResult: (result: TestResultRecord) => void;

  // Helpers
  isLessonComplete: (lessonId: string) => boolean;
  getLessonScore: (lessonId: string) => number | null;

  resetProgress: () => void;
}

const today = () => new Date().toISOString().split('T')[0];

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      view: { kind: 'dashboard' },
      setView: (view) => set({ view }),

      voiceRate: 0.95,
      setVoiceRate: (rate) => set({ voiceRate: rate }),

      xp: 0,
      completedLessons: [],
      testResults: [],
      streakDays: 1,
      lastActiveDate: today(),
      hydratedFromServer: false,

      hydrateFromServer: (data) => {
        set({
          completedLessons: data.completedLessons,
          testResults: data.testResults,
          // Recompute XP locally from server data
          xp: data.completedLessons.reduce((sum, l) => sum + 50 + Math.floor(l.score / 5), 0)
                + data.testResults.reduce((sum, t) => sum + Math.floor((t.correctCount / Math.max(t.totalQuestions, 1)) * 30), 0),
          hydratedFromServer: true,
        });
      },

      markLessonComplete: (lesson) => {
        const state = get();
        const existing = state.completedLessons.find((l) => l.lessonId === lesson.lessonId);
        const updated = existing
          ? state.completedLessons.map((l) => (l.lessonId === lesson.lessonId ? { ...l, ...lesson, score: Math.max(l.score, lesson.score) } : l))
          : [...state.completedLessons, lesson];

        const todayStr = today();
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        const yesterdayStr = yesterday.toISOString().split('T')[0];
        let newStreak = state.streakDays;
        if (state.lastActiveDate !== todayStr) {
          if (state.lastActiveDate === yesterdayStr) {
            newStreak = state.streakDays + 1;
          } else {
            newStreak = 1;
          }
        }

        set({
          completedLessons: updated,
          xp: state.xp + (existing ? Math.floor(lesson.score / 5) : 50 + Math.floor(lesson.score / 5)),
          streakDays: newStreak,
          lastActiveDate: todayStr,
        });
      },

      recordTestResult: (result) => {
        const state = get();
        set({
          testResults: [result, ...state.testResults],
          xp: state.xp + Math.floor((result.correctCount / Math.max(result.totalQuestions, 1)) * 30),
        });
      },

      isLessonComplete: (lessonId) => get().completedLessons.some((l) => l.lessonId === lessonId),
      getLessonScore: (lessonId) => {
        const l = get().completedLessons.find((x) => x.lessonId === lessonId);
        return l ? l.score : null;
      },
      resetProgress: () =>
        set({
          xp: 0,
          completedLessons: [],
          testResults: [],
          streakDays: 1,
          lastActiveDate: today(),
        }),
    }),
    {
      name: 'parlez-storage-v2',
      partialize: (state) => ({
        voiceRate: state.voiceRate,
        xp: state.xp,
        completedLessons: state.completedLessons,
        testResults: state.testResults,
        streakDays: state.streakDays,
        lastActiveDate: state.lastActiveDate,
      }),
    }
  )
);
