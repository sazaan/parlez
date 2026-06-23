'use client';

import { useState, useEffect, useRef } from 'react';
import { ArrowLeft, Clock, CheckCircle2, XCircle, Volume2, AlertCircle, RotateCcw, Trophy, Loader2, Sparkles } from 'lucide-react';
import { EXAM_FORMATS } from '@/lib/mock-tests/exam-formats';
import type { TestQuestion } from '@/lib/mock-tests/types';
import { useAppStore } from '@/lib/store';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { SpeakButton } from './SpeakButton';
import { useToast } from '@/hooks/use-toast';

interface MockTestRunnerProps {
  testType: 'TEF' | 'TCF';
  section: string; // "reading-set1", "listening-set6" (set6 = AI-generated)
}

function parseSection(section: string): { sectionId: string; setId: string; setNum: number } | null {
  const match = section.match(/^(.+)-set(\d+)$/);
  if (!match) return null;
  return { sectionId: match[1], setId: `set${match[2]}`, setNum: parseInt(match[2], 10) };
}

export function MockTestRunner({ testType, section }: MockTestRunnerProps) {
  const setView = useAppStore((s) => s.setView);
  const recordTestResult = useAppStore((s) => s.recordTestResult);
  const { toast } = useToast();

  const exam = EXAM_FORMATS[testType];
  const parsed = parseSection(section);
  const sectionData = exam?.sections.find((s) => s.id === parsed?.sectionId);
  const isAIGenerated = parsed?.setNum === 6;

  const [questions, setQuestions] = useState<TestQuestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [timeLeft, setTimeLeft] = useState((sectionData?.durationMinutes ?? 15) * 60);
  const [phase, setPhase] = useState<'loading' | 'taking' | 'review' | 'results'>('loading');
  const startTimeRef = useRef<number>(Date.now());

  useEffect(() => {
    if (!parsed || !sectionData) return;
    let cancelled = false;
    setLoading(true);

    async function loadQuestions() {
      try {
        if (isAIGenerated) {
          // Set 6: Generate with AI
          await generateWithAI();
        } else {
          // Sets 1-5: Load pre-built questions from server
          await loadPrebuilt();
        }
      } catch (error) {
        if (!cancelled) {
          toast({
            title: 'Could not load questions',
            description: error instanceof Error ? error.message : 'Please try again.',
            variant: 'destructive',
          });
          setView({ kind: 'mock-tests' });
        }
      }
    }

    async function loadPrebuilt() {
      const res = await fetch(`/api/prebuilt-questions?testType=${testType}&section=${parsed!.sectionId}&setId=${parsed!.setId}`);
      if (!res.ok) {
        throw new Error('Pre-built questions not available yet. Try the AI-generated set.');
      }
      const data = await res.json();
      if (cancelled) return;
      setQuestions(data.questions);
      setLoading(false);
      setPhase('taking');
      startTimeRef.current = Date.now();
    }

    async function generateWithAI() {
      const allQuestions: TestQuestion[] = [];
      const batchSize = 15;
      const totalNeeded = sectionData!.questionCount;
      const numBatches = Math.ceil(totalNeeded / batchSize);

      for (let batch = 0; batch < numBatches; batch++) {
        if (cancelled) return;
        const currentBatchSize = Math.min(batchSize, totalNeeded - batch * batchSize);
        const res = await fetch('/api/generate-test', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            testType, section: parsed!.sectionId,
            batchSize: currentBatchSize, batchIndex: batch, setId: parsed!.setId,
          }),
        });
        if (!res.ok) throw new Error('AI generation failed');
        const data = await res.json();
        allQuestions.push(...data.questions);
        if (!cancelled) setQuestions([...allQuestions]);
      }
      if (!cancelled) {
        setLoading(false);
        setPhase('taking');
        startTimeRef.current = Date.now();
      }
    }

    loadQuestions();
    return () => { cancelled = true; };
  }, [testType, section]);

  useEffect(() => {
    if (phase !== 'taking') return;
    if (timeLeft <= 0) { setPhase('review'); return; }
    const t = setTimeout(() => setTimeLeft((s) => s - 1), 1000);
    return () => clearTimeout(t);
  }, [timeLeft, phase]);

  if (phase === 'loading') {
    const totalNeeded = sectionData?.questionCount ?? 0;
    const loaded = questions.length;
    const progress = totalNeeded > 0 ? Math.round((loaded / totalNeeded) * 100) : 0;

    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center max-w-md">
          <Loader2 className="h-12 w-12 animate-spin mx-auto text-primary mb-4" />
          <h2 className="font-serif text-2xl font-semibold mb-2">
            {isAIGenerated ? 'Generating AI Questions' : 'Loading Questions'}
          </h2>
          <p className="text-sm text-muted-foreground mb-4">
            {isAIGenerated
              ? `Creating ${totalNeeded} exam-style questions with AI...`
              : `Loading ${totalNeeded} pre-built exam questions...`}
          </p>
          {isAIGenerated && (
            <>
              <div className="h-2 rounded-full bg-secondary overflow-hidden max-w-xs mx-auto">
                <div className="h-full bg-primary transition-all" style={{ width: `${progress}%` }} />
              </div>
              <p className="text-xs text-muted-foreground mt-2">{loaded} / {totalNeeded} generated</p>
            </>
          )}
        </div>
      </div>
    );
  }

  if (questions.length === 0 || !sectionData) {
    return (
      <div className="text-center py-20">
        <p className="text-muted-foreground">Section not found.</p>
        <Button onClick={() => setView({ kind: 'mock-tests' })} className="mt-4">Back to tests</Button>
      </div>
    );
  }

  const currentQuestion = questions[currentIdx];
  const answeredCount = Object.keys(answers).length;
  const allAnswered = answeredCount === questions.length;

  const handleSubmit = () => setPhase('review');

  const handleFinish = () => {
    const correctCount = questions.filter((q) => answers[q.id] === q.answer).length;
    const total = questions.length;
    const score = Math.round((correctCount / total) * 100);
    const durationSec = Math.round((Date.now() - startTimeRef.current) / 1000);

    recordTestResult({
      id: `${testType}-${section}-${Date.now()}`,
      testType, section, score, total, correctCount,
      totalQuestions: total, durationSec,
      takenAt: new Date().toISOString(),
    });

    fetch('/api/progress', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: 'test-result',
        data: { testType, section, score, correctCount, totalQuestions: total, durationSec },
      }),
    }).catch(() => {});

    setPhase('results');
  };

  const handleRetry = () => {
    setQuestions([]); setAnswers({}); setCurrentIdx(0);
    setTimeLeft(sectionData.durationMinutes * 60);
    setPhase('loading'); setLoading(true);
  };

  const formatTime = (s: number) => `${Math.floor(s / 60)}:${(s % 60).toString().padStart(2, '0')}`;

  // Results
  if (phase === 'results') {
    const correctCount = questions.filter((q) => answers[q.id] === q.answer).length;
    const total = questions.length;
    const score = Math.round((correctCount / total) * 100);
    const durationSec = Math.round((Date.now() - startTimeRef.current) / 1000);
    return (
      <div className="max-w-2xl mx-auto space-y-6">
        <div className="text-center space-y-4">
          <div className="inline-flex h-20 w-20 rounded-full items-center justify-center" style={{ background: score >= 50 ? '#2D6A4F15' : '#B4530915' }}>
            <Trophy className={`h-10 w-10 ${score >= 50 ? 'text-chart-3' : 'text-chart-4'}`} />
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">{testType} · {sectionData.title} · Set {parsed?.setNum}{isAIGenerated ? ' (AI)' : ''}</p>
            <h1 className="font-serif text-4xl font-semibold mt-2">{score}%</h1>
            <p className="mt-1 text-foreground/70">{correctCount} correct out of {total}</p>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-3">
          <div className="rounded-xl border border-border bg-card p-4 text-center">
            <CheckCircle2 className="h-5 w-5 text-chart-3 mx-auto" />
            <p className="font-serif text-2xl font-semibold mt-1">{correctCount}</p>
            <p className="text-xs text-muted-foreground">Correct</p>
          </div>
          <div className="rounded-xl border border-border bg-card p-4 text-center">
            <XCircle className="h-5 w-5 text-destructive mx-auto" />
            <p className="font-serif text-2xl font-semibold mt-1">{total - correctCount}</p>
            <p className="text-xs text-muted-foreground">Incorrect</p>
          </div>
          <div className="rounded-xl border border-border bg-card p-4 text-center">
            <Clock className="h-5 w-5 text-muted-foreground mx-auto" />
            <p className="font-serif text-2xl font-semibold mt-1">{Math.floor(durationSec / 60)}m</p>
            <p className="text-xs text-muted-foreground">Duration</p>
          </div>
        </div>
        <div className="flex gap-3 justify-center flex-wrap">
          <Button onClick={handleRetry} variant="outline" className="gap-2"><RotateCcw className="h-4 w-4" /> {isAIGenerated ? 'New questions' : 'Retry'}</Button>
          <Button onClick={() => setView({ kind: 'mock-tests' })} variant="outline">Back to all tests</Button>
          <Button onClick={() => setView({ kind: 'progress' })}>See progress</Button>
        </div>
      </div>
    );
  }

  // Review
  if (phase === 'review') {
    const unanswered = questions.length - Object.keys(answers).length;
    return (
      <div className="max-w-2xl mx-auto space-y-5">
        <header className="text-center">
          <h1 className="font-serif text-3xl font-semibold">Review your answers</h1>
          <p className="mt-2 text-foreground/70">
            You answered {Object.keys(answers).length} of {questions.length} questions.
            {unanswered > 0 && <span className="text-destructive"> {unanswered} unanswered.</span>}
          </p>
        </header>
        <div className="space-y-3 max-h-[60vh] overflow-y-auto scroll-elegant">
          {questions.map((q, i) => {
            const userAnswer = answers[q.id];
            const isCorrect = userAnswer === q.answer;
            const noAnswer = userAnswer === undefined;
            return (
              <div key={q.id} className={`rounded-xl border p-4 ${noAnswer ? 'border-muted-foreground/30 bg-secondary/30' : isCorrect ? 'border-chart-3/40 bg-chart-3/5' : 'border-destructive/40 bg-destructive/5'}`}>
                <div className="flex items-start gap-3">
                  <span className="flex-shrink-0 h-6 w-6 rounded-full bg-card border border-border text-xs font-bold flex items-center justify-center">{i + 1}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium whitespace-pre-line">{q.prompt}</p>
                    {q.audioText && (
                      <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
                        <SpeakButton text={q.audioText} size="sm" />
                        <span className="italic">&laquo; {q.audioText} &raquo;</span>
                      </div>
                    )}
                    <div className="mt-2 space-y-1">
                      {q.options?.map((opt, j) => {
                        const isUser = userAnswer === j;
                        const isCorrectOpt = j === q.answer;
                        return (
                          <div key={j} className={`text-sm p-2 rounded ${isCorrectOpt ? 'bg-chart-3/15 text-foreground font-medium' : isUser ? 'bg-destructive/15 text-destructive' : 'text-foreground/70'}`}>
                            {opt}
                            {isCorrectOpt && <CheckCircle2 className="inline-block h-3 w-3 ml-2 text-chart-3" />}
                            {isUser && !isCorrectOpt && <XCircle className="inline-block h-3 w-3 ml-2 text-destructive" />}
                          </div>
                        );
                      })}
                    </div>
                    {q.explanation && <p className="mt-2 text-xs text-foreground/60 italic">{q.explanation}</p>}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
        <div className="flex gap-3 justify-center">
          <Button variant="outline" onClick={() => setPhase('taking')}>Back to test</Button>
          <Button onClick={handleFinish} className="gap-2"><Trophy className="h-4 w-4" /> See results</Button>
        </div>
      </div>
    );
  }

  // Taking
  const progressPercent = ((currentIdx + 1) / questions.length) * 100;
  return (
    <div className="space-y-5 max-w-3xl mx-auto">
      <div className="flex items-center justify-between gap-3">
        <Button variant="ghost" size="sm" onClick={() => setView({ kind: 'mock-tests' })} className="gap-1.5">
          <ArrowLeft className="h-4 w-4" /> Exit
        </Button>
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="gap-1"><Clock className="h-3 w-3" /> {formatTime(timeLeft)}</Badge>
          <Badge variant="outline">{testType} · {sectionData.title} · Set {parsed?.setNum}{isAIGenerated ? ' (AI)' : ''}</Badge>
        </div>
      </div>
      <div>
        <div className="flex justify-between text-xs text-muted-foreground mb-1">
          <span>Question {currentIdx + 1} of {questions.length}</span>
          <span>{answeredCount} answered</span>
        </div>
        <div className="h-1.5 rounded-full bg-secondary overflow-hidden">
          <div className="h-full bg-primary transition-all" style={{ width: `${progressPercent}%` }} />
        </div>
      </div>
      <div className="rounded-2xl border border-border bg-card p-6 sm:p-8">
        <div className="flex items-center gap-2 mb-4 flex-wrap">
          {currentQuestion.level && <Badge variant="outline" className="text-[10px] uppercase tracking-wider">Level {currentQuestion.level}</Badge>}
          {currentQuestion.audioText && <Badge variant="secondary" className="text-[10px] gap-1"><Volume2 className="h-3 w-3" /> Audio</Badge>}
          {sectionData.sections && <Badge variant="outline" className="text-[10px]">{getSubSection(currentIdx + 1, testType, parsed?.sectionId || '')}</Badge>}
        </div>
        <p className="text-base font-medium whitespace-pre-line mb-2">{currentQuestion.prompt}</p>
        {currentQuestion.audioText && (
          <div className="my-4 p-4 rounded-xl bg-secondary/50 border border-border flex items-center gap-3">
            <SpeakButton text={currentQuestion.audioText} size="lg" variant="default" label="Play audio" />
            <p className="text-xs text-muted-foreground">Play the audio, then choose your answer.</p>
          </div>
        )}
        <div className="mt-4 space-y-2.5">
          {currentQuestion.options?.map((opt, i) => {
            const isSelected = answers[currentQuestion.id] === i;
            return (
              <button key={i} onClick={() => phase === 'taking' && setAnswers((p) => ({ ...p, [currentQuestion.id]: i }))}
                className={`w-full text-left p-4 rounded-xl border text-sm transition flex items-start gap-3 ${isSelected ? 'border-primary bg-primary/5 shadow-sm' : 'border-border hover:bg-secondary hover:border-foreground/20'}`}>
                <span className={`flex-shrink-0 h-6 w-6 rounded-full border-2 flex items-center justify-center text-xs font-bold ${isSelected ? 'border-primary bg-primary text-primary-foreground' : 'border-border text-muted-foreground'}`}>{String.fromCharCode(65 + i)}</span>
                <span className="flex-1 pt-0.5">{opt}</span>
              </button>
            );
          })}
        </div>
      </div>
      <div className="flex items-center justify-between gap-3">
        <Button variant="outline" onClick={() => setCurrentIdx((i) => Math.max(0, i - 1))} disabled={currentIdx === 0}>Previous</Button>
        <div className="flex gap-1 flex-wrap justify-center max-w-md">
          {questions.map((q, i) => {
            const isAnswered = answers[q.id] !== undefined;
            const isCurrent = i === currentIdx;
            return (
              <button key={q.id} onClick={() => setCurrentIdx(i)}
                className={`h-7 w-7 rounded-md text-xs font-medium transition ${isCurrent ? 'bg-primary text-primary-foreground' : isAnswered ? 'bg-chart-3/20 text-chart-3 hover:bg-chart-3/30' : 'bg-secondary text-muted-foreground hover:bg-secondary/80'}`}
                aria-label={`Q${i + 1}`}>{i + 1}</button>
            );
          })}
        </div>
        {currentIdx === questions.length - 1 ? (
          <Button onClick={handleSubmit} className="gap-2" variant={allAnswered ? 'default' : 'secondary'}><CheckCircle2 className="h-4 w-4" /> Submit</Button>
        ) : (
          <Button onClick={() => setCurrentIdx((i) => Math.min(questions.length - 1, i + 1))} disabled={currentIdx === questions.length - 1}>Next</Button>
        )}
      </div>
      {allAnswered && currentIdx === questions.length - 1 && (
        <div className="rounded-xl bg-chart-3/10 border border-chart-3/30 p-3 text-sm text-center">
          <CheckCircle2 className="inline h-4 w-4 text-chart-3 mr-1.5" />All {questions.length} questions answered!
        </div>
      )}
    </div>
  );
}

function getSubSection(questionNum: number, testType: string, sectionId: string): string {
  if (testType === 'TEF') {
    if (sectionId === 'reading') {
      if (questionNum <= 15) return 'Section A: Signs';
      if (questionNum <= 35) return 'Section B: Short texts';
      return 'Section C: Longer texts';
    }
    if (sectionId === 'listening') {
      if (questionNum <= 15) return 'Announcements';
      if (questionNum <= 35) return 'Conversations';
      return 'Radio/Interviews';
    }
    if (sectionId === 'vocabulary_grammar') return questionNum <= 20 ? 'Vocabulary' : 'Grammar';
  }
  if (testType === 'TCF') {
    if (sectionId === 'language_structures') {
      if (questionNum <= 4) return 'A1-A2';
      if (questionNum <= 10) return 'B1';
      if (questionNum <= 14) return 'B2';
      return 'C1-C2';
    }
    if (questionNum <= 6) return 'A1';
    if (questionNum <= 12) return 'A2';
    if (questionNum <= 18) return 'B1';
    if (questionNum <= 24) return 'B2';
    return 'C1-C2';
  }
  return '';
}
