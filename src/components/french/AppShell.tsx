'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { Home, BookOpen, Mic, FileText, TrendingUp, Settings, X, Languages } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAppStore } from '@/lib/store';
import { Dashboard } from './Dashboard';
import { CourseList } from './CourseList';
import { LessonView } from './LessonView';
import { AIConversation } from './AIConversation';
import { MockTestHub } from './MockTestHub';
import { MockTestRunner } from './MockTestRunner';
import { ProgressDashboard } from './ProgressDashboard';
import { SettingsPanel } from './SettingsPanel';
import { Translation } from './Translation';

type NavTab = 'home' | 'courses' | 'talk' | 'translate' | 'tests' | 'progress';

const navItems: { id: NavTab; label: string; icon: typeof Home }[] = [
  { id: 'home', label: 'Home', icon: Home },
  { id: 'courses', label: 'Courses', icon: BookOpen },
  { id: 'talk', label: 'Talk', icon: Mic },
  { id: 'translate', label: 'Translate', icon: Languages },
  { id: 'tests', label: 'Mock Tests', icon: FileText },
  { id: 'progress', label: 'Progress', icon: TrendingUp },
];

function deriveTab(viewKind: string): NavTab {
  if (viewKind === 'dashboard') return 'home';
  if (viewKind === 'courses' || viewKind === 'lesson') return 'courses';
  if (viewKind === 'conversation') return 'talk';
  if (viewKind === 'translate') return 'translate';
  if (viewKind === 'mock-tests' || viewKind === 'test-runner') return 'tests';
  if (viewKind === 'progress') return 'progress';
  return 'home';
}

