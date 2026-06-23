'use client';

import { useState } from 'react';
import { ArrowRight, ArrowLeft, Loader2, Copy, Check, Volume2, VolumeX, Languages } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { useState as useStateReact } from 'react';

type Direction = 'en-to-fr' | 'fr-to-en';

export function Translation() {
  const [input, setInput] = useState('');
  const [output, setOutput] = useState('');
  const [direction, setDirection] = useState<Direction>('en-to-fr');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [audioState, setAudioState] = useState<'idle' | 'loading' | 'playing'>('idle');
  const { toast } = useToast();

  const sourceLabel = direction === 'en-to-fr' ? 'English' : 'Français';
  const targetLabel = direction === 'en-to-fr' ? 'Français' : 'English';
  const sourcePlaceholder = direction === 'en-to-fr' ? 'Type English text to translate...' : 'Tapez du texte en français...';

  const handleTranslate = async () => {
    if (!input.trim()) {
      toast({ title: 'Nothing to translate', description: 'Please enter some text first.', variant: 'destructive' });
      return;
    }
    setLoading(true);
    setOutput('');
    try {
      const res = await fetch('/api/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: input, direction }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || 'Translation failed');
      }
      setOutput(data.translation);
    } catch (error) {
      const msg = error instanceof Error ? error.message : 'Translation failed';
      toast({ title: 'Translation error', description: msg, variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  const handleSwap = () => {
    setDirection((d) => (d === 'en-to-fr' ? 'fr-to-en' : 'en-to-fr'));
    // Swap input and output
    const temp = input;
    setInput(output);
    setOutput(temp);
  };

  const handleCopy = () => {
    if (!output) return;
    navigator.clipboard.writeText(output);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast({ title: 'Copied!', description: 'Translation copied to clipboard.' });
  };

  const handleSpeak = async () => {
    if (!output) return;
    if (audioState === 'playing') {
      setAudioState('idle');
      return;
    }
    setAudioState('loading');
    try {
      const res = await fetch('/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: output }),
      });
      if (!res.ok) throw new Error('TTS failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.onended = () => setAudioState('idle');
      audio.onerror = () => {
        setAudioState('idle');
        toast({ title: 'Audio error', description: 'Could not play audio.', variant: 'destructive' });
      };
      await audio.play();
      setAudioState('playing');
    } catch (error) {
      setAudioState('idle');
      toast({ title: 'Audio unavailable', description: 'Could not generate audio.', variant: 'destructive' });
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleTranslate();
    }
  };

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Translation Tool</p>
        <h1 className="font-serif text-3xl sm:text-4xl font-semibold">Translate</h1>
        <p className="text-foreground/70 max-w-2xl">
          Type English or French text and get an instant translation. Click the speaker icon to hear the French pronunciation with a natural voice.
        </p>
      </header>

      {/* Direction switcher */}
      <div className="flex items-center justify-center gap-3">
        <span className={`text-sm font-medium px-3 py-1.5 rounded-full ${direction === 'en-to-fr' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground'}`}>
          🇬🇧 English
        </span>
        <Button
          variant="outline"
          size="icon"
          onClick={handleSwap}
          className="rounded-full h-9 w-9"
          aria-label="Swap languages"
          title="Swap languages"
        >
          {direction === 'en-to-fr' ? <ArrowRight className="h-4 w-4" /> : <ArrowLeft className="h-4 w-4" />}
        </Button>
        <span className={`text-sm font-medium px-3 py-1.5 rounded-full ${direction === 'fr-to-en' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground'}`}>
          🇫🇷 Français
        </span>
      </div>

      {/* Translation panels */}
      <div className="grid lg:grid-cols-2 gap-4">
        {/* Input panel */}
        <div className="rounded-2xl border border-border bg-card p-5 flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <Label className="text-xs uppercase tracking-wider text-muted-foreground">
              {sourceLabel}
            </Label>
            <span className="text-xs text-muted-foreground">{input.length}/500</span>
          </div>
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value.slice(0, 500))}
            onKeyDown={handleKeyDown}
            placeholder={sourcePlaceholder}
            className="flex-1 min-h-[180px] resize-none text-base"
            autoFocus
          />
          <div className="mt-3 flex items-center justify-between">
            <p className="text-xs text-muted-foreground">Ctrl+Enter to translate</p>
            <Button
              onClick={handleTranslate}
              disabled={loading || !input.trim()}
              className="gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" /> Translating…
                </>
              ) : (
                <>
                  <Languages className="h-4 w-4" /> Translate
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Output panel */}
        <div className="rounded-2xl border border-border bg-gradient-to-br from-card to-secondary/30 p-5 flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <Label className="text-xs uppercase tracking-wider text-muted-foreground">
              {targetLabel}
            </Label>
            <div className="flex items-center gap-1">
              {output && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleCopy}
                  className="gap-1.5 h-8"
                  aria-label="Copy translation"
                >
                  {copied ? <Check className="h-3.5 w-3.5 text-chart-3" /> : <Copy className="h-3.5 w-3.5" />}
                  <span className="text-xs">{copied ? 'Copied' : 'Copy'}</span>
                </Button>
              )}
              {output && direction === 'en-to-fr' && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleSpeak}
                  className="gap-1.5 h-8"
                  aria-label="Play French audio"
                  title="Listen to French pronunciation"
                >
                  {audioState === 'loading' ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : audioState === 'playing' ? (
                    <VolumeX className="h-3.5 w-3.5" />
                  ) : (
                    <Volume2 className="h-3.5 w-3.5" />
                  )}
                  <span className="text-xs">{audioState === 'loading' ? 'Loading…' : audioState === 'playing' ? 'Stop' : 'Listen'}</span>
                </Button>
              )}
            </div>
          </div>
          <div className="flex-1 min-h-[180px] p-3 rounded-lg bg-card/50 border border-border/50">
            {loading ? (
              <div className="flex items-center justify-center h-full">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span className="text-sm">Translating…</span>
                </div>
              </div>
            ) : output ? (
              <p className="text-base leading-relaxed text-foreground whitespace-pre-wrap">{output}</p>
            ) : (
              <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                Translation will appear here…
              </div>
            )}
          </div>
          {output && direction === 'en-to-fr' && (
            <p className="mt-2 text-xs text-muted-foreground flex items-center gap-1">
              <Volume2 className="h-3 w-3" /> Click "Listen" to hear the French pronunciation
            </p>
          )}
        </div>
      </div>

      {/* Example phrases */}
      <div className="rounded-2xl border border-border bg-card p-5">
        <h3 className="font-serif text-lg font-semibold mb-3">Try these examples</h3>
        <div className="grid sm:grid-cols-2 gap-2">
          {[
            'Hello, how are you today?',
            'I would like a coffee, please.',
            'Where is the train station?',
            'What time does the museum open?',
            'Can you help me, please?',
            'I am learning French.',
            'The weather is beautiful today.',
            'How much does this cost?',
          ].map((phrase, i) => (
            <button
              key={i}
              onClick={() => {
                setDirection('en-to-fr');
                setInput(phrase);
                setOutput('');
              }}
              className="text-left p-3 rounded-lg border border-border bg-secondary/30 hover:bg-secondary transition text-sm"
            >
              {phrase}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
