'use client';

import { useState } from 'react';
import { signIn } from 'next-auth/react';
import { Mail, Lock, User as UserIcon, ArrowRight, Sparkles, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';

interface AuthScreenProps {
  mode: 'login' | 'signup';
  onModeChange: (mode: 'login' | 'signup') => void;
  onSuccess: () => void | Promise<void>;
}

export function AuthScreen({ mode, onModeChange, onSuccess }: AuthScreenProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const isSignup = mode === 'signup';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      toast({ title: 'Missing fields', description: 'Please enter email and password.', variant: 'destructive' });
      return;
    }
    setLoading(true);

    try {
      if (isSignup) {
        // 1. Create the account
        const res = await fetch('/api/auth/signup', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password, name }),
        });
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.error || 'Signup failed');
        }
        // 2. Sign in immediately with redirect:false so we can show toast
        const result = await signIn('credentials', {
          email,
          password,
          redirect: false,
        });
        if (result?.error) {
          throw new Error(result.error);
        }
        toast({ title: 'Welcome to Parlez!', description: 'Your account is ready. Bon courage !' });
        // 3. Hard navigate to '/' (replaces history, full page reload picks up cookie)
        //    Small delay so the toast is visible before navigation.
        setTimeout(() => {
          window.location.replace('/');
        }, 400);
      } else {
        const result = await signIn('credentials', {
          email,
          password,
          redirect: false,
        });
        if (result?.error) {
          throw new Error(result.error);
        }
        toast({ title: `Bon retour !`, description: 'You\'re logged in.' });
        setTimeout(() => {
          window.location.replace('/');
        }, 400);
      }
    } catch (error) {
      const msg = error instanceof Error ? error.message : 'Authentication failed';
      toast({ title: 'Authentication failed', description: msg, variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 sm:p-6">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex h-14 w-14 rounded-2xl bg-primary items-center justify-center shadow-md mb-3">
            <span className="font-serif italic text-2xl font-bold text-primary-foreground">P</span>
          </div>
          <h1 className="font-serif text-3xl font-semibold">Parlez</h1>
          <p className="text-sm text-muted-foreground mt-1 italic">French, beautifully</p>
        </div>

        <div className="rounded-2xl border border-border bg-card p-6 sm:p-8 shadow-sm">
          <div className="flex gap-1 p-1 bg-secondary/60 rounded-full mb-6">
            <button
              type="button"
              onClick={() => onModeChange('login')}
              className={`flex-1 py-2 rounded-full text-sm font-medium transition ${
                !isSignup ? 'bg-card shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              Log in
            </button>
            <button
              type="button"
              onClick={() => onModeChange('signup')}
              className={`flex-1 py-2 rounded-full text-sm font-medium transition ${
                isSignup ? 'bg-card shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              Sign up
            </button>
          </div>

          <h2 className="font-serif text-2xl font-semibold mb-1">
            {isSignup ? 'Create your account' : 'Welcome back'}
          </h2>
          <p className="text-sm text-muted-foreground mb-5">
            {isSignup
              ? 'Your progress is saved to your account. Share Parlez with your classmates!'
              : 'Log in to continue your French journey.'}
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {isSignup && (
              <div className="space-y-1.5">
                <Label htmlFor="name" className="text-xs uppercase tracking-wider text-muted-foreground">Name (optional)</Label>
                <div className="relative">
                  <UserIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="name"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Marie Dupont"
                    className="pl-9"
                    autoComplete="name"
                  />
                </div>
              </div>
            )}

            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-xs uppercase tracking-wider text-muted-foreground">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="pl-9"
                  autoComplete="email"
                  required
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="password" className="text-xs uppercase tracking-wider text-muted-foreground">
                Password {isSignup && <span className="normal-case">(min 6 characters)</span>}
              </Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="pl-9"
                  autoComplete={isSignup ? 'new-password' : 'current-password'}
                  required
                  minLength={6}
                />
              </div>
            </div>

            <Button type="submit" disabled={loading} className="w-full gap-2" size="lg">
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" /> Please wait…
                </>
              ) : (
                <>
                  {isSignup ? 'Create account' : 'Log in'}
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </Button>
          </form>

          <div className="mt-5 text-center text-xs text-muted-foreground">
            {isSignup ? (
              <>Already have an account? <button onClick={() => onModeChange('login')} className="text-primary font-medium hover:underline">Log in</button></>
            ) : (
              <>New here? <button onClick={() => onModeChange('signup')} className="text-primary font-medium hover:underline">Create an account</button></>
            )}
          </div>
        </div>

        <div className="mt-6 flex items-start gap-2 text-xs text-muted-foreground px-4">
          <Sparkles className="h-3.5 w-3.5 mt-0.5 flex-shrink-0 text-accent" />
          <p>
            Free forever · A1 to B2 courses · AI French tutor with voice · TEF &amp; TCF mock tests · Your progress stays private to your account.
          </p>
        </div>
      </div>
    </div>
  );
}
