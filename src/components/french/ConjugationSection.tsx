'use client';

import { useState } from 'react';
import { Zap, CheckCircle2, XCircle, RotateCcw } from 'lucide-react';
import type { ConjugationData, ConjugationPractice } from '@/lib/courses/types';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { SpeakButton } from './SpeakButton';
import { useToast } from '@/hooks/use-toast';

interface ConjugationSectionProps {
  data: ConjugationData;
}

export function ConjugationSection({ data }: ConjugationSectionProps) {
  const [results, setResults] = useState<Record<string, { correct: boolean; userAnswer: string }>>({});

  const handleCheck = (ex: ConjugationPractice, userAnswer: string) => {
    const isCorrect = checkAnswer(ex, userAnswer);
    setResults((p) => ({ ...p, [ex.id]: { correct: isCorrect, userAnswer } }));
    if (isCorrect) {
      // toast handled by parent — but we can use a simple approach here
    }
  };

  const correctCount = Object.values(results).filter((r) => r.correct).length;
  const totalCount = data.practice.length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h2 className="font-serif text-2xl font-semibold">Conjugation</h2>
        {totalCount > 0 && (
          <span className="text-sm text-muted-foreground">
            {correctCount} / {totalCount} correct
          </span>
        )}
      </div>

      {/* Verb tables */}
      {data.verbs.map((verb, i) => (
        <div key={i} className="rounded-2xl border border-border bg-card p-5 sm:p-6">
          <div className="flex items-baseline justify-between mb-3 flex-wrap gap-2">
            <div>
              <h3 className="font-serif text-xl font-semibold">
                {verb.infinitive}
                <span className="ml-2 text-sm text-muted-foreground font-normal">— {verb.translation}</span>
              </h3>
              <Badge variant="outline" className="mt-1 text-[10px] uppercase tracking-wider">{verb.tense}</Badge>
            </div>
            <SpeakButton text={verb.infinitive} size="sm" />
          </div>

          {/* Conjugation table */}
          <div className="overflow-x-auto scroll-elegant">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="bg-primary/10">
                  <th className="text-left p-2.5 font-medium border-b border-border">Pronoun</th>
                  <th className="text-left p-2.5 font-medium border-b border-border">Conjugation</th>
                  <th className="w-10 border-b border-border"></th>
                </tr>
              </thead>
              <tbody>
                {verb.conjugations.map((c, j) => (
                  <tr key={j} className={j % 2 === 0 ? 'bg-card' : 'bg-secondary/30'}>
                    <td className="p-2.5 border-b border-border/50 font-medium">{c.pronoun}</td>
                    <td className="p-2.5 border-b border-border/50">{c.form}</td>
                    <td className="p-2.5 border-b border-border/50">
                      <SpeakButton text={c.form} size="sm" variant="ghost" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Sentence-making rule */}
          <div className="mt-4 rounded-lg bg-accent/15 border border-accent/30 p-3">
            <p className="font-medium text-accent-foreground text-sm mb-2">📝 Sentence-making rule</p>
            <p className="text-sm text-foreground/80">{verb.sentenceRule}</p>
          </div>

          {/* Example sentences */}
          <div className="mt-3 space-y-2">
            <p className="text-xs uppercase tracking-wider text-muted-foreground font-medium">Example sentences</p>
            {verb.sentenceExamples.map((ex, j) => (
              <div key={j} className="rounded-lg bg-secondary/50 p-3 flex items-center gap-3">
                <div className="flex-1">
                  <p className="font-medium">{ex.fr}</p>
                  <p className="text-xs text-muted-foreground">{ex.en}</p>
                </div>
                <SpeakButton text={ex.fr} size="sm" />
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* Practice exercises */}
      {data.practice.length > 0 && (
        <div>
          <h3 className="font-serif text-xl font-semibold mb-4">Conjugation practice</h3>
          <div className="space-y-4">
            {data.practice.map((ex, i) => (
              <ConjugationExerciseCard
                key={ex.id}
                ex={ex}
                index={i}
                result={results[ex.id]}
                onCheck={handleCheck}
              />
            ))}
          </div>

          {/* Summary */}
          {Object.keys(results).length === totalCount && totalCount > 0 && (
            <div className="mt-5 rounded-2xl border border-border bg-card p-5 text-center">
              <p className="font-serif text-3xl font-semibold" style={{ color: correctCount >= totalCount * 0.7 ? '#2D6A4F' : '#B45309' }}>
                {Math.round((correctCount / totalCount) * 100)}%
              </p>
              <p className="mt-1 text-sm text-foreground/70">
                {correctCount === totalCount ? 'Parfait ! Toutes les conjugaisons sont correctes.' :
                 correctCount >= totalCount * 0.7 ? 'Bien joué ! Continuez à pratiquer.' :
                 'Continuez à pratiquer — la conjugaison vient avec la répétition.'}
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setResults({})}
                className="mt-3 gap-1.5"
              >
                <RotateCcw className="h-3.5 w-3.5" /> Reset practice
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ConjugationExerciseCard({
  ex,
  index,
  result,
  onCheck,
}: {
  ex: ConjugationPractice;
  index: number;
  result?: { correct: boolean; userAnswer: string };
  onCheck: (ex: ConjugationPractice, userAnswer: string) => void;
}) {
  const [userInput, setUserInput] = useState('');
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const isAnswered = result !== undefined;

  const handleSubmit = () => {
    if (ex.type === 'multiple_choice') {
      if (selectedOption === null) return;
      onCheck(ex, String(selectedOption));
    } else {
      if (!userInput.trim()) return;
      onCheck(ex, userInput.trim());
    }
  };

  const typeLabels: Record<string, string> = {
    conjugation: 'Conjugate',
    multiple_choice: 'Multiple choice',
    fill_blank: 'Fill in the blank',
    translate_to_fr: 'Translate to French',
    true_false: 'True or false',
  };

  return (
    <div className="rounded-2xl border border-border bg-card p-5">
      <div className="flex items-start gap-3">
        <span className="flex-shrink-0 h-7 w-7 rounded-full bg-primary text-primary-foreground text-xs font-bold flex items-center justify-center mt-0.5">
          {index + 1}
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <Badge variant="outline" className="text-[10px] uppercase tracking-wider gap-1">
              <Zap className="h-3 w-3" /> {typeLabels[ex.type] || ex.type}
            </Badge>
          </div>
          <p className="text-sm font-medium whitespace-pre-line">{ex.prompt}</p>

          {/* Multiple choice */}
          {ex.type === 'multiple_choice' && ex.options && (
            <div className="mt-3 space-y-2">
              {ex.options.map((opt, i) => {
                const isSelected = selectedOption === i;
                const isCorrect = i === ex.answer;
                const showResult = isAnswered;
                return (
                  <button
                    key={i}
                    onClick={() => !isAnswered && setSelectedOption(i)}
                    disabled={isAnswered}
                    className={`w-full text-left p-3 rounded-lg border text-sm transition ${
                      showResult
                        ? isCorrect
                          ? 'border-chart-3 bg-chart-3/10'
                          : isSelected
                          ? 'border-destructive bg-destructive/10'
                          : 'border-border bg-card'
                        : isSelected
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:bg-secondary'
                    }`}
                  >
                    <span className="font-semibold mr-2">{String.fromCharCode(65 + i)}.</span>
                    {opt}
                    {showResult && isCorrect && <CheckCircle2 className="inline h-4 w-4 ml-2 text-chart-3" />}
                    {showResult && isSelected && !isCorrect && <XCircle className="inline h-4 w-4 ml-2 text-destructive" />}
                  </button>
                );
              })}
            </div>
          )}

          {/* Text input */}
          {(ex.type === 'conjugation' || ex.type === 'fill_blank' || ex.type === 'translate_to_fr') && (
            <div className="mt-3">
              <input
                type="text"
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !isAnswered && handleSubmit()}
                disabled={isAnswered}
                placeholder={ex.promptFr || 'Type your answer...'}
                className="w-full p-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          )}

          {!isAnswered && (
            <Button onClick={handleSubmit} size="sm" className="mt-3" disabled={ex.type === 'multiple_choice' ? selectedOption === null : !userInput.trim()}>
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
                    {ex.type === 'multiple_choice' ? ex.options?.[ex.answer as number] : ex.answer}
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

function checkAnswer(ex: ConjugationPractice, userAnswer: string): boolean {
  if (ex.type === 'multiple_choice' || ex.type === 'true_false') {
    return Number(userAnswer) === ex.answer;
  }
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
  const user = normalize(userAnswer);
  if (user === correct) return true;
  if (ex.acceptable) {
    return ex.acceptable.some((a) => normalize(a) === user);
  }
  return false;
}
