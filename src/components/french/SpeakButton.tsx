'use client';

import { useState, useRef } from 'react';
import { Volume2, Square, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';

interface SpeakButtonProps {
  text: string;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'ghost' | 'outline' | 'default' | 'secondary';
  className?: string;
  label?: string;
}

// Cache for audio blobs (per text) so we don't re-fetch the same TTS
const audioCache = new Map<string, HTMLAudioElement>();

export function SpeakButton({ text, size = 'sm', variant = 'ghost', className = '', label }: SpeakButtonProps) {
  const [state, setState] = useState<'idle' | 'loading' | 'playing'>('idle');
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const { toast } = useToast();

  const stopAll = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }
    // Also stop browser TTS if running
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setState('idle');
  };

  const browserFallback = (textToSpeak: string) => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      setState('idle');
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    utterance.lang = 'fr-FR';
    utterance.rate = 0.95;

    const voices = window.speechSynthesis.getVoices().filter((v) => v.lang.startsWith('fr'));
    if (voices.length > 0) {
      const preferred = voices.find((v) => v.name.includes('Google')) ||
                        voices.find((v) => v.lang === 'fr-FR') ||
                        voices[0];
      utterance.voice = preferred;
    }

    utterance.onend = () => setState('idle');
    utterance.onerror = () => setState('idle');
    window.speechSynthesis.speak(utterance);
  };

  const handleSpeak = async () => {
    // If already playing, stop
    if (state === 'playing') {
      stopAll();
      return;
    }

    setState('loading');

    // Truncate very long text
    const truncatedText = text.length > 1000 ? text.substring(0, 1000) + '...' : text;

    try {
      // Check cache first
      let audio = audioCache.get(truncatedText);

      if (!audio) {
        // Fetch from our TTS API (which proxies Google Translate TTS for natural French)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 20000);

        const res = await fetch('/api/tts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: truncatedText }),
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!res.ok) {
          throw new Error(`TTS API returned ${res.status}`);
        }

        const blob = await res.blob();

        // Verify we got actual audio data
        if (blob.size < 100) {
          throw new Error('Empty audio response');
        }

        const url = URL.createObjectURL(blob);
        audio = new Audio(url);
        audioCache.set(truncatedText, audio);
      }

      // Stop any currently playing audio
      stopAll();

      audioRef.current = audio;
      audio.onended = () => setState('idle');
      audio.onerror = () => {
        setState('idle');
        // Fall back to browser TTS
        browserFallback(truncatedText);
      };

      await audio.play();
      setState('playing');
    } catch (error) {
      console.error('TTS failed, falling back to browser:', error);
      setState('idle');
      // Fall back to browser TTS silently (no error toast — just use what we have)
      browserFallback(truncatedText);
    }
  };

  return (
    <Button
      type="button"
      size={size}
      variant={variant}
      onClick={handleSpeak}
      className={`gap-1.5 ${className}`}
      aria-label={label || 'Play audio'}
      title={label || 'Listen in French (natural voice)'}
    >
      {state === 'loading' ? (
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
      ) : state === 'playing' ? (
        <Square className="h-3.5 w-3.5 fill-current" />
      ) : (
        <Volume2 className="h-3.5 w-3.5" />
      )}
      {label && <span className="text-xs">{state === 'loading' ? 'Loading…' : state === 'playing' ? 'Playing…' : label}</span>}
    </Button>
  );
}
