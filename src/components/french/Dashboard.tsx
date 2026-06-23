'use client';

import { Sparkles, Mic, BookOpen, FileText, TrendingUp, Flame, ArrowRight, Quote } from 'lucide-react';
import { useSession } from 'next-auth/react';
import { useAppStore } from '@/lib/store';
import { courses } from '@/lib/courses';
import { conversationScenarios } from '@/lib/courses';
import { mockTests } from '@/lib/mock-tests';

export function Dashboard() {
  const { data: session } = useSession();
  const setView = useAppStore((s) => s.setView);
  const xp = useAppStore((s) => s.xp);
  const streak = useAppStore((s) => s.streakDays);
  const completedLessons = useAppStore((s) => s.completedLessons);
  const testResults = useAppStore((s) => s.testResults);

  const learnerName = session?.user?.name || session?.user?.email?.split('@')[0] || 'Learner';

  const totalLessons = courses.reduce((sum, c) => sum + c.units.reduce((s, u) => s + u.lessons.length, 0), 0);
  const completedCount = completedLessons.length;
  const progressPercent = totalLessons > 0 ? Math.round((completedCount / totalLessons) * 100) : 0;
  const greeting = (() => {
    const h = new Date().getHours();
    if (h < 12) return 'Bonjour';
    if (h < 18) return 'Bon après-midi';
    return 'Bonsoir';
  })();

  const dailyQuote = {
    fr: 'On ne voit bien qu\'avec le cœur. L\'essentiel est invisible pour les yeux.',
    author: 'Antoine de Saint-Exupéry',
    work: 'Le Petit Prince',
  };

  return (
    <div className="space-y-8">
      {/* Hero */}
      <section className="relative overflow-hidden rounded-3xl border border-border bg-gradient-to-br from-card via-card to-secondary/40 p-6 sm:p-10 shadow-sm">
        <div className="absolute -top-12 -right-12 h-48 w-48 rounded-full bg-accent/20 blur-3xl" />
        <div className="absolute -bottom-16 -left-12 h-48 w-48 rounded-full bg-primary/10 blur-3xl" />
        <div className="relative">
          <p className="text-sm uppercase tracking-[0.18em] text-muted-foreground font-medium">{greeting}, {learnerName}</p>
          <h1 className="mt-2 font-serif text-3xl sm:text-5xl font-semibold leading-tight text-foreground">
            Let&apos;s learn French, <span className="italic text-primary">beautifully</span>.
          </h1>
          <p className="mt-3 max-w-xl text-foreground/70 text-base sm:text-lg">
            A complete, free companion for learning French. Talk to your AI tutor, work through A1–B2, and prepare for TEF &amp; TCF.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <button
              onClick={() => setView({ kind: 'conversation' })}
              className="inline-flex items-center gap-2 rounded-full bg-primary text-primary-foreground px-5 py-2.5 text-sm font-medium shadow hover:bg-primary/90 transition"
            >
              <Mic className="h-4 w-4" /> Talk to your tutor
            </button>
            <button
              onClick={() => setView({ kind: 'courses' })}
              className="inline-flex items-center gap-2 rounded-full bg-card border border-border px-5 py-2.5 text-sm font-medium hover:bg-secondary transition"
            >
              <BookOpen className="h-4 w-4" /> Browse lessons
            </button>
          </div>
        </div>
      </section>

      {/* Stats row */}
      <section className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
        <StatCard icon={<Flame className="h-5 w-5" />} value={streak} label="Day streak" tone="accent" />
        <StatCard icon={<Sparkles className="h-5 w-5" />} value={xp} label="XP earned" tone="primary" />
        <StatCard icon={<BookOpen className="h-5 w-5" />} value={`${completedCount}/${totalLessons}`} label="Lessons done" tone="sage" />
        <StatCard icon={<TrendingUp className="h-5 w-5" />} value={`${progressPercent}%`} label="Overall progress" tone="terracotta" />
      </section>

      {/* Quick actions */}
      <section>
        <h2 className="font-serif text-2xl font-semibold mb-4">Continue learning</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <ActionCard
            title="Talk with AI Tutor"
            description="Speak French out loud — your tutor replies with voice. Pick a scenario and dive in."
            cta="Start a conversation"
            icon={<Mic className="h-5 w-5" />}
            tone="primary"
            onClick={() => setView({ kind: 'conversation' })}
          />
          <ActionCard
            title="Browse courses"
            description="From A1 greetings to B2 debates — every CEFR level, with full lessons and activity workbooks."
            cta="Open courses"
            icon={<BookOpen className="h-5 w-5" />}
            tone="sage"
            onClick={() => setView({ kind: 'courses' })}
          />
          <ActionCard
            title="Take a mock test"
            description="Practice TEF and TCF — reading, listening, and language structures with instant scoring."
            cta="Start a test"
            icon={<FileText className="h-5 w-5" />}
            tone="accent"
            onClick={() => setView({ kind: 'mock-tests' })}
          />
        </div>
      </section>

      {/* Levels overview */}
      <section>
        <div className="flex items-baseline justify-between mb-4">
          <h2 className="font-serif text-2xl font-semibold">Your CEFR path</h2>
          <button
            onClick={() => setView({ kind: 'courses' })}
            className="text-sm text-primary hover:underline flex items-center gap-1"
          >
            See all <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {courses.map((c) => {
            const totalForCourse = c.units.reduce((s, u) => s + u.lessons.length, 0);
            const doneForCourse = completedLessons.filter((l) => l.level === c.level).length;
            const pct = totalForCourse > 0 ? Math.round((doneForCourse / totalForCourse) * 100) : 0;
            return (
              <button
                key={c.level}
                onClick={() => setView({ kind: 'courses' })}
                className="group text-left rounded-2xl border border-border bg-card p-5 hover:shadow-md hover:border-foreground/20 transition"
              >
                <div className="flex items-baseline justify-between">
                  <span
                    className="font-serif text-3xl font-bold"
                    style={{ color: c.color }}
                  >
                    {c.level}
                  </span>
                  <span className="text-xs text-muted-foreground uppercase tracking-wider">{c.book}</span>
                </div>
                <p className="mt-2 text-sm text-foreground/70 line-clamp-2">{c.title}</p>
                <div className="mt-4 h-1.5 rounded-full bg-secondary overflow-hidden">
                  <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, background: c.color }} />
                </div>
                <p className="mt-1.5 text-xs text-muted-foreground">{doneForCourse} / {totalForCourse} lessons · {pct}%</p>
              </button>
            );
          })}
        </div>
      </section>

      {/* Conversation scenarios preview */}
      <section>
        <h2 className="font-serif text-2xl font-semibold mb-4">Try a conversation scenario</h2>
        <div className="flex flex-wrap gap-2">
          {conversationScenarios.slice(0, 8).map((s) => (
            <button
              key={s.id}
              onClick={() => setView({ kind: 'conversation' })}
              className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2 text-sm hover:bg-secondary transition"
            >
              <span className="text-lg">{s.icon}</span>
              <span className="font-medium">{s.labelFr}</span>
              <span className="text-xs text-muted-foreground hidden sm:inline">— {s.label}</span>
            </button>
          ))}
        </div>
      </section>

      {/* Recent tests */}
      {testResults.length > 0 && (
        <section>
          <h2 className="font-serif text-2xl font-semibold mb-4">Recent test results</h2>
          <div className="rounded-2xl border border-border bg-card divide-y divide-border">
            {testResults.slice(0, 4).map((t) => (
              <div key={t.id} className="flex items-center justify-between p-4">
                <div>
                  <p className="font-medium">{t.testType} · {t.section}</p>
                  <p className="text-xs text-muted-foreground">{new Date(t.takenAt).toLocaleDateString()}</p>
                </div>
                <div className="text-right">
                  <p className="font-serif text-xl font-semibold text-primary">
                    {t.correctCount}/{t.totalQuestions}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {Math.round((t.correctCount / Math.max(t.totalQuestions, 1)) * 100)}%
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Daily quote */}
      <section className="rounded-2xl border border-border bg-gradient-to-br from-primary/5 to-accent/10 p-6 sm:p-8">
        <Quote className="h-6 w-6 text-accent mb-3" />
        <p className="font-serif italic text-xl sm:text-2xl text-foreground/90 leading-snug">
          “{dailyQuote.fr}”
        </p>
        <p className="mt-3 text-sm text-muted-foreground">
          — {dailyQuote.author}, <em>{dailyQuote.work}</em>
        </p>
      </section>

      {/* Mock test intro */}
      <section className="grid sm:grid-cols-2 gap-4">
        {mockTests.map((t) => (
          <button
            key={t.type}
            onClick={() => setView({ kind: 'mock-tests' })}
            className="text-left rounded-2xl border border-border bg-card p-5 hover:shadow-md hover:border-foreground/20 transition"
          >
            <div className="flex items-baseline justify-between">
              <span
                className="font-serif text-2xl font-bold"
                style={{ color: t.color }}
              >
                {t.name}
              </span>
              <span className="text-xs text-muted-foreground">{t.sections.length} sections</span>
            </div>
            <p className="mt-2 text-sm text-foreground/70 line-clamp-2">{t.fullName}</p>
            <p className="mt-3 text-xs text-muted-foreground line-clamp-2">Used for: {t.usedFor}</p>
          </button>
        ))}
      </section>
    </div>
  );
}

function StatCard({ icon, value, label, tone }: { icon: React.ReactNode; value: string | number; label: string; tone: 'primary' | 'accent' | 'sage' | 'terracotta' }) {
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

function ActionCard({ title, description, cta, icon, tone, onClick }: { title: string; description: string; cta: string; icon: React.ReactNode; tone: 'primary' | 'accent' | 'sage'; onClick: () => void }) {
  const tones: Record<string, string> = {
    primary: 'bg-primary/10 text-primary',
    accent: 'bg-accent/30 text-accent-foreground',
    sage: 'bg-chart-3/15 text-foreground',
  };
  return (
    <button
      onClick={onClick}
      className="group text-left rounded-2xl border border-border bg-card p-5 hover:shadow-md hover:border-foreground/20 transition"
    >
      <div className={`inline-flex h-10 w-10 items-center justify-center rounded-xl ${tones[tone]}`}>
        {icon}
      </div>
      <h3 className="mt-3 font-serif text-lg font-semibold">{title}</h3>
      <p className="mt-1.5 text-sm text-foreground/70">{description}</p>
      <p className="mt-3 text-sm font-medium text-primary flex items-center gap-1">
        {cta} <ArrowRight className="h-3.5 w-3.5 group-hover:translate-x-0.5 transition" />
      </p>
    </button>
  );
}
