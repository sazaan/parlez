'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Volume2, Square, RotateCcw, Mic, Sparkles, MessageCircle } from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { conversationScenarios } from '@/lib/courses';
import type { CourseLevel } from '@/lib/courses/types';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { SpeakButton } from './SpeakButton';
import { VoiceInputButton } from './VoiceInputButton';
import { useToast } from '@/hooks/use-toast';
import { speakHQ, stopHQ } from '@/lib/voice/hq-tts';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

const levels: { id: CourseLevel; label: string; description: string; color: string }[] = [
  { id: 'A1', label: 'A1 — Débutant', description: 'Simple words, present tense', color: '#2D6A4F' },
  { id: 'A2', label: 'A2 — Élémentaire', description: 'Past tenses, opinions', color: '#C19A4B' },
  { id: 'B1', label: 'B1 — Intermédiaire', description: 'Subjunctive, debates', color: '#B45309' },
  { id: 'B2', label: 'B2 — Avancé', description: 'Nuance, literature', color: '#7C2D3F' },
];

export function AIConversation() {
  const voiceRate = useAppStore((s) => s.voiceRate);
  const { toast } = useToast();

  const [level, setLevel] = useState<CourseLevel>('A1');
  const [scenario, setScenario] = useState<string>('cafe');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [autoSpeak, setAutoSpeak] = useState(true);
  const [currentSpeakingId, setCurrentSpeakingId] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  // Reset conversation when level or scenario changes
  const startConversation = (lvl: CourseLevel, scen: string) => {
    setLevel(lvl);
    setScenario(scen);
    setMessages([]);
    stopHQ();
    setCurrentSpeakingId(null);
    // Auto-trigger the AI to start the conversation
    setTimeout(() => {
      sendMessage('', lvl, scen, true);
    }, 100);
  };

  const sendMessage = async (text: string, lvl: CourseLevel = level, scen: string = scenario, isStarter = false) => {
    const trimmed = text.trim();
    if (!trimmed && !isStarter) return;
    if (isThinking) return;

    const userMsg: ChatMessage | null = trimmed
      ? { role: 'user', content: trimmed, timestamp: Date.now() }
      : null;
    const newMessages = userMsg ? [...messages, userMsg] : messages;
    if (userMsg) setMessages(newMessages);
    setInput('');
    setIsThinking(true);

    try {
      const apiMessages = [
        ...newMessages.map((m) => ({ role: m.role, content: m.content })),
      ];
      // If starter, add a tiny user prompt to kick off
      if (isStarter && apiMessages.length === 0) {
        apiMessages.push({ role: 'user', content: '(Start the conversation now — greet me in French.)' });
      }

      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          level: lvl,
          scenario: scen,
          scenarioLabel: scenarios.find((s) => s.id === scen)?.labelFr || '',
          messages: apiMessages,
        }),
      });

      if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.error || 'Network error');
      }

      const data = await res.json();
      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: data.message,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, assistantMsg]);

      // Auto-speak the assistant response
      if (autoSpeak) {
        setTimeout(() => {
          speakAssistant(data.message, assistantMsg.timestamp);
        }, 200);
      }
    } catch (error) {
      console.error('Chat error:', error);
      toast({
        title: 'Conversation error',
        description: error instanceof Error ? error.message : 'Could not reach the AI tutor.',
        variant: 'destructive',
      });
    } finally {
      setIsThinking(false);
    }
  };

  const speakAssistant = (text: string, id: number) => {
    setCurrentSpeakingId(id);
    speakHQ(text, {
      rate: voiceRate,
      onEnd: () => setCurrentSpeakingId(null),
      onError: () => setCurrentSpeakingId(null),
    });
  };

  const handleVoiceTranscript = (transcript: string, isFinal: boolean) => {
    setInput(transcript);
    if (isFinal && transcript.trim()) {
      // Auto-send on final transcript
      setTimeout(() => {
        sendMessage(transcript);
      }, 100);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const resetConversation = () => {
    setMessages([]);
    stopHQ();
    setCurrentSpeakingId(null);
    startConversation(level, scenario);
  };

  const scenarios = conversationScenarios;
  const currentScenario = scenarios.find((s) => s.id === scenario);
  const currentLevel = levels.find((l) => l.id === level);

  return (
    <div className="space-y-5">
      {/* Header */}
      <header className="space-y-2">
        <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">AI French Tutor</p>
        <h1 className="font-serif text-3xl sm:text-4xl font-semibold">Conversation</h1>
        <p className="text-foreground/70 max-w-2xl">
          Talk out loud — your tutor listens and replies in French with voice. Pick a level, pick a scenario, and start chatting. Don&apos;t worry about mistakes; you&apos;ll get gentle corrections.
        </p>
      </header>

      {/* Setup (when no messages yet) */}
      {messages.length === 0 && (
        <div className="grid lg:grid-cols-2 gap-5">
          {/* Level picker */}
          <div className="rounded-2xl border border-border bg-card p-5">
            <h2 className="font-serif text-lg font-semibold mb-3">1. Choose your level</h2>
            <div className="space-y-2">
              {levels.map((l) => (
                <button
                  key={l.id}
                  onClick={() => setLevel(l.id)}
                  className={`w-full text-left p-3 rounded-lg border transition flex items-center gap-3 ${
                    level === l.id ? 'border-primary bg-primary/5' : 'border-border hover:bg-secondary'
                  }`}
                >
                  <div
                    className="flex-shrink-0 h-10 w-10 rounded-lg flex items-center justify-center font-serif font-bold text-white text-sm"
                    style={{ background: l.color }}
                  >
                    {l.id}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm">{l.label}</p>
                    <p className="text-xs text-muted-foreground">{l.description}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Scenario picker */}
          <div className="rounded-2xl border border-border bg-card p-5">
            <h2 className="font-serif text-lg font-semibold mb-3">2. Pick a scenario</h2>
            <div className="grid grid-cols-2 gap-2 max-h-[400px] overflow-y-auto scroll-elegant pr-1">
              {scenarios.map((s) => (
                <button
                  key={s.id}
                  onClick={() => setScenario(s.id)}
                  className={`text-left p-3 rounded-lg border transition ${
                    scenario === s.id ? 'border-primary bg-primary/5' : 'border-border hover:bg-secondary'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{s.icon}</span>
                    <p className="font-medium text-sm">{s.labelFr}</p>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{s.description}</p>
                </button>
              ))}
            </div>
          </div>

          <div className="lg:col-span-2">
            <Button
              onClick={() => startConversation(level, scenario)}
              size="lg"
              className="w-full sm:w-auto gap-2"
            >
              <Sparkles className="h-4 w-4" /> Start the conversation
            </Button>
          </div>
        </div>
      )}

      {/* Conversation active */}
      {messages.length > 0 && (
        <>
          {/* Status bar */}
          <div className="flex items-center justify-between flex-wrap gap-3 rounded-2xl border border-border bg-card p-3">
            <div className="flex items-center gap-2 flex-wrap">
              <Badge style={{ background: currentLevel?.color, color: 'white' }}>{level}</Badge>
              <span className="text-sm text-foreground/70">
                <span className="text-lg mr-1">{currentScenario?.icon}</span>
                {currentScenario?.labelFr}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant={autoSpeak ? 'default' : 'outline'}
                size="sm"
                onClick={() => setAutoSpeak((v) => !v)}
                className="gap-1.5"
              >
                <Volume2 className="h-3.5 w-3.5" /> Auto-voice {autoSpeak ? 'on' : 'off'}
              </Button>
              <Button variant="ghost" size="sm" onClick={resetConversation} className="gap-1.5">
                <RotateCcw className="h-3.5 w-3.5" /> Restart
              </Button>
            </div>
          </div>

          {/* Messages */}
          <div className="rounded-2xl border border-border bg-card overflow-hidden">
            <div className="max-h-[55vh] overflow-y-auto scroll-elegant p-4 sm:p-6 space-y-4">
              {messages.map((m) => {
                const isUser = m.role === 'user';
                return (
                  <div key={m.timestamp} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[85%] sm:max-w-[75%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
                      <div
                        className={`rounded-2xl p-3.5 ${
                          isUser
                            ? 'bg-primary text-primary-foreground rounded-tr-sm'
                            : 'bg-secondary text-foreground rounded-tl-sm'
                        }`}
                      >
                        <p className="text-sm whitespace-pre-wrap leading-relaxed">{m.content}</p>
                      </div>
                      {!isUser && (
                        <button
                          onClick={() => currentSpeakingId === m.timestamp ? (stopHQ(), setCurrentSpeakingId(null)) : speakAssistant(m.content, m.timestamp)}
                          className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 px-1"
                        >
                          {currentSpeakingId === m.timestamp ? (
                            <>
                              <div className="flex items-end gap-0.5 h-3">
                                {[0, 1, 2, 3].map((i) => (
                                  <span
                                    key={i}
                                    className="waveform-bar w-0.5 bg-primary rounded"
                                    style={{ height: '100%', animationDelay: `${i * 0.15}s` }}
                                  />
                                ))}
                              </div>
                              Speaking…
                            </>
                          ) : (
                            <>
                              <Volume2 className="h-3 w-3" /> Replay
                            </>
                          )}
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
              {isThinking && (
                <div className="flex justify-start">
                  <div className="bg-secondary text-foreground rounded-2xl rounded-tl-sm p-4">
                    <div className="flex items-center gap-2">
                      <div className="flex gap-1">
                        {[0, 1, 2].map((i) => (
                          <span
                            key={i}
                            className="w-1.5 h-1.5 rounded-full bg-foreground/50 animate-bounce"
                            style={{ animationDelay: `${i * 0.15}s` }}
                          />
                        ))}
                      </div>
                      <span className="text-xs text-muted-foreground">Votre tuteur réfléchit…</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input area */}
            <div className="border-t border-border bg-card p-3 sm:p-4">
              <div className="flex items-end gap-2">
                <div className="flex-1 relative">
                  <textarea
                    ref={inputRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Écrivez en français… ou utilisez le micro 🎤"
                    rows={1}
                    className="w-full resize-none p-3 pr-12 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary min-h-[48px] max-h-32"
                    style={{ height: 'auto' }}
                  />
                </div>
                <VoiceInputButton onTranscript={handleVoiceTranscript} size="icon" className="h-12 w-12 rounded-xl" />
                <Button
                  onClick={() => sendMessage(input)}
                  disabled={!input.trim() || isThinking}
                  size="icon"
                  className="h-12 w-12 rounded-xl"
                  aria-label="Send message"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
              <p className="mt-2 text-xs text-muted-foreground text-center">
                Press Enter to send · Shift+Enter for newline · 🎤 for voice
              </p>
            </div>
          </div>

          {/* Helper tips */}
          <div className="rounded-2xl border border-accent/30 bg-accent/10 p-4 text-sm">
            <p className="font-medium mb-1">💡 Tips for great practice</p>
            <ul className="text-foreground/70 text-xs space-y-1 ml-4 list-disc">
              <li>Speak in full sentences, even short ones. Your tutor will gently correct mistakes.</li>
              <li>If you don&apos;t know a word, try to describe it in French — that&apos;s how you learn.</li>
              <li>Use the 🎤 button to practice pronunciation. Speak slowly and clearly.</li>
              <li>Replay the tutor&apos;s voice as many times as you need to understand.</li>
            </ul>
          </div>
        </>
      )}
    </div>
  );
}
