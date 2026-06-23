'use client';

import { TrendingUp, Flame, BookOpen, FileText, Award, RotateCcw, Calendar, Target } from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { courses } from '@/lib/courses';
import { mockTests } from '@/lib/mock-tests';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';

export function ProgressDashboard() {
  const xp = useAppStore((s) => s.xp);
  const streak = useAppStore((s) => s.streakDays);
  const completedLessons = useAppStore((s) => s.completedLessons);
  const testResults = useAppStore((s) => s.testResults);
  const resetProgress = useAppStore((s) => s.resetProgress);
  const setView = useAppStore((s) => s.setView);
  const { toast } = useToast();

  const totalLessons = courses.reduce((sum, c) => sum + c.units.reduce((s, u) => s + u.lessons.length, 0), 0);
  const completedCount = completedLessons.length;
  const overallPct = totalLessons > 0 ? Math.round((completedCount / totalLessons) * 100) : 0;

  const avgTestScore = testResults.length > 0
    ? Math.round(testResults.reduce((sum, t) => sum + (t.correctCount / Math.max(t.totalQuestions, 1)) * 100, 0) / testResults.length)
    : 0;

  // Calculate progress by level
  const levelProgress = courses.map((c) => {
    const totalForCourse = c.units.reduce((s, u) => s + u.lessons.length, 0);
    const doneForCourse = completedLessons.filter((l) => l.level === c.level).length;
    const pct = totalForCourse > 0 ? Math.round((doneForCourse / totalForCourse) * 100) : 0;
    const avgScore = completedLessons
      .filter((l) => l.level === c.level)
      .reduce((sum, l) => sum + l.score, 0) / Math.max(doneForCourse, 1);
    return { level: c.level, color: c.color, total: totalForCourse, done: doneForCourse, pct, avgScore: Math.round(avgScore) || 0 };
  });

  // Test results by type
  const testByType = mockTests.map((t) => {
    const results = testResults.filter((r) => r.testType === t.type);
    const avgScore = results.length > 0
      ? Math.round(results.reduce((sum, r) => sum + (r.correctCount / Math.max(r.totalQuestions, 1)) * 100, 0) / results.length)
      : 0;
    return { type: t.type, color: t.color, count: results.length, avgScore, sections: t.sections };
  });

  // Recent activity (last 5)
  const recentActivity = [
    ...completedLessons.map((l) => ({ kind: 'lesson' as const, ...l, sortDate: l.completedAt })),
    ...testResults.map((t) => ({ kind: 'test' as const, ...t, sortDate: t.takenAt })),
  ].sort((a, b) => new Date(b.sortDate).getTime() - new Date(a.sortDate).getTime()).slice(0, 8);

  const handleReset = () => {
    if (confirm('Reset all progress? This cannot be undone.')) {
      resetProgress();
      toast({ title: 'Progress reset', description: 'You\'re starting fresh!' });
    }
  };

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Your Journey</p>
        <h1 className="font-serif text-3xl sm:text-4xl font-semibold">Progress</h1>
        <p className="text-foreground/70">Track your streaks, scores, and the road from A1 to B2.</p>
      </header>

      {/* Top stats */}
      <section className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatBox icon={<Flame className="h-5 w-5" />} value={streak} label="Day streak" tone="accent" />
        <StatBox icon={<Award className="h-5 w-5" />} value={xp} label="Total XP" tone="primary" />
        <StatBox icon={<BookOpen className="h-5 w-5" />} value={`${completedCount}/${totalLessons}`} label="Lessons" tone="sage" />
        <StatBox icon={<TrendingUp className="h-5 w-5" />} value={`${avgTestScore}%`} label="Avg test score" tone="terracotta" />
      </section>

      {/* Overall progress ring */}
      <section className="rounded-2xl border border-border bg-card p-6 sm:p-8">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h2 className="font-serif text-2xl font-semibold">Overall completion</h2>
            <p className="text-sm text-foreground/70 mt-1">Across all four CEFR levels</p>
          </div>
          <div className="relative h-24 w-24 sm:h-28 sm:w-28">
            <svg viewBox="0 0 100 100" className="h-full w-full -rotate-90">
              <circle cx="50" cy="50" r="44" fill="none" stroke="var(--secondary)" strokeWidth="8" />
              <circle
                cx="50" cy="50" r="44" fill="none"
                stroke="var(--primary)" strokeWidth="8"
                strokeLinecap="round"
                strokeDasharray={`${(overallPct / 100) * 276.46} 276.46`}
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="font-serif text-2xl font-bold">{overallPct}%</span>
            </div>
          </div>
        </div>
      </section>

      {/* By level */}
      <section>
        <h2 className="font-serif text-2xl font-semibold mb-4">By level</h2>
        <div className="space-y-3">
          {levelProgress.map((lp) => (
            <div key={lp.level} className="rounded-xl border border-border bg-card p-4">
              <div className="flex items-baseline justify-between mb-2">
                <div className="flex items-baseline gap-2">
                  <span className="font-serif text-2xl font-bold" style={{ color: lp.color }}>{lp.level}</span>
                  <span className="text-sm text-muted-foreground">{lp.done} / {lp.total} lessons</span>
                </div>
                <div className="flex items-center gap-3 text-sm">
                  {lp.avgScore > 0 && (
                    <span className="text-muted-foreground">avg score: <span className="font-medium text-foreground">{lp.avgScore}%</span></span>
                  )}
                  <span className="font-semibold" style={{ color: lp.color }}>{lp.pct}%</span>
                </div>
              </div>
              <div className="h-2 rounded-full bg-secondary overflow-hidden">
                <div className="h-full rounded-full transition-all" style={{ width: `${lp.pct}%`, background: lp.color }} />
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Test results */}
      {testByType.some((t) => t.count > 0) && (
        <section>
          <h2 className="font-serif text-2xl font-semibold mb-4">Mock test performance</h2>
          <div className="grid sm:grid-cols-2 gap-3">
            {testByType.filter((t) => t.count > 0).map((t) => (
              <div key={t.type} className="rounded-xl border border-border bg-card p-4">
                <div className="flex items-baseline justify-between">
                  <span className="font-serif text-2xl font-bold" style={{ color: t.color }}>{t.type}</span>
                  <span className="text-sm text-muted-foreground">{t.count} attempts</span>
                </div>
                <p className="mt-2 text-sm text-foreground/70">Average score</p>
                <p className="font-serif text-3xl font-semibold mt-1" style={{ color: t.color }}>{t.avgScore}%</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Recent activity */}
      {recentActivity.length > 0 ? (
        <section>
          <h2 className="font-serif text-2xl font-semibold mb-4">Recent activity</h2>
          <div className="rounded-2xl border border-border bg-card divide-y divide-border">
            {recentActivity.map((item, i) => (
              <div key={i} className="p-4 flex items-center gap-3">
                <div className={`flex-shrink-0 h-9 w-9 rounded-xl flex items-center justify-center ${item.kind === 'lesson' ? 'bg-chart-3/15' : 'bg-accent/30'}`}>
                  {item.kind === 'lesson' ? <BookOpen className="h-4 w-4 text-chart-3" /> : <FileText className="h-4 w-4 text-accent-foreground" />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">
                    {item.kind === 'lesson'
                      ? `Completed a ${item.level} lesson`
                      : `${item.testType} · ${item.section.replace(/_/g, ' ')}`
                    }
                  </p>
                  <p className="text-xs text-muted-foreground flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {new Date(item.sortDate).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-semibold" style={{ color: item.kind === 'lesson' ? '#2D6A4F' : '#B45309' }}>
                    {item.kind === 'lesson' ? `${item.score}%` : `${item.correctCount}/${item.totalQuestions}`}
                  </p>
                  <p className="text-xs text-muted-foreground">{item.kind === 'lesson' ? 'score' : 'correct'}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      ) : (
        <section className="rounded-2xl border border-dashed border-border bg-card/50 p-8 text-center">
          <Target className="h-10 w-10 text-muted-foreground mx-auto" />
          <p className="mt-3 font-serif text-lg font-semibold">No activity yet</p>
          <p className="text-sm text-foreground/70 mt-1">Complete a lesson or take a mock test to see your progress here.</p>
          <div className="mt-4 flex gap-2 justify-center">
            <Button onClick={() => setView({ kind: 'courses' })}>Start a lesson</Button>
            <Button variant="outline" onClick={() => setView({ kind: 'mock-tests' })}>Take a test</Button>
          </div>
        </section>
      )}

      {/* Reset */}
      <section className="rounded-2xl border border-destructive/30 bg-destructive/5 p-5 flex items-center justify-between gap-3">
        <div>
          <p className="font-medium text-sm">Reset all progress</p>
          <p className="text-xs text-foreground/60">This will erase your streak, XP, completed lessons, and test scores.</p>
        </div>
        <Button variant="outline" size="sm" onClick={handleReset} className="gap-1.5 text-destructive border-destructive/40 hover:bg-destructive/10">
          <RotateCcw className="h-3.5 w-3.5" /> Reset
        </Button>
      </section>
    </div>
  );
}

function StatBox({ icon, value, label, tone }: { icon: React.ReactNode; value: string | number; label: string; tone: 'primary' | 'accent' | 'sage' | 'terracotta' }) {
  const tones: Record<string, string> = {
    primary: 'text-primary bg-primary/10',
    accent: 'text-accent-foreground bg-accent/30',
    sage: 'text-foreground bg-chart-3/15',
    terracotta: 'text-foreground bg-chart-4/15',
  };
  return (
    <div className="rounded-2xl border border-border bg-card p-4 sm:p-5">
      <div className={`inline-flex h-9 w-9 items-center justify-center rounded-xl ${tones[tone]}`}>
        {icon}
      </div>
      <p className="mt-3 font-serif text-2xl sm:text-3xl font-semibold text-foreground">{value}</p>
      <p className="text-xs sm:text-sm text-muted-foreground">{label}</p>
    </div>
  );
}
