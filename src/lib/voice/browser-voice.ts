// Browser-native voice utilities (100% free, no API needed)
// These wrap the Web Speech API: SpeechSynthesis (TTS) and SpeechRecognition (STT)

import { useSyncExternalStore } from 'react';

// ========== Text-to-Speech (Synthesis) ==========

let cachedFrenchVoices: SpeechSynthesisVoice[] = [];

export function isTTSSupported(): boolean {
  return typeof window !== 'undefined' && 'speechSynthesis' in window;
}

// React hook for SSR-safe feature detection
const emptySubscribe = () => () => {};
export function useTTSSupported(): boolean {
  return useSyncExternalStore(
    emptySubscribe,
    () => typeof window !== 'undefined' && 'speechSynthesis' in window,
    () => false
  );
}

export function useSTTSupported(): boolean {
  return useSyncExternalStore(
    emptySubscribe,
    () => {
      if (typeof window === 'undefined') return false;
      return (
        'SpeechRecognition' in window ||
        'webkitSpeechRecognition' in window
      );
    },
    () => false
  );
}

/**
 * Load French voices from the browser. Voices load asynchronously in some browsers.
 * Prioritizes the most natural-sounding French voices:
 *   1. "Google français" / "Google French" (Chrome online voice — very natural)
 *   2. Any fr-FR voice with "natural" or "premium" in the name
 *   3. Any fr-FR voice
 *   4. Any voice starting with "fr"
 */
export function loadFrenchVoices(): Promise<SpeechSynthesisVoice[]> {
  return new Promise((resolve) => {
    if (!isTTSSupported()) {
      resolve([]);
      return;
    }
    const existing = window.speechSynthesis.getVoices().filter((v) => v.lang.startsWith('fr'));
    if (existing.length > 0) {
      cachedFrenchVoices = sortFrenchVoices(existing);
      resolve(cachedFrenchVoices);
      return;
    }
    let attempts = 0;
    const check = () => {
      attempts++;
      const voices = window.speechSynthesis.getVoices().filter((v) => v.lang.startsWith('fr'));
      if (voices.length > 0 || attempts > 15) {
        cachedFrenchVoices = sortFrenchVoices(voices);
        resolve(cachedFrenchVoices);
      } else {
        setTimeout(check, 200);
      }
    };
    check();
    window.speechSynthesis.onvoiceschanged = () => {
      cachedFrenchVoices = sortFrenchVoices(window.speechSynthesis.getVoices().filter((v) => v.lang.startsWith('fr')));
    };
  });
}

/**
 * Sort French voices by quality preference.
 * Google voices and "natural"/"premium" voices come first.
 */
function sortFrenchVoices(voices: SpeechSynthesisVoice[]): SpeechSynthesisVoice[] {
  return [...voices].sort((a, b) => {
    const scoreA = getVoiceScore(a);
    const scoreB = getVoiceScore(b);
    return scoreB - scoreA;
  });
}

function getVoiceScore(voice: SpeechSynthesisVoice): number {
  let score = 0;
  const name = voice.name.toLowerCase();

  // Prefer Google voices (very natural, online)
  if (name.includes('google')) score += 100;
  // Prefer "natural" or "premium" voices
  if (name.includes('natural')) score += 50;
  if (name.includes('premium')) score += 50;
  if (name.includes('enhanced')) score += 30;
  // Prefer fr-FR over other French variants
  if (voice.lang === 'fr-FR') score += 20;
  // Prefer female voices for French (generally clearer for learning)
  if (name.includes('amelie') || name.includes('amélie') || name.includes('marie') ||
      name.includes('julie') || name.includes('virginie') || name.includes('audrey') ||
      name.includes('female')) score += 10;
  // Slightly prefer local voices (lower latency) over remote, unless Google
  if (voice.localService && !name.includes('google')) score += 5;
  return score;
}

/**
 * Get the best available French voice.
 */
export function getBestFrenchVoice(): SpeechSynthesisVoice | null {
  if (cachedFrenchVoices.length > 0) return cachedFrenchVoices[0];
  if (!isTTSSupported()) return null;
  const voices = window.speechSynthesis.getVoices().filter((v) => v.lang.startsWith('fr'));
  if (voices.length === 0) return null;
  cachedFrenchVoices = sortFrenchVoices(voices);
  return cachedFrenchVoices[0];
}

export interface SpeakOptions {
  rate?: number; // 0.5 to 2.0, default 0.95
  pitch?: number; // 0 to 2, default 1.0
  volume?: number; // 0 to 1, default 1.0
  voiceURI?: string; // specific voice
  onStart?: () => void;
  onEnd?: () => void;
  onError?: (err: unknown) => void;
}

let currentUtterance: SpeechSynthesisUtterance | null = null;

