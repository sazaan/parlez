'use client';

import { useState } from 'react';
import { useSession, signOut } from 'next-auth/react';
import { AppShell } from '@/components/french/AppShell';
import { AuthScreen } from '@/components/auth/AuthScreen';
import { LogOut } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function Home() {
  const { data: session, status } = useSession();
  const [authMode, setAuthMode] = useState<'login' | 'signup'>('login');

  // Show a brief loading state while session is being fetched
  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="inline-flex h-14 w-14 rounded-2xl bg-primary items-center justify-center shadow-md mb-3">
            <span className="font-serif italic text-2xl font-bold text-primary-foreground">P</span>
          </div>
          <p className="text-sm text-muted-foreground">Loading Parlez…</p>
        </div>
      </div>
    );
  }

  // Not logged in — show auth screen.
  // After successful login, AuthScreen does window.location.replace('/') which
  // forces a full page reload with the new session cookie, so useSession()
  // will pick up the authenticated session on the next render.
  if (!session) {
    return <AuthScreen mode={authMode} onModeChange={setAuthMode} onSuccess={() => {}} />;
  }

  return (
    <div className="relative">
      <AppShell />
      {/* Floating logout button — bottom-left to avoid conflict with mobile nav */}
      <Button
        variant="outline"
        size="sm"
        onClick={async () => {
          await signOut({ redirect: false });
          // Hard reload to guarantee the auth context picks up the cleared cookie.
          window.location.replace('/');
        }}
        className="fixed bottom-4 left-4 z-30 gap-1.5 bg-card/95 backdrop-blur shadow-md opacity-70 hover:opacity-100 transition"
        aria-label="Log out"
        title={`Logged in as ${session.user?.email}`}
      >
        <LogOut className="h-3.5 w-3.5" />
        <span className="hidden sm:inline">Log out</span>
      </Button>
    </div>
  );
}
