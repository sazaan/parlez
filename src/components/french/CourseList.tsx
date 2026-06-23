'use client';

import { useState } from 'react';
import { ChevronDown, ChevronRight, Clock, CheckCircle2, Circle, BookOpen } from 'lucide-react';
import { courses } from '@/lib/courses';
import { useAppStore } from '@/lib/store';
import type { CourseLevel } from '@/lib/courses/types';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

export function CourseList() {
  const [expanded, setExpanded] = useState<Record<CourseLevel, boolean>>({
    A1: true,
    A2: false,
    B1: false,
    B2: false,
  });
  const setView = useAppStore((s) => s.setView);
  const isLessonComplete = useAppStore((s) => s.isLessonComplete);
  const getLessonScore = useAppStore((s) => s.getLessonScore);

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Curriculum</p>
        <h1 className="font-serif text-3xl sm:text-4xl font-semibold">Courses</h1>
        <p className="text-foreground/70 max-w-2xl">
          Four CEFR levels — from your first «&nbsp;bonjour&nbsp;» to debating literature in the subjunctive. Each lesson includes vocabulary with audio, grammar rules with examples, dialogues, core exercises, and a full activity workbook.
        </p>
      </header>

      <div className="space-y-4">
        {courses.map((course) => {
          const isOpen = expanded[course.level];
          const totalLessons = course.units.reduce((s, u) => s + u.lessons.length, 0);
          return (
            <div key={course.level} className="rounded-2xl border border-border bg-card overflow-hidden">
              {/* Course header */}
              <button
                onClick={() => setExpanded((p) => ({ ...p, [course.level]: !p[course.level] }))}
                className="w-full p-5 sm:p-6 flex items-start gap-4 hover:bg-secondary/50 transition text-left"
              >
                <div
                  className="flex-shrink-0 h-14 w-14 sm:h-16 sm:w-16 rounded-2xl flex items-center justify-center font-serif text-2xl sm:text-3xl font-bold text-white shadow"
                  style={{ background: course.color }}
                >
                  {course.level}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline gap-2 flex-wrap">
                    <h2 className="font-serif text-xl sm:text-2xl font-semibold">{course.title}</h2>
                    <span className="text-xs text-muted-foreground uppercase tracking-wider">{course.book}</span>
                  </div>
                  <p className="mt-1 text-sm text-foreground/70 line-clamp-2">{course.description}</p>
                  <div className="mt-2 flex items-center gap-3 text-xs text-muted-foreground">
                    <span>{course.units.length} units</span>
                    <span>·</span>
                    <span>{totalLessons} lessons</span>
                  </div>
                </div>
                {isOpen ? <ChevronDown className="h-5 w-5 text-muted-foreground mt-1" /> : <ChevronRight className="h-5 w-5 text-muted-foreground mt-1" />}
              </button>

              {/* Course body */}
              {isOpen && (
                <div className="border-t border-border p-4 sm:p-6 space-y-5 bg-secondary/20">
                  <p className="text-xs italic text-muted-foreground border-l-2 border-accent pl-3">
                    CEFR {course.level}: {course.cefrDescription}
                  </p>

                  {course.units.map((unit) => (
                    <div key={unit.id} className="rounded-xl border border-border bg-card p-4">
                      <div className="flex items-baseline justify-between gap-3 mb-3">
                        <div>
                          <h3 className="font-serif text-lg font-semibold">{unit.titleFr}</h3>
                          <p className="text-xs text-muted-foreground">{unit.title} · {unit.theme}</p>
                        </div>
                        <Badge variant="secondary" className="whitespace-nowrap">{unit.lessons.length} lessons</Badge>
                      </div>
                      <p className="text-sm text-foreground/70 mb-3">{unit.description}</p>

                      <div className="space-y-1.5">
                        {unit.lessons.map((lesson) => {
                          const done = isLessonComplete(lesson.id);
                          const score = getLessonScore(lesson.id);
                          return (
                            <button
                              key={lesson.id}
                              onClick={() => setView({ kind: 'lesson', level: course.level, unitId: unit.id, lessonId: lesson.id })}
                              className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-secondary transition text-left group"
                            >
                              <div className="flex-shrink-0">
                                {done ? (
                                  <CheckCircle2 className="h-5 w-5 text-chart-3" />
                                ) : (
                                  <Circle className="h-5 w-5 text-muted-foreground/40" />
                                )}
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-baseline gap-2">
                                  <p className="font-medium text-sm truncate">{lesson.titleFr}</p>
                                  {score !== null && (
                                    <span className="text-xs font-medium text-chart-3">{score}%</span>
                                  )}
                                </div>
                                <p className="text-xs text-muted-foreground truncate">{lesson.title}</p>
                              </div>
                              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                <Clock className="h-3 w-3" />
                                <span>{lesson.estimatedMinutes}min</span>
                                <ChevronRight className="h-4 w-4 opacity-0 group-hover:opacity-100 transition" />
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Helper note */}
      <div className="rounded-2xl border border-accent/40 bg-accent/10 p-5 flex gap-3">
        <BookOpen className="h-5 w-5 text-accent-foreground flex-shrink-0 mt-0.5" />
        <div className="text-sm">
          <p className="font-medium">New here? Start with A1 — Unit 1.</p>
          <p className="text-foreground/70 mt-1">
            Every lesson includes vocabulary you can hear, grammar with examples, a dialogue to listen to, and exercises with instant feedback.
          </p>
        </div>
      </div>
    </div>
  );
}
