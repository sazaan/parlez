// Run with: node --test tests/test_voice_frontend.cjs
// Execute the actual voice section with browser API doubles (no audio hardware).
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('static/app.js', 'utf8');
const voiceSource = source.slice(source.indexOf('let currentAudio = null;'), source.indexOf('// Exercise Rendering'));

function harness({ secure = true, voices = [], providerFails = false } = {}) {
    const calls = { audio: [], revoked: [], spoken: [], toasts: [], fetches: [], starts: 0 };
    const button = { title: '', classList: { toggle() {} }, setAttribute() {} };
    const status = { style: {} };
    const input = { value: '' };
    class Recognition {
        constructor() { calls.recognition = this; }
        start() { calls.starts++; }
        abort() { this.onend(); }
    }
    const context = vm.createContext({
        window: {
            isSecureContext: secure, SpeechRecognition: Recognition,
            speechSynthesis: { cancel() {}, getVoices: () => voices,
                speak: utterance => calls.spoken.push(utterance),
                addEventListener() {}, removeEventListener() {} }
        },
        SpeechSynthesisUtterance: class { constructor(text) { this.text = text; } },
        Audio: class {
            constructor(url) { this.url = url; calls.audio.push(this); }
            pause() { this.paused = true; }
            async play() {}
        },
        URL: { createObjectURL: () => 'blob:test', revokeObjectURL: url => calls.revoked.push(url) },
        AbortController, console: { warn() {} }, setTimeout, clearTimeout,
        apiFetch: async (_url, options) => {
            calls.fetches.push(options);
            if (providerFails) throw new Error('Provider unavailable');
            return { ok: true, blob: async () => ({ size: 100, type: 'audio/mpeg' }) };
        },
        showToast: message => calls.toasts.push(message), voiceButton: button,
        document: { getElementById: () => status }, messageInput: input,
        autoResize() {}, updateSendButton() {},
    });
    vm.runInContext('let recognition = null; let isRecording = false;\n' + voiceSource, context);
    return { context, calls, input, button };
}
const evaluate = (h, code) => vm.runInContext(code, h.context);

test('successful server playback releases object URLs on completion', async () => {
    const h = harness();
    await evaluate(h, "speakText('Bonjour')");
    assert.equal(h.calls.audio.length, 1);
    h.calls.audio[0].onended();
    assert.deepEqual(h.calls.revoked, ['blob:test']);
    assert.equal(evaluate(h, 'currentSpeakingText'), '');
});

test('repeated click stops playback instead of starting another request', async () => {
    const h = harness();
    await evaluate(h, "speakText('Bonjour')");
    await evaluate(h, "speakText('Bonjour')");
    assert.equal(h.calls.fetches.length, 1);
    assert.equal(h.calls.audio[0].paused, true);
});

test('stopping a pending fetch prevents stale audio from playing', async () => {
    const h = harness();
    let resolve;
    h.context.apiFetch = () => new Promise(r => { resolve = r; });
    const promise = evaluate(h, "speakText('Bonjour')");
    evaluate(h, 'stopSpeaking()');
    resolve({ ok: true, blob: async () => ({ size: 100, type: 'audio/mpeg' }) });
    await promise;
    assert.equal(h.calls.audio.length, 0);
});

test('newest request wins even when the earlier response arrives last', async () => {
    const h = harness();
    const responses = [];
    h.context.apiFetch = () => new Promise(resolve => responses.push(resolve));
    const first = evaluate(h, "speakText('Bonjour')");
    const second = evaluate(h, "speakText('Bonsoir')");
    const response = { ok: true, blob: async () => ({ size: 100, type: 'audio/mpeg' }) };
    responses[1](response); await second;
    responses[0](response); await first;
    assert.equal(h.calls.audio.length, 1);
    assert.equal(evaluate(h, 'currentSpeakingText'), 'Bonsoir');
});

test('provider failure falls back to the requested language and remains toggleable', async () => {
    const h = harness({ providerFails: true, voices: [
        { lang: 'fr-FR', name: 'Google français' }, { lang: 'en-US', name: 'Google English' }
    ] });
    await evaluate(h, "speakText('Hello', 'en')");
    assert.equal(h.calls.spoken[0].voice.lang, 'en-US');
    await evaluate(h, "speakText('Hello', 'en')");
    assert.equal(h.calls.spoken.length, 1);
});

test('decode errors fall back even after play resolves', async () => {
    const h = harness({ voices: [{ lang: 'fr-FR', name: 'French' }] });
    await evaluate(h, "speakText('Bonjour')");
    h.calls.audio[0].onerror();
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(h.calls.spoken.length, 1);
    assert.deepEqual(h.calls.revoked, ['blob:test']);
});

test('autoplay denial gives actionable feedback', async () => {
    const h = harness();
    h.context.Audio.prototype.play = async () => { throw Object.assign(new Error('blocked'), { name: 'NotAllowedError' }); };
    await evaluate(h, "speakText('Bonjour')");
    assert.match(h.calls.toasts[0], /Allow sound/);
    assert.equal(h.calls.spoken.length, 0);
});

test('insecure HTTP shows HTTPS requirement without starting recognition', () => {
    const h = harness({ secure: false });
    evaluate(h, 'initVoice(); toggleVoice()');
    assert.equal(h.calls.starts, 0);
    assert.match(h.calls.toasts[0], /requires HTTPS/);
});

test('recognition reports permission errors and inserts transcripts', () => {
    const h = harness();
    evaluate(h, 'initVoice(); toggleVoice(); toggleVoice()');
    assert.equal(h.calls.starts, 1); // second click aborts pending startup
    h.calls.recognition.onerror({ error: 'not-allowed' });
    assert.match(h.calls.toasts[0], /Microphone access was blocked/);
    h.calls.recognition.onresult({ results: [[{ transcript: 'Bonjour' }]] });
    assert.equal(h.input.value, 'Bonjour');
});

test('browser speech errors clear state and report failure', async () => {
    const h = harness({ providerFails: true, voices: [{ lang: 'fr-FR', name: 'French' }] });
    await evaluate(h, "speakText('Bonjour')");
    h.calls.spoken[0].onerror({ error: 'language-unavailable' });
    assert.equal(evaluate(h, 'currentSpeakingText'), '');
    assert.match(h.calls.toasts[0], /Browser speech failed/);
});

test('unsupported recognition offers typing rather than silently ignoring clicks', () => {
    const h = harness();
    delete h.context.window.SpeechRecognition;
    evaluate(h, 'initVoice(); toggleVoice()');
    assert.match(h.calls.toasts[0], /not supported/);
    assert.equal(h.calls.starts, 0);
});

test('synchronous recognition failure resets pending state', () => {
    const h = harness();
    evaluate(h, 'initVoice()');
    h.calls.recognition.start = () => { throw Object.assign(new Error('denied'), { name: 'NotAllowedError' }); };
    evaluate(h, 'toggleVoice()');
    assert.equal(evaluate(h, 'isVoiceStarting'), false);
    assert.match(h.calls.toasts[0], /Microphone access was blocked/);
});