/**
 * Speak text using the browser's SpeechSynthesis API.
 * Automatically selects the best available French voice.
 */
export function speak(text: string, options: SpeakOptions = {}): void {
  if (!isTTSSupported()) {
    options.onError?.(new Error('TTS not supported in this browser'));
    return;
  }
  // Cancel any ongoing speech
  window.speechSynthesis.cancel();

  // Small delay to ensure cancel takes effect
  setTimeout(() => {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'fr-FR';
    utterance.rate = options.rate ?? 0.95;
    utterance.pitch = options.pitch ?? 1.0;
    utterance.volume = options.volume ?? 1.0;

    // Pick the best French voice
    const voices = cachedFrenchVoices.length > 0
      ? cachedFrenchVoices
      : window.speechSynthesis.getVoices().filter((v) => v.lang.startsWith('fr'));

    if (voices.length > 0) {
      const preferredVoice =
        voices.find((v) => v.voiceURI === options.voiceURI) ||
        voices[0]; // Already sorted by quality in loadFrenchVoices
      utterance.voice = preferredVoice;
    }

    utterance.onstart = () => options.onStart?.();
    utterance.onend = () => {
      currentUtterance = null;
      options.onEnd?.();
    };
    utterance.onerror = (e) => {
      currentUtterance = null;
      options.onError?.(e);
    };

    currentUtterance = utterance;
    window.speechSynthesis.speak(utterance);
  }, 50);
}

export function stopSpeaking(): void {
  if (isTTSSupported()) {
    window.speechSynthesis.cancel();
    currentUtterance = null;
  }
}

export function isSpeaking(): boolean {
  return isTTSSupported() && window.speechSynthesis.speaking;
}

// ========== Speech-to-Text (Recognition) ==========

interface SpeechRecognitionEvent extends Event {
  readonly resultIndex: number;
  readonly results: {
    length: number;
    [index: number]: {
      length: number;
      isFinal: boolean;
      [index: number]: { transcript: string; confidence: number };
    };
  };
}

interface SpeechRecognitionErrorEvent extends Event {
  readonly error: string;
  readonly message: string;
}

interface ISpeechRecognition extends EventTarget {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  maxAlternatives: number;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  onstart: (() => void) | null;
}

type SpeechRecognitionConstructor = new () => ISpeechRecognition;

function getSpeechRecognitionCtor(): SpeechRecognitionConstructor | null {
  if (typeof window === 'undefined') return null;
  return (
    (window as unknown as { SpeechRecognition?: SpeechRecognitionConstructor }).SpeechRecognition ||
    (window as unknown as { webkitSpeechRecognition?: SpeechRecognitionConstructor }).webkitSpeechRecognition ||
    null
  );
}

export function isSTTSupported(): boolean {
  return getSpeechRecognitionCtor() !== null;
}

export interface ListenOptions {
  lang?: string; // default 'fr-FR'
  continuous?: boolean; // default false
  interimResults?: boolean; // default true
  onResult?: (transcript: string, isFinal: boolean) => void;
  onStart?: () => void;
  onEnd?: () => void;
  onError?: (err: string) => void;
}

let activeRecognition: ISpeechRecognition | null = null;

export function startListening(options: ListenOptions = {}): void {
  const Ctor = getSpeechRecognitionCtor();
  if (!Ctor) {
    options.onError?.('not-supported');
    return;
  }
  if (activeRecognition) {
    try {
      activeRecognition.abort();
    } catch {
      // ignore
    }
    activeRecognition = null;
  }

  const recognition = new Ctor();
  recognition.lang = options.lang ?? 'fr-FR';
  recognition.continuous = options.continuous ?? false;
  recognition.interimResults = options.interimResults ?? true;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => options.onStart?.();

  recognition.onresult = (event: SpeechRecognitionEvent) => {
    let finalTranscript = '';
    let interimTranscript = '';
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const result = event.results[i];
      const transcript = result[0].transcript;
      if (result.isFinal) {
        finalTranscript += transcript;
      } else {
        interimTranscript += transcript;
      }
    }
    if (finalTranscript) {
      options.onResult?.(finalTranscript.trim(), true);
    }
    if (interimTranscript) {
      options.onResult?.(interimTranscript.trim(), false);
    }
  };

  recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
    options.onError?.(event.error);
  };

  recognition.onend = () => {
    activeRecognition = null;
    options.onEnd?.();
  };

  activeRecognition = recognition;
  try {
    recognition.start();
  } catch (e) {
    options.onError?.(e instanceof Error ? e.message : 'start-failed');
  }
}

export function stopListening(): void {
  if (activeRecognition) {
    try {
      activeRecognition.stop();
    } catch {
      // ignore
    }
    activeRecognition = null;
  }
}
