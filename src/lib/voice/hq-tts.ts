// High-quality French TTS playback utility
// Uses our /api/tts proxy (Google Translate TTS) for natural French pronunciation
// Falls back to browser SpeechSynthesis if the API fails

const audioCache = new Map<string, HTMLAudioElement>();
let currentAudio: HTMLAudioElement | null = null;

export interface SpeakOptions {
  rate?: number;
  onStart?: () => void;
  onEnd?: () => void;
  onError?: (err: unknown) => void;
}

/**
 * Play text as speech using high-quality Google Translate TTS.
 * Falls back to browser SpeechSynthesis if the API fails.
 */
export async function speakHQ(text: string, options: SpeakOptions = {}): Promise<void> {
  // Stop any currently playing audio
  stopHQ();

  // Truncate very long text to prevent timeouts (keep reasonable)
  const truncatedText = text.length > 1000 ? text.substring(0, 1000) + '...' : text;

  try {
    // Check cache first
    let audio = audioCache.get(truncatedText);

    if (!audio) {
      // Fetch from our TTS API with a timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 20000); // 20s timeout

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

      // Verify we got actual audio data (not an error JSON)
      if (blob.size < 100) {
        throw new Error('TTS returned empty response');
      }

      const url = URL.createObjectURL(blob);
      audio = new Audio(url);
      audioCache.set(truncatedText, audio);
    }

    currentAudio = audio;
    audio.onended = () => {
      currentAudio = null;
      options.onEnd?.();
    };
    audio.onerror = () => {
      currentAudio = null;
      options.onError?.(new Error('Audio playback failed'));
    };

    options.onStart?.();
    await audio.play();
  } catch (error) {
    console.error('TTS API failed, falling back to browser:', error);
    // Don't call onError — fall back to browser TTS instead
    browserFallback(truncatedText, options);
  }
}

function browserFallback(text: string, options: SpeakOptions) {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
    options.onError?.(new Error('TTS not supported'));
    return;
  }

  try {
    window.speechSynthesis.cancel();

    // Split long text for browser TTS too
    const chunks = text.match(/[^.!?]+[.!?]*/g) || [text];

    let chunkIndex = 0;

    const speakChunk = () => {
      if (chunkIndex >= chunks.length) {
        options.onEnd?.();
        return;
      }

      const utterance = new SpeechSynthesisUtterance(chunks[chunkIndex]);
      utterance.lang = 'fr-FR';
      utterance.rate = options.rate ?? 0.95;

      const voices = window.speechSynthesis.getVoices().filter((v) => v.lang.startsWith('fr'));
      if (voices.length > 0) {
        // Prefer Google French voice, then any fr-FR voice
        const preferred = voices.find((v) => v.name.includes('Google')) ||
                          voices.find((v) => v.lang === 'fr-FR') ||
                          voices[0];
        utterance.voice = preferred;
      }

      if (chunkIndex === 0) {
        utterance.onstart = () => options.onStart?.();
      }
      utterance.onend = () => {
        chunkIndex++;
        speakChunk();
      };
      utterance.onerror = () => {
        options.onError?.(new Error('Browser TTS error'));
      };

      window.speechSynthesis.speak(utterance);
    };

    speakChunk();
  } catch (err) {
    options.onError?.(err);
  }
}

export function stopHQ(): void {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio.currentTime = 0;
    currentAudio = null;
  }
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
}
