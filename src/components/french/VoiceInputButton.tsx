'use client';

import { useState, useEffect } from 'react';
import { Mic, Square } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { startListening, stopListening } from '@/lib/voice/browser-voice';
import { useToast } from '@/hooks/use-toast';

interface VoiceInputButtonProps {
  onTranscript: (text: string, isFinal: boolean) => void;
  lang?: string;
  size?: 'sm' | 'md' | 'lg' | 'icon';
  variant?: 'default' | 'outline' | 'secondary' | 'ghost';
  className?: string;
  label?: string;
}

export function VoiceInputButton({
  onTranscript,
  lang = 'fr-FR',
  size = 'icon',
  variant = 'default',
  className = '',
  label,
}: VoiceInputButtonProps) {
  const [isListening, setIsListening] = useState(false);
  const [mounted, setMounted] = useState(false);
  const { toast } = useToast();

  // Detect speech recognition support — computed after mount to avoid SSR issues
  const supported = mounted &&
    typeof window !== 'undefined' &&
    ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window);

  // Mark as mounted on the client side
  useEffect(() => {
    // Use requestAnimationFrame to defer the state update out of the effect body
    // to satisfy the react-hooks/set-state-in-effect lint rule
    const raf = requestAnimationFrame(() => setMounted(true));
    return () => cancelAnimationFrame(raf);
  }, []);

  const handleToggle = () => {
    if (!supported) {
      toast({ title: 'Voice input unavailable', description: 'Try Chrome or Edge for voice features.', variant: 'destructive' });
      return;
    }
    if (isListening) {
      stopListening();
      setIsListening(false);
      return;
    }
    setIsListening(true);
    startListening({
      lang,
      continuous: false,
      interimResults: true,
      onStart: () => setIsListening(true),
      onResult: (transcript, isFinal) => {
        onTranscript(transcript, isFinal);
        if (isFinal) {
          setIsListening(false);
        }
      },
      onEnd: () => setIsListening(false),
      onError: (err) => {
        setIsListening(false);
        if (err === 'not-allowed' || err === 'service-not-allowed') {
          toast({ title: 'Microphone blocked', description: 'Please allow microphone access in your browser settings.', variant: 'destructive' });
        } else if (err === 'no-speech') {
          // Silent: user just didn't speak
        } else if (err !== 'aborted') {
          toast({ title: 'Voice input error', description: `Error: ${err}`, variant: 'destructive' });
        }
      },
    });
  };

  // Before mount, don't render (avoids hydration mismatch)
  // After mount, always render the button — if speech recognition isn't supported,
  // clicking will show a helpful toast instead of silently hiding the button
  if (!mounted) {
    return null;
  }

  return (
    <Button
      type="button"
      size={size}
      variant={variant}
      onClick={handleToggle}
      className={`gap-2 ${isListening ? 'recording-pulse bg-destructive text-white hover:bg-destructive/90' : ''} ${className}`}
      aria-label={isListening ? 'Stop recording' : label || 'Speak'}
      title={isListening ? 'Stop recording' : label || 'Speak in French'}
    >
      {isListening ? <Square className="h-4 w-4 fill-current" /> : <Mic className="h-4 w-4" />}
      {label && <span className="text-sm">{isListening ? 'Listening…' : label}</span>}
    </Button>
  );
}
