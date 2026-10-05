# Voice troubleshooting

Parlez has two separate voice features:

- **Listen / speaker buttons:** request speech audio from `/api/tts`, then play
  it in the browser. Browser speech synthesis is a fallback.
- **Microphone button:** uses the browser's speech-recognition service to insert
  French dictation into the chat input. It is not a server-hosted recognition
  service, and availability depends on the browser/device.

## After deploying the voice fix

Rebuild/recreate the app and reload the page:

```bash
docker compose up --build -d
docker compose logs --tail=100 chatbot
```

The app's Content Security Policy must include `media-src 'self' blob:` because
Listen uses a locally created audio object URL. If another reverse proxy adds a
second CSP, every policy applies: that proxy must also permit the audio URL.
Do not disable CSP or relax `script-src` to solve an audio problem.

## Listen does not play

1. Check the device volume, output device, tab mute setting and the browser's
   sound/autoplay permissions. Click a Listen button explicitly.
2. In browser Developer Tools → Network, check `POST /api/tts`:
   - `200` with `audio/mpeg`: inspect Console for media/CSP/permission errors.
   - `401`: log in again.
   - `429`: wait before trying again (TTS is rate-limited).
   - `502` / `500`: inspect container logs; upstream TTS may be unavailable.
3. Browser fallback requires speech synthesis support and a usable voice for
   French. Install/enable French voices through your device settings if needed.
4. Clicking the same text again stops it, including while a request is pending.
   Clicking a different text cancels the old playback/request.

The current server integration calls Google's Translate TTS endpoint, not a
contracted Google Cloud speech API. Availability is not guaranteed. Network
failures, empty responses or non-audio responses trigger browser fallback. For
production reliability, migrate to a supported speech provider with reviewed
terms and quotas; do not assume this endpoint provides a production SLA.

## Microphone does nothing

1. **Use HTTPS.** `http://localhost:8000` on your own computer is a browser
   exception, but `http://SERVER_IP:8000` or an HTTP LAN address normally is not.
   Running Docker locally on a remote server does not make that server's IP
   “localhost” to your browser.
2. Allow microphone access for the site and in your operating system. Connect
   a microphone and verify it works elsewhere.
3. Try a browser with Web Speech recognition support (commonly Chrome/Edge).
   Availability still varies by platform and policy. Type instead if unsupported.
4. Browser recognition may require access to an online speech service. A network
   error can occur even when Parlez itself is reachable.
5. If embedded in a preview/iframe, microphone access may also depend on the
   embedding platform's permissions. Try opening the app directly in a tab.

The UI now distinguishes insecure connections, permission denial, missing
microphones, no speech, and speech-service network errors instead of silently
resetting the button. Recognized French speech populates the message box; press
Send to submit it.

## Regression checks

```bash
node --check static/app.js
node --test tests/test_voice_frontend.cjs
JWT_SECRET=this-is-a-test-secret-that-is-32-chars-long \
NVIDIA_API_KEY=dummy python -m pytest tests/test_tts.py -q
```

Frontend tests use API doubles for deterministic lifecycle, cancellation,
fallback and recognition-error checks. Python tests verify CSP and mocked
upstream TTS responses. Neither substitutes for an audible device/browser test.