export function AppShell() {
  const view = useAppStore((s) => s.view);
  const setView = useAppStore((s) => s.setView);
  const hydrateFromServer = useAppStore((s) => s.hydrateFromServer);
  const hydratedFromServer = useAppStore((s) => s.hydratedFromServer);
  const [showSettings, setShowSettings] = useState(false);
  const { data: session } = useSession();

  // On mount, hydrate progress from server (so each user sees only their own data)
  useEffect(() => {
    if (hydratedFromServer) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch('/api/progress', { cache: 'no-store' });
        if (!res.ok) return;
        const data = await res.json();
        if (cancelled) return;
        const completedLessons = (data.lessons ?? [])
          .filter((l: { status?: string }) => l.status === 'completed')
          .map((l: { lessonId: string; courseLevel: CourseLevel; unitId: string; score: number; completedAt: string | Date }) => ({
            lessonId: l.lessonId,
            level: l.courseLevel,
            unitId: l.unitId,
            score: l.score,
            completedAt: typeof l.completedAt === 'string' ? l.completedAt : new Date(l.completedAt).toISOString(),
          }));
        const testResults = (data.tests ?? []).map((t: { id: string; testType: 'TEF' | 'TCF'; section: string; score: number; totalQuestions: number; correctCount: number; durationSec: number; takenAt: string | Date }) => ({
          id: t.id,
          testType: t.testType,
          section: t.section,
          score: t.score,
          total: t.totalQuestions,
          correctCount: t.correctCount,
          totalQuestions: t.totalQuestions,
          durationSec: t.durationSec,
          takenAt: typeof t.takenAt === 'string' ? t.takenAt : new Date(t.takenAt).toISOString(),
        }));
        hydrateFromServer({ completedLessons, testResults });
      } catch (e) {
        console.error('Could not hydrate from server:', e);
      }
    })();
    return () => { cancelled = true; };
  }, [hydrateFromServer, hydratedFromServer]);

  const activeTab = deriveTab(view.kind);

  const handleTabClick = (tab: NavTab) => {
    if (tab === 'home') setView({ kind: 'dashboard' });
    else if (tab === 'courses') setView({ kind: 'courses' });
    else if (tab === 'talk') setView({ kind: 'conversation' });
    else if (tab === 'translate') setView({ kind: 'translate' });
    else if (tab === 'tests') setView({ kind: 'mock-tests' });
    else if (tab === 'progress') setView({ kind: 'progress' });
  };

  const renderContent = () => {
    switch (view.kind) {
      case 'dashboard':
        return <Dashboard />;
      case 'courses':
        return <CourseList />;
      case 'lesson':
        return <LessonView level={view.level} unitId={view.unitId} lessonId={view.lessonId} />;
      case 'conversation':
        return <AIConversation />;
      case 'translate':
        return <Translation />;
      case 'mock-tests':
        return <MockTestHub />;
      case 'test-runner':
        return <MockTestRunner testType={view.testType} section={view.section} />;
      case 'progress':
        return <ProgressDashboard />;
      default:
        return <Dashboard />;
    }
  };

  const userDisplayName = session?.user?.name || session?.user?.email?.split('@')[0] || 'Learner';

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <header className="sticky top-0 z-40 backdrop-blur-xl bg-background/85 border-b border-border/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
          <button
            onClick={() => handleTabClick('home')}
            className="flex items-center gap-2.5 group"
            aria-label="Parlez home"
          >
            <div className="h-9 w-9 rounded-xl bg-primary flex items-center justify-center shadow-sm">
              <span className="font-serif italic text-xl font-bold text-primary-foreground">P</span>
            </div>
            <div className="hidden sm:block text-left">
              <div className="font-serif text-xl font-semibold text-foreground leading-none">Parlez</div>
              <div className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">French, beautifully</div>
            </div>
          </button>

          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => handleTabClick(item.id)}
                className={`px-3.5 py-2 rounded-full text-sm font-medium transition-all flex items-center gap-1.5 ${
                  activeTab === item.id
                    ? 'bg-primary text-primary-foreground shadow-sm'
                    : 'text-foreground/70 hover:text-foreground hover:bg-secondary'
                }`}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </button>
            ))}
          </nav>

          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowSettings(true)}
              className="gap-2 rounded-full"
            >
              <span className="hidden sm:inline text-sm text-muted-foreground max-w-[140px] truncate">{userDisplayName}</span>
              <Settings className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <nav className="md:hidden border-t border-border/40 overflow-x-auto scroll-elegant">
          <div className="flex items-center gap-1 px-3 py-2 min-w-max">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => handleTabClick(item.id)}
                className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all flex items-center gap-1.5 whitespace-nowrap ${
                  activeTab === item.id
                    ? 'bg-primary text-primary-foreground'
                    : 'text-foreground/70 hover:bg-secondary'
                }`}
              >
                <item.icon className="h-3.5 w-3.5" />
                {item.label}
              </button>
            ))}
          </div>
        </nav>
      </header>

      <main className="flex-1 w-full">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
          <div
            key={view.kind + (view.kind === 'lesson' ? view.lessonId : '') + (view.kind === 'test-runner' ? view.section : '')}
            className="fade-in-up"
          >
            {renderContent()}
          </div>
        </div>
      </main>

      <footer className="mt-auto border-t border-border/60 bg-card/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-muted-foreground">
          <p>
            <span className="font-serif italic text-foreground/80">Parlez</span> — A free French learning companion · CEFR A1 to B2
          </p>
          <p className="flex items-center gap-3">
            <span>Voice powered by your browser</span>
            <span className="hidden sm:inline">·</span>
            <span className="hidden sm:inline">AI tutor powered by Z.ai</span>
          </p>
        </div>
      </footer>

      {showSettings && (
        <div className="fixed inset-0 z-50 flex justify-end" role="dialog" aria-modal="true">
          <div
            className="absolute inset-0 bg-black/30 backdrop-blur-sm"
            onClick={() => setShowSettings(false)}
          />
          <div className="relative w-full sm:max-w-md h-full bg-background shadow-2xl overflow-y-auto scroll-elegant">
            <div className="sticky top-0 bg-background/95 backdrop-blur border-b border-border px-5 py-4 flex items-center justify-between">
              <h2 className="font-serif text-xl font-semibold">Settings</h2>
              <Button variant="ghost" size="icon" onClick={() => setShowSettings(false)} aria-label="Close settings">
                <X className="h-4 w-4" />
              </Button>
            </div>
            <SettingsPanel />
          </div>
        </div>
      )}
    </div>
  );
}
