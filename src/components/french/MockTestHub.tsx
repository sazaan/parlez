'use client';

import { useState } from 'react';
import { Clock, FileText, ArrowRight, Info, ChevronRight, Layers, Sparkles } from 'lucide-react';
import { EXAM_FORMATS } from '@/lib/mock-tests/exam-formats';
import { useAppStore } from '@/lib/store';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

export function MockTestHub() {
  const setView = useAppStore((s) => s.setView);
  const testResults = useAppStore((s) => s.testResults);
  const [selectedExam, setSelectedExam] = useState<'TEF' | 'TCF' | null>(null);

  const TOTAL_SETS = 6; // 5 pre-built + 1 AI-generated

  if (selectedExam) {
    const exam = EXAM_FORMATS[selectedExam];
    const totalQuestions = exam.sections.reduce((sum, s) => sum + s.questionCount, 0);

    return (
      <div className="space-y-6">
        <button onClick={() => setSelectedExam(null)} className="text-sm text-primary hover:underline">← All exams</button>

        <header className="space-y-2">
          <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">{exam.name} Practice — Full Exam Format</p>
          <h1 className="font-serif text-3xl sm:text-4xl font-semibold">{exam.name} — {TOTAL_SETS} Practice Sets</h1>
          <p className="text-foreground/70 max-w-2xl">
            Sets 1-5 contain <strong>pre-built exam questions</strong> based on real TEF/TCF formats. Set 6 is <strong>AI-generated</strong> with fresh questions every time. Each set has the exact exam format: {exam.sections.map(s => `${s.questionCount} ${s.title.toLowerCase()}`).join(' + ')} = {totalQuestions} total.
          </p>
        </header>

        {/* Exam format overview */}
        <div className="rounded-2xl border border-border bg-card overflow-hidden">
          <div className="p-5 border-b border-border bg-secondary/30">
            <h2 className="font-serif text-xl font-semibold mb-1">Exam Structure (Official Format)</h2>
            <p className="text-sm text-muted-foreground">{exam.fullName} — {exam.administeredBy}</p>
          </div>
          <div className="divide-y divide-border">
            {exam.sections.map((section) => (
              <div key={section.id} className="p-4 flex items-center gap-4">
                <span className="text-2xl flex-shrink-0">{section.icon}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline gap-2 flex-wrap">
                    <p className="font-medium">{section.title}</p>
                    <p className="text-xs text-muted-foreground italic">{section.titleFr}</p>
                  </div>
                  <p className="text-xs text-foreground/70 mt-0.5">{section.description}</p>
                  {section.sections && (
                    <div className="mt-1.5 flex flex-wrap gap-1">
                      {section.sections.map((sub, i) => (
                        <Badge key={i} variant="outline" className="text-[10px]">{sub}</Badge>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex-shrink-0 text-right">
                  <p className="font-serif text-2xl font-semibold" style={{ color: exam.color }}>{section.questionCount}</p>
                  <p className="text-xs text-muted-foreground">questions</p>
                  <p className="text-xs text-muted-foreground flex items-center gap-0.5 justify-end mt-0.5"><Clock className="h-3 w-3" />{section.durationMinutes}min</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Practice sets */}
        <div>
          <h2 className="font-serif text-2xl font-semibold mb-4">Practice Sets</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {Array.from({ length: TOTAL_SETS }, (_, i) => i + 1).map((setNum) => {
              const isAI = setNum === 6;
              const setResults = testResults.filter((r) => r.testType === selectedExam && r.section.includes(`set${setNum}`));
              const lastScore = setResults.length > 0
                ? Math.round(setResults.reduce((sum, r) => sum + r.correctCount, 0) / setResults.reduce((sum, r) => sum + r.totalQuestions, 0) * 100)
                : null;

              return (
                <div key={setNum} className={`rounded-2xl border p-5 ${isAI ? 'border-primary/40 bg-primary/5' : 'border-border bg-card'}`}>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div className={`h-10 w-10 rounded-xl flex items-center justify-center font-serif font-bold text-white ${isAI ? 'bg-gradient-to-br from-primary to-purple-600' : ''}`} style={!isAI ? { background: exam.color } : {}}>
                        {isAI ? <Sparkles className="h-5 w-5" /> : setNum}
                      </div>
                      <div>
                        <p className="font-medium">{isAI ? 'AI Generated' : `Practice Set ${setNum}`}</p>
                        <p className="text-xs text-muted-foreground">{totalQuestions} questions · Full exam</p>
                      </div>
                    </div>
                    {lastScore !== null && <Badge style={{ background: lastScore >= 70 ? '#2D6A4F' : '#B45309', color: 'white' }}>{lastScore}%</Badge>}
                  </div>

                  {isAI && (
                    <p className="text-xs text-primary mb-2 flex items-center gap-1">
                      <Sparkles className="h-3 w-3" /> Fresh questions generated each time
                    </p>
                  )}

                  <div className="space-y-1.5">
                    {exam.sections.map((section) => {
                      const sectionResults = testResults.filter((r) => r.testType === selectedExam && r.section === `${section.id}-set${setNum}`);
                      const sectionScore = sectionResults.length > 0 ? Math.round(sectionResults[0].correctCount / sectionResults[0].totalQuestions * 100) : null;
                      return (
                        <button key={section.id} onClick={() => setView({ kind: 'test-runner', testType: selectedExam, section: `${section.id}-set${setNum}` })}
                          className="w-full flex items-center gap-2 p-2.5 rounded-lg border border-border hover:bg-secondary hover:border-foreground/20 transition text-left group">
                          <span className="text-lg">{section.icon}</span>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium truncate">{section.title}</p>
                            <p className="text-xs text-muted-foreground">{section.questionCount} Q · {section.durationMinutes} min</p>
                          </div>
                          {sectionScore !== null && <span className="text-xs font-medium" style={{ color: sectionScore >= 70 ? '#2D6A4F' : '#B45309' }}>{sectionScore}%</span>}
                          <ChevronRight className="h-4 w-4 text-muted-foreground group-hover:text-foreground transition" />
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="rounded-2xl border border-accent/40 bg-accent/10 p-5 flex gap-3">
          <Info className="h-5 w-5 text-accent-foreground flex-shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="font-medium mb-1">About {exam.name}</p>
            <p className="text-foreground/70">{exam.description}</p>
            <p className="text-foreground/70 mt-2"><strong>Used for:</strong> {exam.usedFor}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Official Exam Practice</p>
        <h1 className="font-serif text-3xl sm:text-4xl font-semibold">Mock Tests — Full Exam Format</h1>
        <p className="text-foreground/70 max-w-2xl">
          Practice with <strong>full-length exams</strong> matching the exact official format. {TOTAL_SETS} sets per exam: 5 pre-built + 1 AI-generated. Same question counts and time limits as the real test.
        </p>
      </header>

      <div className="grid lg:grid-cols-2 gap-5">
        {Object.values(EXAM_FORMATS).map((exam) => {
          const totalQuestions = exam.sections.reduce((sum, s) => sum + s.questionCount, 0);
          const totalDuration = exam.sections.reduce((sum, s) => sum + s.durationMinutes, 0);
          const pastResults = testResults.filter((r) => r.testType === exam.type);
          const lastScore = pastResults.length > 0 ? Math.round(pastResults.reduce((sum, r) => sum + r.correctCount, 0) / pastResults.reduce((sum, r) => sum + r.totalQuestions, 0) * 100) : null;

          return (
            <div key={exam.type} className="rounded-2xl border border-border bg-card overflow-hidden">
              <div className="p-5 sm:p-6 text-white" style={{ background: `linear-gradient(135deg, ${exam.color}, ${exam.color}dd)` }}>
                <div className="flex items-baseline justify-between">
                  <h2 className="font-serif text-3xl font-bold">{exam.name}</h2>
                  {lastScore !== null && <Badge className="bg-white/20 text-white border-white/30">Last: {lastScore}%</Badge>}
                </div>
                <p className="mt-1 text-white/90 text-sm">{exam.fullName}</p>
              </div>
              <div className="p-5 sm:p-6 space-y-4">
                <div className="text-sm text-foreground/70">{exam.description}</div>
                <div className="grid grid-cols-3 gap-2">
                  <div className="rounded-lg bg-secondary/40 p-3 text-center"><p className="font-serif text-xl font-semibold">{TOTAL_SETS}</p><p className="text-xs text-muted-foreground">Sets (5+1 AI)</p></div>
                  <div className="rounded-lg bg-secondary/40 p-3 text-center"><p className="font-serif text-xl font-semibold">{totalQuestions}</p><p className="text-xs text-muted-foreground">Q per set</p></div>
                  <div className="rounded-lg bg-secondary/40 p-3 text-center"><p className="font-serif text-xl font-semibold">{totalDuration}m</p><p className="text-xs text-muted-foreground">Time per set</p></div>
                </div>
                <div className="space-y-2">
                  <p className="text-xs uppercase tracking-wider text-muted-foreground font-medium">Sections (exact exam format)</p>
                  {exam.sections.map((section) => (
                    <div key={section.id} className="flex items-center gap-2 text-sm">
                      <span className="text-lg">{section.icon}</span>
                      <span className="flex-1">{section.title}</span>
                      <Badge variant="secondary" className="text-xs">{section.questionCount} Q</Badge>
                      <span className="text-xs text-muted-foreground flex items-center gap-0.5"><Clock className="h-3 w-3" />{section.durationMinutes}m</span>
                    </div>
                  ))}
                </div>
                <Button onClick={() => setSelectedExam(exam.type as 'TEF' | 'TCF')} className="w-full gap-2" size="lg" style={{ background: exam.color }}>
                  <Layers className="h-4 w-4" /> View {TOTAL_SETS} practice sets <ArrowRight className="h-4 w-4" />
                </Button>
                <div className="text-xs text-muted-foreground"><strong>Used for:</strong> {exam.usedFor}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
