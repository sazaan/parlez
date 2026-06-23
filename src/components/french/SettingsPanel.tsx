'use client';

import { useState, useEffect } from 'react';
import { useSession, signOut } from 'next-auth/react';
import { Volume2, Mic, Info, LogOut, User as UserIcon, Mail } from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { useTTSSupported, useSTTSupported, loadFrenchVoices } from '@/lib/voice/browser-voice';

export function SettingsPanel() {
  const { data: session } = useSession();
  const voiceRate = useAppStore((s) => s.voiceRate);
  const setVoiceRate = useAppStore((s) => s.setVoiceRate);
  const resetProgress = useAppStore((s) => s.resetProgress);
  const { toast } = useToast();

  const [rate, setRate] = useState(voiceRate);
  const ttsSupported = useTTSSupported();
  const sttSupported = useSTTSupported();
  const [voicesCount, setVoicesCount] = useState(0);

  useEffect(() => {
    if (!ttsSupported) return;
    loadFrenchVoices().then((v) => setVoicesCount(v.length));
  }, [ttsSupported]);

  const handleSave = () => {
    setVoiceRate(rate);
    toast({ title: 'Settings saved', description: 'Your preferences have been updated.' });
  };

  const handleSignOut = async () => {
    await signOut({ redirect: false });
    toast({ title: 'Signed out', description: 'See you soon!' });
    // Hard reload to guarantee the auth context picks up the cleared cookie.
    window.location.reload();
  };

  return (
    <div className="p-5 space-y-7">
      {/* Account */}
      <section>
        <h3 className="font-serif text-lg font-semibold mb-3 flex items-center gap-2">
          <UserIcon className="h-4 w-4" /> Your account
        </h3>
        <div className="space-y-2 text-sm">
          {session?.user?.name && (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-secondary/50">
              <UserIcon className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground text-xs uppercase tracking-wider">Name</span>
              <span className="ml-auto font-medium">{session.user.name}</span>
            </div>
          )}
          <div className="flex items-center gap-2 p-3 rounded-lg bg-secondary/50">
            <Mail className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground text-xs uppercase tracking-wider">Email</span>
            <span className="ml-auto font-medium truncate max-w-[180px]">{session?.user?.email}</span>
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleSignOut}
          className="mt-3 gap-1.5 text-destructive border-destructive/40 hover:bg-destructive/10 w-full"
        >
          <LogOut className="h-3.5 w-3.5" /> Log out
        </Button>
      </section>

      {/* Voice speed */}
      <section>
        <h3 className="font-serif text-lg font-semibold mb-3 flex items-center gap-2">
          <Volume2 className="h-4 w-4" /> Voice speed
        </h3>
        <p className="text-xs text-muted-foreground mb-3">Adjust how fast French audio plays back (slower helps beginners).</p>
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground w-12">Slow</span>
          <Slider
            value={[rate]}
            onValueChange={(v) => setRate(v[0])}
            min={0.5}
            max={1.5}
            step={0.05}
            className="flex-1"
          />
          <span className="text-xs text-muted-foreground w-12 text-right">Fast</span>
        </div>
        <p className="text-xs text-muted-foreground mt-1.5 text-center">Current: {rate.toFixed(2)}× (default 0.95)</p>
        <Button onClick={handleSave} size="sm" className="mt-3 w-full">Save settings</Button>
      </section>

      {/* Voice support info */}
      <section>
        <h3 className="font-serif text-lg font-semibold mb-3 flex items-center gap-2">
          <Mic className="h-4 w-4" /> Voice support
        </h3>
        <div className="space-y-2 text-sm">
          <div className="flex items-center justify-between p-3 rounded-lg bg-secondary/50">
            <span>Text-to-speech (playback)</span>
            <span className={`text-xs font-medium ${ttsSupported ? 'text-chart-3' : 'text-destructive'}`}>
              {ttsSupported ? 'Available' : 'Not available'}
            </span>
          </div>
          <div className="flex items-center justify-between p-3 rounded-lg bg-secondary/50">
            <span>Speech recognition (voice input)</span>
            <span className={`text-xs font-medium ${sttSupported ? 'text-chart-3' : 'text-destructive'}`}>
              {sttSupported ? 'Available' : 'Not available'}
            </span>
          </div>
          {ttsSupported && (
            <div className="flex items-center justify-between p-3 rounded-lg bg-secondary/50">
              <span>French voices found</span>
              <span className="text-xs font-medium">{voicesCount}</span>
            </div>
          )}
        </div>
        {(!ttsSupported || !sttSupported) && (
          <div className="mt-3 rounded-lg bg-accent/15 border border-accent/30 p-3 text-xs flex gap-2">
            <Info className="h-4 w-4 flex-shrink-0 mt-0.5" />
            <p className="text-foreground/80">
              For best voice support, use <strong>Google Chrome</strong> or <strong>Microsoft Edge</strong>. Other browsers may have limited or no French voice features.
            </p>
          </div>
        )}
      </section>

      {/* About */}
      <section>
        <h3 className="font-serif text-lg font-semibold mb-3">About Parlez</h3>
        <div className="text-xs text-foreground/70 space-y-2">
          <p>
            <strong>Parlez</strong> is a free, voice-powered French learning app. The curriculum covers CEFR levels A1 (beginner) through B2 (upper-intermediate), with detailed lessons on vocabulary, grammar, dialogues, exercises, and cultural notes.
          </p>
          <p>
            The AI tutor adapts to your level — speaking slowly with simple words for A1, and using nuanced grammar and abstract topics at B2. Voice features use your browser&apos;s built-in speech capabilities (free, no API keys).
          </p>
          <p>
            Mock tests for TEF (Canadian immigration) and TCF (French nationality) help you prepare for official exams.
          </p>
          <p className="pt-2 border-t border-border mt-3">
            <strong>Account &amp; privacy:</strong> Your progress is saved to your account and is private to you. Other users (including your classmates) cannot see your data.
          </p>
        </div>
      </section>

      {/* Danger zone */}
      <section className="rounded-xl border border-destructive/30 bg-destructive/5 p-4">
        <p className="font-medium text-sm">Reset local progress cache</p>
        <p className="text-xs text-foreground/60 mt-1">Clears the locally-cached progress on this browser. Server-side data is preserved — it will be re-downloaded on next login.</p>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            if (confirm('Clear local progress cache? Your server-side data will reload on next page refresh.')) {
              resetProgress();
              toast({ title: 'Local cache cleared', description: 'Refresh to reload your server-side progress.' });
            }
          }}
          className="mt-2 gap-1.5 text-destructive border-destructive/40 hover:bg-destructive/10"
        >
          Clear cache
        </Button>
      </section>
    </div>
  );
}
