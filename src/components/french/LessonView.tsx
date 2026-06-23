'use client';

import { useState, useMemo } from 'react';
import { ArrowLeft, ArrowRight, BookOpen, Volume2, MessageCircle, PenLine, CheckCircle2, XCircle, Info, Sparkles, RotateCcw, PencilLine, Zap } from 'lucide-react';
import { courses, getCourse } from '@/lib/courses';
import type { CourseLevel, Exercise, VocabItem, GrammarRule, DialogueLine } from '@/lib/courses/types';
import { useAppStore } from '@/lib/store';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { SpeakButton } from './SpeakButton';
import { ConjugationSection } from './ConjugationSection';
import { useToast } from '@/hooks/use-toast';

interface LessonViewProps {
  level: CourseLevel;
  unitId: string;
  lessonId: string;
}

type LessonSection = 'overview' | 'vocabulary' | 'grammar' | 'conjugation' | 'dialogue' | 'practice' | 'workbook';

export function LessonView({ level, unitId, lessonId }: LessonViewProps) {
  const setView = useAppStore((s) => s.setView);
  const markLessonComplete = useAppStore((s) => s.markLessonComplete);
  const isLessonComplete = useAppStore((s) => s.isLessonComplete);
  const { toast } = useToast();

  const course = getCourse(level);
  const unit = course.units.find((u) => u.id === unitId);
  const lesson = unit?.lessons.find((l) => l.id === lessonId);

  const [section, setSection] = useState<LessonSection>('overview');
  const [exerciseResults, setExerciseResults] = useState<Record<string, { correct: boolean; userAnswer: string | number | number[] | Record<string, string> }>>({});

  if (!lesson || !unit) {
    return (
      <div className="text-center py-20">
        <p className="text-muted-foreground">Lesson not found.</p>
        <Button onClick={() => setView({ kind: 'courses' })} className="mt-4">Back to courses</Button>
      </div>
    );
  }

  const sections: { id: LessonSection; label: string; icon: typeof BookOpen }[] = [
    { id: 'overview', label: 'Overview', icon: Info },
    { id: 'vocabulary', label: 'Vocabulary', icon: BookOpen },
    { id: 'grammar', label: 'Grammar', icon: PenLine },
    ...(lesson.conjugation ? [{ id: 'conjugation' as LessonSection, label: 'Conjugation', icon: Zap }] : []),
    { id: 'dialogue', label: 'Dialogue', icon: MessageCircle },
    { id: 'practice', label: 'Practice', icon: Sparkles },
    ...(lesson.activities && lesson.activities.length > 0 ? [{ id: 'workbook' as LessonSection, label: 'Workbook', icon: PencilLine }] : []),
  ];

  const totalExercises = lesson.exercises.length + (lesson.activities?.length ?? 0);
  const answeredCount = Object.keys(exerciseResults).length;
  const correctCount = Object.values(exerciseResults).filter((r) => r.correct).length;
  const allAnswered = answeredCount >= lesson.exercises.length; // activities are bonus
  const practiceScore = lesson.exercises.length > 0 ? Math.round((Object.entries(exerciseResults).filter(([k, r]) => lesson.exercises.some(e => e.id === k) && r.correct).length / lesson.exercises.length) * 100) : 0;
  const fullScore = totalExercises > 0 ? Math.round((correctCount / totalExercises) * 100) : 0;

  const handleCheck = (ex: Exercise, userAnswer: string | number | number[] | Record<string, string>) => {
    const isCorrect = checkAnswer(ex, userAnswer);
    setExerciseResults((p) => ({ ...p, [ex.id]: { correct: isCorrect, userAnswer } }));
    if (isCorrect) {
      toast({ title: 'Correct !', description: 'Bien joué.' });
    } else {
      toast({ title: 'Pas tout à fait', description: 'See the explanation below.', variant: 'destructive' });
    }
  };

  const handleComplete = () => {
    markLessonComplete({
      lessonId: lesson.id,
      level,
      unitId,
      score: practiceScore,
      completedAt: new Date().toISOString(),
    });
    // Also save to server
    fetch('/api/progress', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: 'lesson-complete',
        data: { courseLevel: level, unitId, lessonId: lesson.id, score: practiceScore },
      }),
    }).catch(() => {}); // silent fail — local store is source of truth
    toast({
      title: 'Lesson complete !',
      description: `You scored ${practiceScore}% on practice. Keep it up !`,
    });
    setView({ kind: 'courses' });
  };

  const allLessons = course.units.flatMap((u) => u.lessons.map((l) => ({ lesson: l, unitId: u.id })));
  const currentIndex = allLessons.findIndex((x) => x.lesson.id === lesson.id);
  const nextLesson = currentIndex >= 0 && currentIndex < allLessons.length - 1 ? allLessons[currentIndex + 1] : null;

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-3 flex-wrap">
        <Button variant="ghost" size="sm" onClick={() => setView({ kind: 'courses' })} className="gap-1.5">
          <ArrowLeft className="h-4 w-4" /> Courses
        </Button>
        <span className="text-muted-foreground text-sm">/</span>
        <span className="text-sm text-muted-foreground">{course.book}</span>
        <span className="text-muted-foreground text-sm">/</span>
        <span className="text-sm font-medium">{unit.titleFr}</span>
      </div>

      {/* Lesson header */}
      <header className="rounded-2xl border border-border bg-card p-6 sm:p-8" style={{ borderTopColor: course.color, borderTopWidth: '4px' }}>
        <div className="flex items-center gap-2 mb-2 flex-wrap">
          <Badge style={{ background: course.color, color: 'white' }}>{course.level}</Badge>
          {isLessonComplete(lesson.id) && (
            <Badge variant="secondary" className="gap-1">
              <CheckCircle2 className="h-3 w-3" /> Completed
            </Badge>
          )}
          <span className="text-xs text-muted-foreground ml-auto flex items-center gap-1">
            <Volume2 className="h-3 w-3" /> {lesson.estimatedMinutes} min
          </span>
        </div>
        <h1 className="font-serif text-3xl sm:text-4xl font-semibold">{lesson.titleFr}</h1>
        <p className="mt-1 text-lg text-foreground/70">{lesson.title}</p>
        <p className="mt-3 text-foreground/70">{lesson.description}</p>
      </header>

      {/* Section tabs */}
      <div className="sticky top-16 sm:top-16 z-30 -mx-4 sm:mx-0 px-4 sm:px-0 py-2 bg-background/95 backdrop-blur border-b border-border/60">
        <div className="flex items-center gap-1 overflow-x-auto scroll-elegant">
          {sections.map((s) => (
            <button
              key={s.id}
              onClick={() => setSection(s.id)}
              className={`px-3.5 py-2 rounded-full text-sm font-medium whitespace-nowrap flex items-center gap-1.5 transition ${
                section === s.id
                  ? 'bg-primary text-primary-foreground'
                  : 'text-foreground/70 hover:bg-secondary'
              }`}
            >
              <s.icon className="h-3.5 w-3.5" />
              {s.label}
              {s.id === 'practice' && answeredCount > 0 && (
                <span className="ml-1 text-xs opacity-80">
                  ({Object.entries(exerciseResults).filter(([k, r]) => lesson.exercises.some(e => e.id === k) && r.correct).length}/{lesson.exercises.length})
                </span>
              )}
              {s.id === 'workbook' && lesson.activities && (
                <span className="ml-1 text-xs opacity-70">({lesson.activities.length})</span>
              )}
            </button>
          ))}
        </div>
      </div>

      <div className="min-h-[300px]">
        {section === 'overview' && (
          <OverviewSection
            lesson={lesson}
            level={level}
            color={course.color}
            onStartPractice={() => setSection('practice')}
            onComplete={handleComplete}
            score={practiceScore}
            allAnswered={allAnswered}
            isComplete={isLessonComplete(lesson.id)}
          />
        )}
        {section === 'vocabulary' && <VocabularySection vocabulary={lesson.vocabulary} />}
        {section === 'grammar' && <GrammarSection grammar={lesson.grammar} />}
        {section === 'conjugation' && lesson.conjugation && <ConjugationSection data={lesson.conjugation} />}
        {section === 'dialogue' && <DialogueSection dialogue={lesson.dialogue} />}
        {section === 'practice' && (
          <PracticeSection
            title="Practice exercises"
            description="Core exercises that test the main points of this lesson."
            exercises={lesson.exercises}
            results={exerciseResults}
            onCheck={handleCheck}
            onComplete={handleComplete}
            score={practiceScore}
            allAnswered={allAnswered}
            correctCount={Object.entries(exerciseResults).filter(([k, r]) => lesson.exercises.some(e => e.id === k) && r.correct).length}
            totalCount={lesson.exercises.length}
          />
        )}
        {section === 'workbook' && lesson.activities && (
          <PracticeSection
            title="Activity workbook"
            description="Extra practice — dictation, word banks, sentence reordering, and more."
            exercises={lesson.activities}
            results={exerciseResults}
            onCheck={handleCheck}
            onComplete={handleComplete}
            score={fullScore}
            allAnswered={false}
            correctCount={Object.entries(exerciseResults).filter(([k, r]) => lesson.activities!.some(e => e.id === k) && r.correct).length}
            totalCount={lesson.activities.length}
            isActivityWorkbook
          />
        )}
      </div>

      {section === 'overview' && lesson.culturalNote && (
        <div className="rounded-2xl border border-accent/40 bg-accent/10 p-5">
          <div className="flex gap-3">
            <Info className="h-5 w-5 text-accent-foreground flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-serif text-lg font-semibold mb-1">Cultural note</p>
              <p className="text-sm text-foreground/80">{lesson.culturalNote}</p>
            </div>
          </div>
        </div>
      )}

      {nextLesson && (
        <div className="flex justify-end">
          <Button
            variant="outline"
            onClick={() => setView({ kind: 'lesson', level, unitId: nextLesson.unitId, lessonId: nextLesson.lesson.id })}
            className="gap-2"
          >
            Next lesson: {nextLesson.lesson.titleFr} <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}

function OverviewSection({ lesson, color, onStartPractice, onComplete, score, allAnswered, isComplete }: {
  lesson: typeof courses[0]['units'][0]['lessons'][0];
  level: CourseLevel;
  color: string;
  onStartPractice: () => void;
  onComplete: () => void;
  score: number;
  allAnswered: boolean;
  isComplete: boolean;
}) {
  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-border bg-card p-6">
        <h2 className="font-serif text-xl font-semibold mb-3">What you&apos;ll learn</h2>
        <ul className="space-y-2">
          {lesson.objectives.map((o: string, i: number) => (
            <li key={i} className="flex items-start gap-2.5">
              <span className="flex-shrink-0 mt-0.5 h-5 w-5 rounded-full flex items-center justify-center text-[10px] font-bold text-white" style={{ background: color }}>
                {i + 1}
              </span>
              <span className="text-sm text-foreground/80">{o}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="grid sm:grid-cols-3 gap-3">
        <div className="rounded-xl border border-border bg-card p-4 text-center">
          <BookOpen className="h-5 w-5 mx-auto text-primary" />
          <p className="mt-2 font-serif text-2xl font-semibold">{lesson.vocabulary.length}</p>
          <p className="text-xs text-muted-foreground">Vocabulary words</p>
        </div>
        <div className="rounded-xl border border-border bg-card p-4 text-center">
          <PenLine className="h-5 w-5 mx-auto text-primary" />
          <p className="mt-2 font-serif text-2xl font-semibold">{lesson.grammar.length}</p>
          <p className="text-xs text-muted-foreground">Grammar rules</p>
        </div>
        <div className="rounded-xl border border-border bg-card p-4 text-center">
          <Sparkles className="h-5 w-5 mx-auto text-primary" />
          <p className="mt-2 font-serif text-2xl font-semibold">{lesson.exercises.length + (lesson.activities?.length ?? 0)}</p>
          <p className="text-xs text-muted-foreground">Exercises + activities</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        <Button onClick={onStartPractice} size="lg" className="gap-2">
          <Sparkles className="h-4 w-4" /> Start practice
        </Button>
        {isComplete && (
          <Button variant="outline" onClick={onStartPractice} size="lg" className="gap-2">
            <RotateCcw className="h-4 w-4" /> Try again
          </Button>
        )}
        {/* Always show "Mark complete" button so users can progress */}
        <Button variant="secondary" onClick={onComplete} size="lg" className="gap-2">
          <CheckCircle2 className="h-4 w-4" /> {isComplete ? 'Update score' : 'Mark lesson complete'} {allAnswered && `(${score}%)`}
        </Button>
      </div>
    </div>
  );
}

function VocabularySection({ vocabulary }: { vocabulary: VocabItem[] }) {
  const categories = useMemo(() => {
    const groups: Record<string, VocabItem[]> = {};
    vocabulary.forEach((v) => {
      const c = v.category || 'words';
      if (!groups[c]) groups[c] = [];
      groups[c].push(v);
    });
    return groups;
  }, [vocabulary]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="font-serif text-2xl font-semibold">Vocabulary</h2>
        <span className="text-sm text-muted-foreground">{vocabulary.length} words · click 🔊 to hear each</span>
      </div>
      {Object.entries(categories).map(([cat, items]) => (
        <div key={cat}>
          <h3 className="text-xs uppercase tracking-[0.18em] text-muted-foreground mb-2 font-medium">{cat}</h3>
          <div className="grid sm:grid-cols-2 gap-2.5">
            {items.map((v, i) => (
              <div key={i} className="rounded-xl border border-border bg-card p-3.5 flex items-start gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline gap-2 flex-wrap">
                    <p className="font-medium text-foreground">{v.fr}</p>
                    {v.ipa && <p className="text-xs text-muted-foreground font-mono">{v.ipa}</p>}
                  </div>
                  <p className="text-sm text-foreground/70">{v.en}</p>
                  {v.example && (
                    <p className="mt-2 text-xs text-foreground/60 italic border-l-2 border-accent pl-2">
                      « {v.example} »
                      {v.exampleEn && <span className="block not-italic text-muted-foreground">— {v.exampleEn}</span>}
                    </p>
                  )}
                </div>
                <SpeakButton text={v.example || v.fr} size="sm" variant="ghost" />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function GrammarSection({ grammar }: { grammar: GrammarRule[] }) {
  return (
    <div className="space-y-6">
      <h2 className="font-serif text-2xl font-semibold">Grammar</h2>
      {grammar.map((rule, i) => (
        <div key={i} className="rounded-2xl border border-border bg-card p-5 sm:p-6">
          <h3 className="font-serif text-xl font-semibold mb-2">{rule.title}</h3>
          <p className="text-sm text-foreground/80 leading-relaxed">{rule.explanation}</p>

          {rule.examples?.length > 0 && (
            <div className="mt-4 space-y-2">
              <p className="text-xs uppercase tracking-wider text-muted-foreground font-medium">Examples</p>
              {rule.examples.map((ex, j) => (
                <div key={j} className="rounded-lg bg-secondary/50 p-3 flex items-center gap-3">
                  <div className="flex-1">
                    <p className="font-medium">{ex.fr}</p>
                    <p className="text-xs text-muted-foreground">{ex.en}</p>
                  </div>
                  <SpeakButton text={ex.fr} size="sm" />
                </div>
              ))}
            </div>
          )}

          {rule.table && (
            <div className="mt-4 overflow-x-auto scroll-elegant">
              <table className="w-full text-sm border-collapse">
                {rule.table.caption && (
                  <caption className="text-left text-xs text-muted-foreground mb-2">{rule.table.caption}</caption>
                )}
                <thead>
                  <tr className="bg-primary/10">
                    {rule.table.headers.map((h, j) => (
                      <th key={j} className="text-left p-2.5 font-medium border-b border-border">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rule.table.rows.map((row, j) => (
                    <tr key={j} className={j % 2 === 0 ? 'bg-card' : 'bg-secondary/30'}>
                      {row.map((cell, k) => (
                        <td key={k} className="p-2.5 border-b border-border/50">{cell}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {rule.tip && (
            <div className="mt-4 rounded-lg bg-accent/15 border border-accent/30 p-3 text-sm">
              <span className="font-medium text-accent-foreground">Tip: </span>
              <span className="text-foreground/80">{rule.tip}</span>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function DialogueSection({ dialogue }: { dialogue: DialogueLine[] }) {
  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="font-serif text-2xl font-semibold">Dialogue</h2>
        <SpeakButton
          text={dialogue.map((d) => d.fr).join('. ')}
          size="sm"
          variant="outline"
          label="Play all"
        />
      </div>

      <div className="space-y-3 max-w-3xl">
        {dialogue.map((line, i) => {
          const isA = line.speaker === 'A';
          const isNarrator = line.speaker === 'N';
          return (
            <div key={i} className={`flex ${isNarrator ? 'justify-center' : isA ? 'justify-start' : 'justify-end'}`}>
              <div className={`max-w-[85%] sm:max-w-[75%] ${isNarrator ? 'text-center text-xs italic text-muted-foreground' : ''}`}>
                {!isNarrator && line.name && (
                  <p className={`text-xs font-medium text-muted-foreground mb-1 ${isA ? 'text-left' : 'text-right'}`}>
                    {line.name}
                  </p>
                )}
                <div
                  className={`rounded-2xl p-3.5 ${
                    isNarrator
                      ? 'bg-transparent'
                      : isA
                      ? 'bg-card border border-border rounded-tl-sm'
                      : 'bg-primary text-primary-foreground rounded-tr-sm'
                  }`}
                >
                  <p className={`text-sm ${isNarrator ? 'italic' : 'font-medium'}`}>{line.fr}</p>
                  <p className={`text-xs mt-1 ${isA ? 'text-muted-foreground' : isNarrator ? '' : 'text-primary-foreground/70'}`}>
                    {line.en}
                  </p>
                </div>
                {!isNarrator && (
                  <div className={isA ? 'text-left mt-1' : 'text-right mt-1'}>
                    <SpeakButton text={line.fr} size="sm" variant="ghost" />
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function PracticeSection({ title, description, exercises, results, onCheck, onComplete, score, allAnswered, correctCount, totalCount, isActivityWorkbook }: {
  title: string;
  description: string;
  exercises: Exercise[];
  results: Record<string, { correct: boolean; userAnswer: string | number | number[] | Record<string, string> }>;
  onCheck: (ex: Exercise, userAnswer: string | number | number[] | Record<string, string>) => void;
  onComplete: () => void;
  score: number;
  allAnswered: boolean;
  correctCount: number;
  totalCount: number;
  isActivityWorkbook?: boolean;
}) {
  return (
    <div className="space-y-5">
      <div>
        <h2 className="font-serif text-2xl font-semibold">{title}</h2>
        <p className="text-sm text-foreground/70 mt-1">{description}</p>
        <div className="mt-2 text-sm text-muted-foreground">
          {correctCount} / {totalCount} correct
          {allAnswered && <span className="ml-2 font-medium text-foreground">· {score}%</span>}
        </div>
      </div>

      {exercises.map((ex, i) => (
        <ExerciseCard key={ex.id} ex={ex} index={i} result={results[ex.id]} onCheck={onCheck} />
      ))}

      {/* Show completion card when all exercises are answered */}
      {allAnswered && !isActivityWorkbook && (
        <div className="rounded-2xl border border-border bg-card p-5 sm:p-6 text-center">
          <p className="font-serif text-3xl font-semibold" style={{ color: score >= 70 ? '#2D6A4F' : '#B45309' }}>
            {score}%
          </p>
          <p className="mt-1 text-sm text-foreground/70">
            {score === 100 ? 'Parfait ! Toutes les réponses sont correctes.' :
             score >= 70 ? 'Bien joué ! Continuez comme ça.' :
             'Pas mal — revoyez la leçon et réessayez.'}
          </p>
          <Button onClick={onComplete} className="mt-4 gap-2">
            <CheckCircle2 className="h-4 w-4" /> Mark lesson complete
          </Button>
        </div>
      )}

      {/* Always show a "Mark complete" button at the bottom of practice/workbook */}
      {!allAnswered && (
        <div className="rounded-2xl border border-border bg-card p-5 sm:p-6 text-center">
          <p className="text-sm text-foreground/70 mb-3">
            {correctCount} of {totalCount} correct so far. Keep going, or mark this lesson complete to move on.
          </p>
          <Button onClick={onComplete} variant="secondary" className="gap-2">
            <CheckCircle2 className="h-4 w-4" /> Mark lesson complete
          </Button>
        </div>
      )}
    </div>
  );
}

function ExerciseCard({ ex, index, result, onCheck }: {
  ex: Exercise;
  index: number;
  result?: { correct: boolean; userAnswer: string | number | number[] | Record<string, string> };
  onCheck: (ex: Exercise, userAnswer: string | number | number[] | Record<string, string>) => void;
}) {
  const [userInput, setUserInput] = useState('');
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  // For matching exercises: map of left → selected right value
  const [matchingAnswers, setMatchingAnswers] = useState<Record<string, string>>({});
  // For word_bank / reorder: ordered selected words
  const [selectedWords, setSelectedWords] = useState<string[]>([]);

  // Shuffle the right-side options for matching exercises — but only once per card mount
  // so they don't reshuffle on every re-render. Using a stable key based on ex.id.
  const shuffledRights = useMemo(() => {
    if (!ex.pairs) return [];
    const rights = ex.pairs.map((p) => p.right);
    // Deterministic shuffle using a simple seeded approach (based on ex.id hash)
    const seed = ex.id.split('').reduce((s, c) => s + c.charCodeAt(0), 0);
    const shuffled = [...rights];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = (seed * (i + 7)) % (i + 1);
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return [...new Set(shuffled)]; // dedupe just in case
  }, [ex.id, ex.pairs]);

  // Shuffle the word bank / reorder words too — same deterministic approach
  const shuffledWords = useMemo(() => {
    const source = ex.wordBank ?? ex.words ?? [];
    if (source.length === 0) return [];
    const seed = ex.id.split('').reduce((s, c) => s + c.charCodeAt(0), 0) + 1;
    const shuffled = [...source];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = (seed * (i + 13)) % (i + 1);
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
  }, [ex.id, ex.wordBank, ex.words]);

  const isAnswered = result !== undefined;

  const handleSubmit = () => {
    if (ex.type === 'multiple_choice' || ex.type === 'true_false' || ex.type === 'article_choice') {
      if (selectedOption === null) return;
      onCheck(ex, selectedOption);
    } else if (ex.type === 'matching') {
      if (Object.keys(matchingAnswers).length < (ex.pairs?.length ?? 0)) return;
      onCheck(ex, matchingAnswers);
    } else if (ex.type === 'word_bank') {
      const sentence = selectedWords.join(' ');
      if (!sentence) return;
      onCheck(ex, sentence);
    } else {
      if (!userInput.trim()) return;
      onCheck(ex, userInput.trim());
    }
  };

  const typeLabels: Record<string, string> = {
    multiple_choice: 'Multiple choice',
    fill_blank: 'Fill in the blank',
    translate_to_fr: 'Translate to French',
    translate_to_en: 'Translate to English',
    true_false: 'True or false',
    reorder: 'Reorder the words',
    matching: 'Matching',
    word_bank: 'Word bank',
    dictation: 'Dictation',
    conjugation: 'Conjugation',
    article_choice: 'Article choice',
    pronoun_replace: 'Pronoun replacement',
    transformation: 'Transformation',
    short_answer: 'Short answer',
  };

  return (
    <div className="rounded-2xl border border-border bg-card p-5">
      <div className="flex items-start gap-3">
        <span className="flex-shrink-0 h-7 w-7 rounded-full bg-primary text-primary-foreground text-xs font-bold flex items-center justify-center mt-0.5">
          {index + 1}
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <Badge variant="outline" className="text-[10px] uppercase tracking-wider">{typeLabels[ex.type] || ex.type}</Badge>
            {ex.promptFr && <Badge variant="secondary" className="text-[10px]">{ex.promptFr}</Badge>}
            {ex.hint && <Badge variant="outline" className="text-[10px] text-muted-foreground">{ex.hint}</Badge>}
          </div>
          <p className="text-sm font-medium whitespace-pre-line">{ex.prompt}</p>

          {/* Dictation / audio prompt */}
          {ex.type === 'dictation' && ex.audioText && (
            <div className="mt-3 p-3 rounded-lg bg-secondary/40 flex items-center gap-3">
              <SpeakButton text={ex.audioText} size="md" variant="default" label="Play audio" />
              <span className="text-xs text-muted-foreground">Listen carefully, then type what you hear.</span>
            </div>
          )}

          {/* Multiple choice / true-false / article choice */}
          {(ex.type === 'multiple_choice' || ex.type === 'true_false' || ex.type === 'article_choice') && ex.options && (
            <div className="mt-3 space-y-2">
              {ex.options.map((opt, i) => {
                const isSelected = selectedOption === i;
                const isCorrectAnswer = i === ex.answer;
                const showResult = isAnswered;
                return (
                  <button
                    key={i}
                    onClick={() => !isAnswered && setSelectedOption(i)}
                    disabled={isAnswered}
                    className={`w-full text-left p-3 rounded-lg border text-sm transition ${
                      showResult
                        ? isCorrectAnswer
                          ? 'border-chart-3 bg-chart-3/10'
                          : isSelected
                          ? 'border-destructive bg-destructive/10'
                          : 'border-border bg-card'
                        : isSelected
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:bg-secondary'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span><span className="font-semibold mr-2">{String.fromCharCode(65 + i)}.</span>{opt}</span>
                      {showResult && isCorrectAnswer && <CheckCircle2 className="h-4 w-4 text-chart-3" />}
                      {showResult && isSelected && !isCorrectAnswer && <XCircle className="h-4 w-4 text-destructive" />}
                    </div>
                  </button>
                );
              })}
            </div>
          )}

          {/* Text input: fill_blank, translate, conjugation, dictation, pronoun_replace, transformation, short_answer */}
          {['fill_blank', 'translate_to_fr', 'translate_to_en', 'dictation', 'conjugation', 'pronoun_replace', 'transformation', 'short_answer'].includes(ex.type) && (
            <div className="mt-3">
              <input
                type="text"
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !isAnswered && handleSubmit()}
                disabled={isAnswered}
                placeholder={ex.hint || 'Type your answer...'}
                className="w-full p-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          )}

          {/* Matching */}
          {ex.type === 'matching' && ex.pairs && (
            <div className="mt-3 space-y-2">
              {ex.pairs.map((pair, i) => (
                <div key={i} className="flex items-center gap-2">
                  <span className="flex-1 p-2 rounded bg-secondary/40 text-sm font-medium">{pair.left}</span>
                  <span className="text-muted-foreground">→</span>
                  <select
                    value={matchingAnswers[pair.left] || ''}
                    onChange={(e) => !isAnswered && setMatchingAnswers((p) => ({ ...p, [pair.left]: e.target.value }))}
                    disabled={isAnswered}
                    className="flex-1 p-2 rounded border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  >
                    <option value="">— select —</option>
                    {shuffledRights.map((r) => (
                      <option key={r} value={r}>{r}</option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          )}

          {/* Word bank */}
          {ex.type === 'word_bank' && ex.wordBank && (
            <div className="mt-3 space-y-3">
              {/* Selected words */}
              <div className="min-h-[44px] p-2 rounded-lg border border-border bg-background flex flex-wrap gap-1.5">
                {selectedWords.length === 0 && <span className="text-xs text-muted-foreground self-center px-2">Click words below to build the sentence…</span>}
                {selectedWords.map((word, i) => (
                  <button
                    key={i}
                    onClick={() => !isAnswered && setSelectedWords((w) => w.filter((_, idx) => idx !== i))}
                    disabled={isAnswered}
                    className="px-2.5 py-1 rounded bg-primary/10 text-primary text-sm font-medium"
                  >
                    {word} ×
                  </button>
                ))}
              </div>
              {/* Word bank */}
              <div className="flex flex-wrap gap-1.5">
                {shuffledWords.map((word, i) => (
                  <button
                    key={i}
                    onClick={() => !isAnswered && !selectedWords.includes(word) && setSelectedWords((w) => [...w, word])}
                    disabled={isAnswered || selectedWords.includes(word)}
                    className={`px-2.5 py-1 rounded border text-sm font-medium transition ${
                      selectedWords.includes(word)
                        ? 'opacity-30 border-border bg-secondary'
                        : 'border-border bg-card hover:bg-secondary'
                    }`}
                  >
                    {word}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Reorder */}
          {ex.type === 'reorder' && ex.words && (
            <div className="mt-3 space-y-3">
              <div className="min-h-[44px] p-2 rounded-lg border border-border bg-background flex flex-wrap gap-1.5">
                {selectedWords.length === 0 && <span className="text-xs text-muted-foreground self-center px-2">Click words in the correct order…</span>}
                {selectedWords.map((word, i) => (
                  <button
                    key={i}
                    onClick={() => !isAnswered && setSelectedWords((w) => w.filter((_, idx) => idx !== i))}
                    disabled={isAnswered}
                    className="px-2.5 py-1 rounded bg-primary/10 text-primary text-sm font-medium"
                  >
                    {word} ×
                  </button>
                ))}
              </div>
              <div className="flex flex-wrap gap-1.5">
                {shuffledWords.map((word, i) => (
                  <button
                    key={i}
                    onClick={() => !isAnswered && !selectedWords.includes(word) && setSelectedWords((w) => [...w, word])}
                    disabled={isAnswered || selectedWords.includes(word)}
                    className={`px-2.5 py-1 rounded border text-sm font-medium transition ${
                      selectedWords.includes(word)
                        ? 'opacity-30 border-border bg-secondary'
                        : 'border-border bg-card hover:bg-secondary'
                    }`}
                  >
                    {word}
                  </button>
                ))}
              </div>
            </div>
          )}

          {!isAnswered && (
            <Button
              onClick={handleSubmit}
              size="sm"
              className="mt-3"
              disabled={
                ex.type === 'multiple_choice' || ex.type === 'true_false' || ex.type === 'article_choice'
                  ? selectedOption === null
                  : ex.type === 'matching'
                  ? Object.keys(matchingAnswers).length < (ex.pairs?.length ?? 0)
                  : ex.type === 'word_bank' || ex.type === 'reorder'
                  ? selectedWords.length === 0
                  : !userInput.trim()
              }
            >
              Check answer
            </Button>
          )}

          {isAnswered && (
            <div className={`mt-3 rounded-lg p-3 text-sm ${result.correct ? 'bg-chart-3/10 border border-chart-3/30' : 'bg-destructive/10 border border-destructive/30'}`}>
              <p className="font-medium flex items-center gap-1.5">
                {result.correct ? <CheckCircle2 className="h-4 w-4 text-chart-3" /> : <XCircle className="h-4 w-4 text-destructive" />}
                {result.correct ? 'Correct !' : 'Incorrect.'}
              </p>
              {!result.correct && (
                <p className="mt-1 text-xs">
                  Correct answer: <span className="font-medium">
                    {ex.type === 'multiple_choice' || ex.type === 'true_false' || ex.type === 'article_choice'
                      ? ex.options?.[ex.answer as number]
                      : ex.type === 'matching'
                      ? (ex.pairs?.map((p) => `${p.left} → ${p.right}`).join('; '))
                      : ex.type === 'word_bank' || ex.type === 'reorder'
                      ? (typeof ex.answer === 'string' ? ex.answer : '')
                      : typeof ex.answer === 'string' ? ex.answer : ''}
                  </span>
                </p>
              )}
              {ex.explanation && <p className="mt-1 text-xs text-foreground/70">{ex.explanation}</p>}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function checkAnswer(ex: Exercise, userAnswer: string | number | number[] | Record<string, string>): boolean {
  if (ex.type === 'multiple_choice' || ex.type === 'true_false' || ex.type === 'article_choice') {
    return userAnswer === ex.answer;
  }
  if (ex.type === 'matching') {
    if (!ex.pairs) return false;
    const userMap = userAnswer as Record<string, string>;
    return ex.pairs.every((p) => userMap[p.left] === p.right);
  }
  // Text-based answers — normalize and compare
  const normalize = (s: string) => s.toLowerCase().trim()
    .replace(/[.,!?;:'"]/g, '')
    .replace(/\s+/g, ' ')
    .replace(/[éèêë]/g, 'e')
    .replace(/[àâä]/g, 'a')
    .replace(/[îï]/g, 'i')
    .replace(/[ôö]/g, 'o')
    .replace(/[ûü]/g, 'u')
    .replace(/ç/g, 'c');
  const correct = typeof ex.answer === 'string' ? normalize(ex.answer) : '';
  const user = typeof userAnswer === 'string' ? normalize(userAnswer) : '';
  if (user === correct) return true;
  if (ex.acceptable) {
    return ex.acceptable.some((a) => normalize(a) === user);
  }
  return false;
}
