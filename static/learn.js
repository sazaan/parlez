// ============================================================
// Parlez interactive learning shell (Phase A)
// Path view + session player. Uses the existing course APIs and
// XSS-safe renderExercise(); no framework, no build step.
// ============================================================

(() => {
    'use strict';

    const pathEl = document.getElementById('learnPath');
    const sessionEl = document.getElementById('sessionHost');
    const levelEl = document.getElementById('learnLevel');
    const viewEl = document.getElementById('learnView');
    const STORAGE_KEY = 'parlezLearnSession';
    let course = null;
    let session = null;
    let levelMeta = {};
    let levelDetailsCache = null;

    function h(value) {
        return typeof escapeHtml === 'function' ? escapeHtml(value) : String(value ?? '');
    }

    function recordEvent(name, props) {
        try {
            fetch('/api/events', {
                method: 'POST', credentials: 'same-origin',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, props: props || {} }),
                keepalive: true,
            }).catch(() => {});
        } catch (e) { /* analytics must never break learning */ }
    }

    function showPath() {
        if (!sessionEl) return;
        sessionEl.hidden = true;
        if (pathEl) pathEl.style.display = '';
        document.querySelectorAll('.app-bottom-nav button').forEach(b => b.classList.remove('active'));
        document.querySelector('.app-bottom-nav [data-nav="learn"]')?.classList.add('active');
    }

    function showSession() {
        if (!sessionEl) return;
        sessionEl.hidden = false;
        if (typeof animateView === 'function') animateView(sessionEl);
        if (pathEl) pathEl.style.display = 'none';
    }

    window.showLearnView = async function() {
        if (!viewEl) return;
        document.getElementById('chatView').style.display = 'none';
        document.getElementById('toolView').style.display = 'none';
        viewEl.style.display = 'flex';
        if (typeof animateView === 'function') animateView(viewEl);
        document.getElementById('chatTitle').textContent = 'Learn French — your path';
        document.getElementById('btnBackToChat').style.display = 'none';
        if (typeof setCoursesNavActive === 'function') setCoursesNavActive(false);
        setBottomNav('learn');

        // One round-trip, not four sequential ones.
        const [rewards, progress] = await Promise.all([
            apiFetch('/api/rewards/summary').then(r => r.json()).catch(() => ({})),
            apiFetch('/api/progress').then(r => r.json()).catch(() => ({})),
        ]);
        const xpEl = document.getElementById('learnXp');
        const streakEl = document.getElementById('learnStreak');
        const badgeEl = document.getElementById('learnBadges');
        const starEl = document.getElementById('learnStars');
        if (xpEl) xpEl.textContent = rewards.total_xp || 0;
        if (streakEl) streakEl.textContent = rewards.streak || 0;
        if (badgeEl) badgeEl.textContent = (rewards.badges || []).length;
        if (starEl) starEl.textContent = rewards.totalStars || 0;

        if (!levelEl.options.length) await loadLearnLevels(progress);
        await loadLearnPath(levelEl.value || currentLevel || 'A1', progress);
        const saved = readSession();
        if (saved && saved.lessonId) showResumeBanner(saved);
        else showPath();
    };

    async function loadLearnLevels(providedProgress) {
        try {
            const levelsRes = await apiFetch('/api/learn/courses');
            const levels = (await levelsRes.json()).levels;
            const progress = providedProgress || await apiFetch('/api/progress').then(r => r.json()).catch(() => ({}));
            const passed = passedSet(progress);
            if (!levelDetailsCache) {
                levelDetailsCache = {};
                await Promise.all(levels.map(async (level) => {
                    const detail = await apiFetch(`/api/learn/courses/${encodeURIComponent(level.level)}`).then(r => r.json());
                    levelDetailsCache[level.level] = detail;
                }));
            }
            levelMeta = {};
            for (const level of levels) {
                const detail = levelDetailsCache[level.level] || { units: [], title: level.title };
                const units = detail.units || [];
                levelMeta[level.level] = {
                    lessonIds: units.flatMap(u => (u.lessons || []).map(l => l.id)),
                    title: detail.title,
                };
            }
            levelEl.innerHTML = levels.map((l, index) => {
                const previousIds = index === 0 ? [] : (levelMeta[levels[index - 1].level]?.lessonIds || []);
                const unlocked = index === 0 || (previousIds.length > 0 && previousIds.every(id => passed.has(id)));
                return `<option value="${h(l.level)}" ${unlocked ? '' : 'disabled'}>${h(l.level)} · ${h(l.name || l.title || '')}${unlocked ? '' : ' 🔒'}</option>`;
            }).join('');
            const preferred = currentLevel || 'A1';
            if ([...levelEl.options].some(o => o.value === preferred && !o.disabled)) levelEl.value = preferred;
            else levelEl.value = levels[0].level;
        } catch (e) {
            levelEl.innerHTML = '<option value="A1">A1</option>';
        }
    }

    async function loadLearnPath(level, providedProgress) {
        if (!pathEl) return;
        pathEl.innerHTML = '<p class="path-empty">Loading your path…</p>';
        try {
            const courseRes = await apiFetch(`/api/learn/courses/${encodeURIComponent(level)}`);
            course = await courseRes.json();
            const progress = providedProgress || await apiFetch('/api/progress').then(r => r.json()).catch(() => ({}));
            renderLearnPath(course, progress);
        } catch (e) {
            pathEl.innerHTML = '<p class="path-empty">Could not load the course path. Please try again.</p>';
        }
    }

    function passedSet(progress) {
        const results = progress?.lesson_results || {};
        const passed = new Set(
            Object.entries(results).filter(([, value]) => value && value.passed).map(([key]) => key)
        );
        for (const id of progress?.lessons_completed || []) passed.add(id);
        return passed;
    }

    function renderLearnPath(data, progress) {
        const done = passedSet(progress);
        let html = '<div class="path-intro"><h2>Your learning path</h2><p>Short, focused steps. Tap a lesson to begin — your progress saves automatically.</p><p><button class="explain-button" data-action="learn-placement">Check your level (informal, 12 questions)</button></p></div>';
        const resume = readSession();
        if (resume && resume.lessonId) {
            html += `<div class="path-banner"><span>Continue where you left off: <strong>${h(resume.title || 'your lesson')}</strong></span><button data-action="learn-resume">Resume</button></div>`;
        }
        if (!data.units || !data.units.length) {
            html += '<p class="path-empty">No published units for this level yet.</p>';
            pathEl.innerHTML = html;
            return;
        }
        let firstUndone = true;
        const allLessons = (data.units || []).flatMap(u => u.lessons || []);
        let globalIndex = -1;
        for (const unit of data.units) {
            html += `<section class="path-unit"><div class="path-unit-head"><h3>${h(unit.title)}</h3><small>${h(unit.titleFr || '')}</small></div>`;
            html += `<p class="session-text">${h(unit.description || '')}</p>`;
            html += '<div class="path-node-list">';
            const lessons = unit.lessons || [];
            for (let li = 0; li < lessons.length; li += 1) {
                const lesson = lessons[li];
                globalIndex += 1;
                const complete = done.has(lesson.id);
                const unlocked = globalIndex === 0 || done.has(allLessons[globalIndex - 1].id);
                const current = unlocked && firstUndone && !complete;
                const stars = Math.max(0, Math.min(3, progress?.lesson_results?.[lesson.id]?.stars || 0));
                if (current) firstUndone = false;
                const icon = unlocked ? (lesson.skillTags?.includes('speaking') ? '🎙️' :
                    lesson.skillTags?.includes('listening') ? '🎧' :
                    lesson.skillTags?.includes('exam') ? '🎯' : '📖') : '🔒';
                html += `<button class="path-node ${complete ? 'done' : ''} ${current ? 'current' : ''} ${unlocked ? '' : 'locked'}" data-action="learn-start" data-level="${h(data.level)}" data-id="${h(lesson.id)}" ${unlocked ? '' : 'disabled aria-disabled="true"'}>
                    <span class="path-node-icon" aria-hidden="true">${icon}</span>
                    <span><strong>${h(lesson.title)}</strong><small>Stage ${globalIndex + 1}/${allLessons.length} · ${h(lesson.estimatedMinutes || 10)} min${stars ? ` · ${'★'.repeat(stars)}` : ''}</small></span>
                    <span class="path-node-status">${complete ? `${'★'.repeat(stars) || '✓'} Passed` : unlocked ? current ? 'Start' : 'Next' : 'Locked'}</span>
                </button>`;
            }
            html += '</div></section>';
        }
        html += `<section class="path-unit"><div class="path-unit-head"><h3>Speaking missions</h3><small>Falou-style · listen, say, review</small></div>
            <p class="session-text">Short conversations with Pip. Your words are transcribed in the browser; audio is not stored by Parlez.</p>
            <div class="path-node-list"><button class="path-node" data-action="learn-speaking"><span class="path-node-icon">🎙️</span><span><strong>Start a speaking mission</strong><small>Pick a prompt, speak, then review with Pip</small></span><span class="path-node-status">Practice</span></button></div></section>`;
        html += `<section class="path-unit exam-missions"><div class="path-unit-head"><h3>Exam missions</h3><small>TEF / TCF Canada · original practice</small></div>
            <p class="session-text">Timed, format-based practice. Results are practice accuracy — not official scores, CEFR/NCLC levels, or immigration evidence.</p>
            <div class="path-node-list">
                <button class="path-node" data-action="learn-exam" data-type="TEF"><span class="path-node-icon">🎯</span><span><strong>TEF Canada mission</strong><small>Reading · listening · writing · speaking practice</small></span><span class="path-node-status">Practice</span></button>
                <button class="path-node" data-action="learn-exam" data-type="TCF"><span class="path-node-icon">🎯</span><span><strong>TCF Canada mission</strong><small>Reading · listening · writing · speaking practice</small></span><span class="path-node-status">Practice</span></button>
            </div></section>`;
        pathEl.innerHTML = html;
    }

    function showResumeBanner(saved) {
        // The banner is rendered by renderLearnPath; nothing extra needed here.
    }

    function buildSteps(lesson) {
        const steps = [{ kind: 'briefing', title: lesson.title, objectives: lesson.objectives || [] }];
        if (lesson.vocabulary?.length) {
            const words = lesson.vocabulary;
            const chunk = 5;
            for (let i = 0; i < words.length; i += chunk) {
                steps.push({ kind: 'vocabulary', words: words.slice(i, i + chunk) });
            }
        }
        for (const rule of lesson.grammar || []) {
            steps.push({ kind: 'grammar', rule });
        }
        if (lesson.dialogue?.length) steps.push({ kind: 'dialogue', lines: lesson.dialogue });
        for (const ex of lesson.exercises || []) steps.push({ kind: 'exercise', exercise: ex });
        if (lesson.transferTask) steps.push({ kind: 'transfer', text: lesson.transferTask, checks: lesson.selfCheck || [] });
        steps.push({ kind: 'checkpoint' });
        steps.push({ kind: 'results' });
        return steps;
    }

    async function startLearnSession(level, lessonId, savedSteps) {
        try {
            const r = await apiFetch(`/api/learn/courses/${encodeURIComponent(level)}/lessons/${encodeURIComponent(lessonId)}`);
            const lesson = await r.json();
            session = {
                level, lessonId,
                title: lesson.title || lessonId,
                steps: savedSteps || buildSteps(lesson),
                index: savedSteps ? 0 : 0,
                correct: 0, wrong: 0, mistakes: [],
            };
            saveSession();
            recordEvent('lesson_start', { level });
            showSession();
            renderLearnStep();
        } catch (e) {
            showToast('Could not start this lesson. Please try again.');
        }
    }

    function saveSession() {
        if (!session) return;
        try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ ...session, steps: undefined, stepCount: session.steps.length })); } catch (e) { /* quota */ }
    }
    function readSession() {
        try { return JSON.parse(sessionStorage.getItem(STORAGE_KEY) || 'null'); } catch (e) { return null; }
    }
    function clearSession() {
        try { sessionStorage.removeItem(STORAGE_KEY); } catch (e) { /* ignore */ }
    }

    function setProgress() {
        const pct = Math.round((session.index / Math.max(1, session.steps.length - 1)) * 100);
        const bar = sessionEl.querySelector('.progress-track span');
        if (bar) bar.style.width = `${pct}%`;
    }

    function shell(inner, actions) {
        sessionEl.innerHTML = `<div class="session-wrap"><div class="progress-track"><span></span></div>
            <div class="session-card"><img class="session-mascot" src="/static/mascot.svg" alt="" aria-hidden="true">${inner}
            <div class="session-actions">${actions || ''}</div></div></div>`;
        setProgress();
    }

    function renderLearnStep() {
        if (!session) return;
        const step = session.steps[session.index];
        if (!step) return;
        if (step.kind === 'briefing') {
            shell(`<p class="session-kicker">Lesson</p><h2 class="session-title">${h(step.title)}</h2>
                <ul class="session-list">${(step.objectives || []).map(o => `<li>${h(o)}</li>`).join('') || '<li>Practise the language of this lesson.</li>'}</ul>`,
                '<button data-action="learn-next">Start →</button><button class="ghost" data-action="learn-quit">Back to path</button>');
        } else if (step.kind === 'vocabulary') {
            const cards = step.words.map(w => `<button class="vocab-flip" data-action="learn-flip"><strong>${h(w.fr)}</strong><small>${h(w.en)}</small>${w.ipa ? `<span class="ipa">${h(w.ipa)}</span>` : ''}</button>`).join('');
            shell(`<p class="session-kicker">Vocabulary · tap a card</p><h2 class="session-title">Words to know</h2><div class="vocab-grid">${cards}</div>`,
                '<button data-action="learn-next">Continue →</button>');
        } else if (step.kind === 'grammar') {
            const r = step.rule || {};
            const examples = (r.examples || []).map(e => `<li>${h(e.fr)} — ${h(e.en)}</li>`).join('');
            shell(`<p class="session-kicker">Language focus</p><h2 class="session-title">${h(r.title || 'Grammar')}</h2>
                <p class="session-text">${h(r.explanation || '')}</p>
                ${r.tip ? `<p class="session-text"><strong>Tip:</strong> ${h(r.tip)}</p>` : ''}
                <ul class="session-list">${examples}</ul>`,
                '<button data-action="learn-next">Got it →</button>');
        } else if (step.kind === 'dialogue') {
            const lines = step.lines.map(l => `<div class="dialogue-line"><button data-action="speak" data-text="${h(l.fr)}" aria-label="Listen">🔊</button><span><strong>${h(l.name || l.speaker || 'A')}</strong><br>${h(l.fr)}<br><small>${h(l.en)}</small></span></div>`).join('');
            shell(`<p class="session-kicker">Conversation</p><h2 class="session-title">Listen and read</h2>${lines}`,
                '<button data-action="learn-next">Continue →</button>');
        } else if (step.kind === 'exercise') {
            renderLearnExercise(step.exercise);
        } else if (step.kind === 'transfer') {
            shell(`<p class="session-kicker">Use it</p><h2 class="session-title">Your turn</h2><p class="session-text">${h(step.text)}</p>
                <ul class="session-list">${(step.checks || []).map(c => `<li>${h(c)}</li>`).join('')}</ul>
                <p class="session-text">This task is unscored — it is for practice, not certification.</p>`,
                '<button data-action="learn-next">Finish →</button>');
        } else if (step.kind === 'checkpoint') {
            renderCheckpoint();
        } else if (step.kind === 'results') {
            renderLearnResults();
        }
    }

    function renderLearnExercise(exercise) {
        shell(`<p class="session-kicker">Practice</p><div id="learnExerciseMount"></div>
            <div id="learnExerciseFeedback" class="session-feedback" role="status" aria-live="polite" hidden></div>`,
            '<button id="learnContinue" data-action="learn-next" hidden>Continue →</button>');
        const mount = document.getElementById('learnExerciseMount');
        mount.innerHTML = (typeof renderExercise === 'function') ? renderExercise(exercise) : `<p>${h(exercise.prompt)}</p>`;

        const feedback = document.getElementById('learnExerciseFeedback');
        const continueBtn = document.getElementById('learnContinue');
        const container = mount.querySelector('.exercise-container');
        const observeTarget = container || mount;
        const observer = new MutationObserver(() => {
            const fb = observeTarget.querySelector('.quiz-feedback, .exercise-feedback');
            if (!fb || !fb.style.display || fb.style.display === 'none') return;
            feedback.hidden = false;
            const good = /^✓/.test(fb.textContent || '') || fb.classList.contains('correct');
            feedback.className = 'session-feedback ' + (good ? 'good' : 'bad');
            feedback.textContent = fb.textContent || (good ? 'Correct' : 'Try again');
            const ask = document.createElement('button');
            ask.type = 'button';
            ask.className = 'explain-button';
            ask.dataset.action = 'learn-explain';
            ask.textContent = 'Ask Pip why →';
            feedback.appendChild(ask);
            session.lastExercise = {
                prompt: exercise.prompt || '',
                answer: observeTarget.querySelector('.quiz-option.selected')?.textContent?.trim() ||
                        observeTarget.querySelector('.exercise-input')?.value?.trim() || '',
            };
            if (good) session.correct += 1;
            else { session.wrong += 1; session.mistakes.push(exercise.prompt || exercise.id); }
            saveSession();
            continueBtn.hidden = false;
            observer.disconnect();
        });
        observer.observe(observeTarget, { subtree: true, attributes: true, attributeFilter: ['style', 'class'] });
    }

    // ---------------- Dedicated speaking mission (Phase B/P6) ----------------

    const SPEAKING_PROMPTS_LEARN = [
        "Bonjour ! Comment t'appelles-tu ?",
        "D'où viens-tu et pourquoi apprends-tu le français ?",
        "Qu'est-ce que tu aimes faire le week-end ?",
        "Commande un café au lait dans un café.",
        "Explique en une minute pourquoi tu veux passer le TEF ou le TCF."
    ];
    let speakingMission = null;

    function startSpeakingMission() {
        if (typeof setBottomNav === 'function') setBottomNav('speak');
        const prompt = SPEAKING_PROMPTS_LEARN[Math.floor(Math.random() * SPEAKING_PROMPTS_LEARN.length)];
        speakingMission = { prompt, transcript: '', rating: 0 };
        showSession();
        shell(`<p class="session-kicker">Speaking mission · unofficial practice</p>
            <h2 class="session-title">Say it out loud</h2>
            <p class="session-text"><strong>${h(prompt)}</strong></p>
            <p class="session-text">Listen first, then say your answer. Your browser transcribes it; Parlez stores only the text you choose to save. This is not pronunciation scoring.</p>
            <div class="speaking-controls">
                <button data-action="speak" data-text="${h(prompt)}">🔊 Listen to the prompt</button>
                <button data-action="speaking-listen" id="speakingMic">🎙️ Speak your answer</button>
            </div>
            <label class="speaking-label" for="speakingAnswerLearn">Transcript (edit it before sending)</label>
            <textarea id="speakingAnswerLearn" class="speaking-textarea" rows="4" aria-label="Your answer as text">${h(speakingMission.transcript)}</textarea>
            <div id="speakingTutorReply" class="speaking-reply" aria-live="polite" hidden></div>
            <p class="session-text">How well did you manage? <span class="rating-row">${[1,2,3,4,5].map(n => `<button data-action="speaking-rate" data-rating="${n}">${n}</button>`).join('')}</span></p>`,
            '<button data-action="speaking-send">Send to Pip →</button><button data-action="speaking-save">Save attempt</button><button class="ghost" data-action="learn-quit">Back to path</button>');
    }

    window.startSpeakingListenLearn = function(button) {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) { showToast('Speech recognition is not supported here. Type your answer instead.'); return; }
        if (speakingMission?.recognition) { speakingMission.recognition.stop(); return; }
        const field = document.getElementById('speakingAnswerLearn');
        try {
            const recognition = new SR();
            speakingMission.recognition = recognition;
            recognition.lang = 'fr-FR'; recognition.continuous = false; recognition.interimResults = true;
            recognition.onstart = () => { button.textContent = '🎙️ Listening… tap to stop'; };
            recognition.onresult = (event) => {
                if (field) field.value = Array.from(event.results).map(r => r[0].transcript).join('');
            };
            const finish = () => { button.textContent = '🎙️ Speak your answer'; speakingMission.recognition = null; };
            recognition.onend = finish;
            recognition.onerror = (event) => {
                finish();
                if (event.error !== 'aborted') showToast('Microphone unavailable — type your answer instead.');
            };
            recognition.start();
        } catch (e) {
            speakingMission.recognition = null;
            showToast('Could not start the microphone. Type your answer instead.');
        }
    };

    async function sendSpeakingToPip() {
        const field = document.getElementById('speakingAnswerLearn');
        const reply = document.getElementById('speakingTutorReply');
        const text = (field?.value || '').trim();
        if (!text) { showToast('Say or type an answer first.'); return; }
        speakingMission.transcript = text;
        reply.hidden = false;
        reply.textContent = 'Pip is listening…';
        try {
            const r = await apiFetch('/api/chat', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: `Speaking practice prompt: ${speakingMission.prompt}. My answer: ${text}. Reply in French with one natural follow-up question and one gentle correction if needed.`,
                    mode: 'conversation', level: currentLevel || 'A1' }),
            });
            const data = await r.json();
            if (!r.ok) throw new Error(data.detail || 'failed');
            reply.innerHTML = parseMarkdown(data.response);
            if (typeof speakText === 'function') speakText(data.response);
        } catch (e) {
            reply.textContent = 'Pip could not reply right now. Try again in a moment.';
        }
    }

    async function saveSpeakingAttempt() {
        const field = document.getElementById('speakingAnswerLearn');
        speakingMission.transcript = (field?.value || '').trim();
        if (!speakingMission.transcript) { showToast('Nothing to save yet.'); return; }
        try {
            await apiFetch('/api/speaking/attempts', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ scenario: speakingMission.prompt,
                    transcript: speakingMission.transcript, self_rating: speakingMission.rating }),
            });
            showToast('Speaking attempt saved.');
        } catch (e) {
            showToast('Could not save this attempt.');
        }
    }

    // ---------------- Informal placement check ----------------

    let placement = null;

    async function startPlacement() {
        try {
            const data = await apiFetch('/api/assessment/placement').then(r => r.json());
            placement = { items: data.items, answers: {} };
            renderPlacement();
        } catch (e) {
            showToast('Could not load the level check.');
        }
    }

    function renderPlacement(result) {
        if (!placement) return;
        let html = '<p class="session-kicker">Assessment · informal practice</p><h2 class="session-title">Check your level</h2>' +
            `<p class="session-text">${result ? '' : 'Twelve short items. This is not a CEFR/NCLC test, an exam score, or an assessment of listening, speaking or writing.'}</p>`;
        if (result) {
            html += `<div class="session-feedback good"><strong>Practice band: ${h(result.levelEstimate)}</strong><br>${h(result.notice)}</div>`;
        }
        placement.items.forEach((item, index) => {
            html += `<div class="exam-item"><p class="session-text"><strong>${index + 1}. ${h(item.prompt)}</strong> <small>(${h(item.band)} practice)</small></p><div class="quiz-options">`;
            item.options.forEach((option, idx) => {
                const chosen = placement.answers[item.id] === idx;
                html += `<button class="quiz-option ${chosen ? 'selected' : ''}" data-action="placement-select" data-id="${h(item.id)}" data-idx="${idx}" ${result ? 'disabled' : ''}>${String.fromCharCode(65 + idx)}. ${h(option)}</button>`;
            });
            html += '</div></div>';
        });
        showSession();
        shell(html, result
            ? '<button data-action="learn-quit">Back to path</button>'
            : '<button data-action="placement-submit">See my practice band</button><button class="ghost" data-action="learn-quit">Cancel</button>');
        if (result) {
            const skills = Object.entries(result.bySkill).map(([k, v]) => `${k}: ${v.correct}/${v.total}`).join(' · ');
            const body = sessionEl.querySelector('.session-text');
            if (body) body.innerHTML = `<p>Coverage — ${h(skills)}</p><p>Not assessed: ${h(result.unassessedSkills.join(', '))}.</p>`;
        }
    }

    async function submitPlacement() {
        try {
            const result = await apiFetch('/api/assessment/placement/submit', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ answers: placement.answers }),
            }).then(r => r.json());
            recordEvent('placement_submit', { level: result.levelEstimate });
            renderPlacement(result);
        } catch (e) {
            showToast('Could not score the level check.');
        }
    }

    // ---------------- Phase C: in-session tutor help ----------------

    async function askPip(message, kicker) {
        let panel = document.getElementById('learnExplainPanel');
        if (!panel) {
            panel = document.createElement('div');
            panel.id = 'learnExplainPanel';
            panel.className = 'explain-panel';
            panel.setAttribute('role', 'dialog');
            panel.setAttribute('aria-modal', 'true');
            panel.innerHTML = '<div class="explain-box"><button class="explain-close" data-action="learn-close-explain" aria-label="Close">×</button><p class="session-kicker">Ask Pip</p><div class="explain-body">Thinking…</div></div>';
            document.body.appendChild(panel);
        }
        panel.querySelector('.session-kicker').textContent = kicker || 'Ask Pip';
        recordEvent('coach_request', { source: kicker?.includes('coach') ? 'coach_card' : 'explain' });
        const body = panel.querySelector('.explain-body');
        try {
            const r = await apiFetch('/api/chat', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message, mode: 'grammar', level: session?.level || currentLevel || 'A1' }),
            });
            const data = await r.json();
            if (!r.ok) throw new Error(data.detail || 'failed');
            body.textContent = data.response;
        } catch (e) {
            body.textContent = 'Pip could not answer right now. Try again in a moment.';
        }
    }

    async function askPipWhy() {
        if (!session?.lastExercise) return;
        await askPip(
            `Explain this French exercise in two short sentences, then give one correct example. Exercise: ${session.lastExercise.prompt}. Learner answered: ${session.lastExercise.answer || '(no answer)'}. Stay in French-learning scope.`,
            'Ask Pip · why?',
        );
    }

    // ---------------- Phase B: exam missions ----------------

    let examMission = null;

    async function appendResourceLinks() {
        try {
            const data = await apiFetch('/api/practice/resources').then(r => r.json());
            const card = sessionEl.querySelector('.session-card');
            if (!card) return;
            const box = document.createElement('details');
            box.className = 'session-resources';
            box.innerHTML = '<summary>Official samples &amp; open question banks (licence-aware)</summary>' +
                '<ul>' + data.resources.map(r => `<li><a href="${h(r.url)}" target="_blank" rel="noopener">${h(r.name)}</a> · ${h(r.licence)} · ${r.mode === 'link_only' ? 'link only' : 'adapt with attribution'}</li>`).join('') + '</ul>' +
                `<p class="session-text"><small>${h(data.notice)}</small></p>`;
            card.appendChild(box);
        } catch (e) { /* non-essential */ }
    }

    function showExamBriefing(exam) {
        showSession();
        shell(`<p class="session-kicker">Exam mission · unofficial practice</p>
            <h2 class="session-title">${h(exam)} Canada practice</h2>
            <p class="session-text">Original items written from published task specifications. Timed like the real format, but these are <strong>not</strong> real past questions and the result is <strong>not</strong> an official score.</p>
            <div class="vocab-grid">
                <button class="vocab-flip" data-action="exam-mission" data-exam="${h(exam)}" data-skill="reading"><strong>Reading</strong><small>Timed comprehension set →</small></button>
                <button class="vocab-flip" data-action="exam-mission" data-exam="${h(exam)}" data-skill="listening"><strong>Listening</strong><small>Audio script + questions →</small></button>
            </div>
            <p class="session-text">Official samples for reference: <a href="https://www.lefrancaisdesaffaires.fr/candidat/test-evaluation-francais/tef-canada/preparation/" target="_blank" rel="noopener">TEF (CCI)</a> · <a href="https://www.france-education-international.fr/en/test/exemples-epreuves-tcf" target="_blank" rel="noopener">TCF (FEI)</a></p>`,
            '<button class="ghost" data-action="learn-quit">Back to path</button>');
        appendResourceLinks();
    }

    async function startExamMission(exam, skill) {
        try {
            const r = await apiFetch(`/api/exam/practice/${encodeURIComponent(exam)}/${encodeURIComponent(skill)}`);
            const data = await r.json();
            examMission = { exam, skill, items: data.items, answers: {}, seconds: 180 };
            recordEvent('exam_mission_start', { exam, skill });
            renderExamMission();
            clearInterval(examMission.timer);
            examMission.timer = setInterval(() => {
                examMission.seconds -= 1;
                const el = document.getElementById('examTimer');
                if (el) el.textContent = `${Math.floor(examMission.seconds / 60)}:${String(examMission.seconds % 60).padStart(2, '0')}`;
                if (examMission.seconds <= 0) {
                    clearInterval(examMission.timer);
                    submitExamMission();
                }
            }, 1000);
        } catch (e) {
            showToast('Could not load this exam mission.');
        }
    }

    function renderExamMission(result) {
        if (!examMission) return;
        if (examMission.timer) clearInterval(examMission.timer);
        const mission = examMission;
        let html = `<p class="session-kicker">${h(mission.exam)} · ${h(mission.skill)} · unofficial practice</p>
            <h2 class="session-title">Exam mission <span id="examTimer" class="hud-item">3:00</span></h2>
            <p class="session-text">Read each item and choose one answer. Practice accuracy only — not an official score, CEFR/NCLC level, or immigration evidence.</p>`;
        if (result) {
            html += `<div class="session-feedback ${result.accuracyPercent >= 60 ? 'good' : 'bad'}"><strong>${h(result.correct)} / ${h(result.total)} correct (${h(result.accuracyPercent)}%)</strong><br>${h(result.notice)}</div>`;
        }
        mission.items.forEach((item, index) => {
            const graded = result?.results?.find(x => x.id === item.id);
            html += `<div class="exam-item"><p class="session-text"><strong>${index + 1}. ${h(item.prompt)}</strong></p>
                <p class="session-text">${h(item.passage)}</p><div class="quiz-options">`;
            item.options.forEach((option, idx) => {
                let cls = 'quiz-option';
                if (graded) {
                    if (idx === graded.correctIndex) cls += ' correct';
                    else if (mission.answers[item.id] === idx) cls += ' incorrect';
                } else if (mission.answers[item.id] === idx) cls += ' selected';
                html += `<button class="${cls}" data-action="exam-select" data-id="${h(item.id)}" data-idx="${idx}" ${graded ? 'disabled' : ''}>${String.fromCharCode(65 + idx)}. ${h(option)}</button>`;
            });
            html += '</div>';
            if (graded) html += `<p class="session-text">${h(graded.explanation)}</p>`;
            html += `<p class="session-text"><small>Format fact: ${h(item.specFact)} <a href="${h(item.specSource)}" target="_blank" rel="noopener">Source</a></small></p></div>`;
        });
        shell(html, result
            ? '<button data-action="learn-quit">Back to path</button>'
            : '<button data-action="exam-submit">Submit answers</button><button class="ghost" data-action="learn-quit">Quit</button>');
        if (result) {
            const timerEl = document.getElementById('examTimer');
            if (timerEl) timerEl.textContent = 'done';
            appendResourceLinks();
        }
    }

    async function submitExamMission() {
        if (!examMission) return;
        try {
            const r = await apiFetch('/api/exam/practice/grade', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ exam: examMission.exam, skill: examMission.skill, answers: examMission.answers }),
            });
            const result = await r.json();
            examMission.result = result;
            recordEvent('exam_mission_submit', { exam: examMission.exam, skill: examMission.skill });
            renderExamMission(result);
            if (typeof updateXP === 'function') {
                const p = await apiFetch('/api/progress').then(x => x.json()).catch(() => null);
                if (p && p.xp) updateXP(p.xp);
            }
        } catch (e) {
            showToast('Could not grade this mission. Please try again.');
        }
    }

    // ---------------- Lesson checkpoint + unlock ----------------

    let checkpoint = null;

    async function renderCheckpoint() {
        shell('<p class="session-kicker">Checkpoint · server graded</p><h2 class="session-title">Prove it</h2>'
            + '<p class="session-text">A short comprehensive test of this lesson. Answer at least 70% correctly to unlock the next lesson.</p>'
            + '<div id="checkpointMount"><p class="session-text">Loading checkpoint…</p></div>',
            '<button data-action="cp-submit" id="cpSubmit">Submit answers</button>');
        try {
            const data = await apiFetch(`/api/learn/courses/${encodeURIComponent(session.level)}/lessons/${encodeURIComponent(session.lessonId)}/checkpoint`).then(r => r.json());
            checkpoint = { questions: data.questions, answers: {}, passPercent: data.passPercent || 70, result: null };
            renderCheckpointQuestions();
        } catch (e) {
            document.getElementById('checkpointMount').innerHTML = '<p class="session-text">Could not load the checkpoint.</p>';
        }
    }

    function renderCheckpointQuestions(result) {
        const mount = document.getElementById('checkpointMount');
        if (!mount || !checkpoint) return;
        let html = '';
        if (result) {
            html += `<div class="session-feedback ${result.passed ? 'good' : 'bad'}"><strong>${h(result.score)}/${h(result.total)} (${h(result.percent)}%)</strong> — ${result.passed ? 'Checkpoint passed! Unlocking the next step…' : 'Not quite — review and try again.'}</div>`;
        }
        checkpoint.questions.forEach((question, index) => {
            html += `<div class="exam-item"><p class="session-text"><strong>${index + 1}. ${h(question.prompt)}</strong></p><div class="quiz-options">`;
            question.options.forEach((option, idx) => {
                const chosen = checkpoint.answers[question.id] === idx;
                let cls = 'quiz-option' + (chosen ? ' selected' : '');
                if (result) {
                    const item = result.review.find(x => x.id === question.id);
                    if (item && item.correct && idx === chosen) cls += ' correct';
                    else if (item && !item.correct && idx === chosen) cls += ' incorrect';
                }
                html += `<button class="${cls}" data-action="cp-select" data-id="${h(question.id)}" data-idx="${idx}" ${result ? 'disabled' : ''}>${String.fromCharCode(65 + idx)}. ${h(option)}</button>`;
            });
            html += '</div></div>';
        });
        mount.innerHTML = html || '<p class="session-text">No checkpoint questions available for this lesson.</p>';
        const submit = document.getElementById('cpSubmit');
        if (submit) {
            submit.hidden = Boolean(result);
            if (result && !result.passed) {
                submit.hidden = false;
                submit.textContent = 'Try again';
            }
        }
        if (result && result.passed) {
            celebrate();
            showUnlockOverlay();
        }
    }

    async function submitCheckpoint() {
        if (!checkpoint) return;
        try {
            const result = await apiFetch(`/api/learn/courses/${encodeURIComponent(session.level)}/lessons/${encodeURIComponent(session.lessonId)}/checkpoint/submit`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ answers: checkpoint.answers }),
            }).then(r => r.json());
            checkpoint.result = result;
            renderCheckpointQuestions(result);
        } catch (e) {
            showToast('Could not grade the checkpoint. Please try again.');
        }
    }

    function unlockTarget() {
        if (!course) return null;
        const units = course.units || [];
        const flat = units.flatMap(u => u.lessons || []);
        const index = flat.findIndex(l => l.id === session.lessonId);
        if (index < 0) return { type: 'course', name: 'the whole A1–B2 path' };
        if (index < flat.length - 1) {
            const next = flat[index + 1];
            const unitIndex = units.findIndex(u => (u.lessons || []).some(l => l.id === session.lessonId));
            const nextUnitIndex = units.findIndex(u => (u.lessons || []).some(l => l.id === next.id));
            if (nextUnitIndex !== unitIndex) {
                return { type: 'chapter', name: units[nextUnitIndex].title, lessonName: next.title };
            }
            return { type: 'lesson', name: next.title };
        }
        const levels = levelEl ? [...levelEl.options].map(o => o.value) : [];
        const current = levels.indexOf(session.level);
        if (current >= 0 && current < levels.length - 1) {
            return { type: 'level', name: levels[current + 1], fromLevel: session.level };
        }
        return { type: 'course', name: 'the whole A1–B2 path' };
    }

    function playSuccessTone() {
        try {
            const Ctx = window.AudioContext || window.webkitAudioContext;
            if (!Ctx) return;
            const ctx = new Ctx();
            [523.25, 659.25, 783.99].forEach((frequency, index) => {
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'sine';
                osc.frequency.value = frequency;
                gain.gain.setValueAtTime(0.0001, ctx.currentTime + index * 0.12);
                gain.gain.exponentialRampToValueAtTime(0.16, ctx.currentTime + index * 0.12 + 0.02);
                gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + index * 0.12 + 0.35);
                osc.connect(gain).connect(ctx.destination);
                osc.start(ctx.currentTime + index * 0.12);
                osc.stop(ctx.currentTime + index * 0.12 + 0.36);
            });
            setTimeout(() => ctx.close(), 900);
        } catch (e) { /* audio is decorative */ }
    }

    function showLevelUpOverlay(target) {
        const current = (target.fromLevel || session.level || 'A1').toUpperCase();
        const next = String(target.name || '').toUpperCase();
        const overlay = document.createElement('div');
        overlay.className = 'unlock-overlay levelup-overlay';
        overlay.setAttribute('role', 'dialog');
        overlay.setAttribute('aria-modal', 'true');
        overlay.innerHTML = `<div class="levelup-card">
            <div class="levelup-rays" aria-hidden="true"></div>
            <p class="session-kicker">Checkpoint complete</p>
            <h2 class="levelup-title">LEVEL UP!</h2>
            <div class="levelup-stairs" aria-hidden="true">
                <span class="step step-3"></span><span class="step step-2"></span><span class="step step-1"></span>
                <img src="/static/mascot.svg" alt="" class="levelup-mascot">
                <span class="sparkle s1">✦</span><span class="sparkle s2">✦</span><span class="sparkle s3">✦</span>
            </div>
            <div class="levelup-levels">
                <span class="level-chip old">${h(current)}</span>
                <span class="levelup-arrow">→</span>
                <span class="level-chip new">${h(next)}</span>
            </div>
            <p class="session-text"><strong>Level ${h(next)}</strong> is now unlocked. Onwards !</p>
            <button class="btn-primary" data-action="unlock-continue">Continue to ${h(next)} →</button>
        </div>`;
        document.body.appendChild(overlay);
        playSuccessTone();
    }

    function showUnlockOverlay() {
        const target = unlockTarget();
        if (target.type === 'level') {
            showLevelUpOverlay(target);
            return;
        }
        const overlay = document.createElement('div');
        overlay.className = 'unlock-overlay';
        overlay.setAttribute('role', 'dialog');
        overlay.setAttribute('aria-modal', 'true');
        overlay.innerHTML = `<div class="unlock-card">
            <div class="unlock-lock" aria-hidden="true">🔓</div>
            <img src="/static/mascot.svg" alt="" class="unlock-mascot">
            <p class="session-kicker">Checkpoint passed</p>
            <h2 class="session-title">${target.type === 'chapter' ? 'New chapter unlocked!' : 'New lesson unlocked!'}</h2>
            <p class="session-text"><strong>${h(target.name)}</strong>${target.lessonName ? ` — starting with “${h(target.lessonName)}”` : ''} is now available.</p>
            <button class="btn-primary" data-action="unlock-continue">Continue →</button>
        </div>`;
        document.body.appendChild(overlay);
        playSuccessTone();
    }

    function celebrate() {
        const colors = ['#a11b36', '#f2a93b', '#e8b64b', '#0f7a6c', '#2f8f5b', '#c33a4e'];
        for (let i = 0; i < 36; i += 1) {
            const piece = document.createElement('span');
            piece.className = 'confetti-piece';
            piece.style.left = `${Math.random() * 100}%`;
            piece.style.background = colors[i % colors.length];
            piece.style.animationDelay = `${Math.random() * 0.5}s`;
            piece.style.animationDuration = `${1.8 + Math.random()}s`;
            document.body.appendChild(piece);
            setTimeout(() => piece.remove(), 3200);
        }
    }

    function renderLearnResults() {
        const total = session.correct + session.wrong || 1;
        const accuracy = Math.round((session.correct / total) * 100);
        shell(`<p class="session-kicker">Session complete</p><h2 class="session-title">Bien joué !</h2>
            <div class="results-stats"><div><strong>${session.correct}</strong><span>Correct</span></div>
            <div><strong>${accuracy}%</strong><span>Accuracy</span></div>
            <div><strong>${session.mistakes.length}</strong><span>To review</span></div></div>
            <p class="session-text">${session.mistakes.length ? 'Mistakes in this session: ' + h(session.mistakes.slice(0, 3).join(', ')) : 'No mistakes — excellent work.'}</p>
            <p class="session-text">Practice accuracy is not an official score or a CEFR/NCLC level.</p>`,
            '<button data-action="learn-coach">Coach card ✨</button><button data-action="learn-share">Share progress</button><button data-action="learn-quit">Back to path</button>');
        const mascot = sessionEl.querySelector('.session-mascot');
        if (mascot) {
            mascot.classList.add('mascot-celebrate');
            setTimeout(() => mascot.classList.remove('mascot-celebrate'), 700);
        }
        celebrate();
        clearSession();
        recordEvent('lesson_complete', { level: session.level });
        fetch('/api/progress/complete-lesson', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lesson_id: session.lessonId, score: accuracy }),
        }).then(r => r.json()).then(d => { if (typeof updateXP === 'function' && d.total_xp) updateXP(d.total_xp); }).catch(() => {});
    }

    function nextStep() {
        if (!session) return;
        session.index += 1;
        saveSession();
        renderLearnStep();
    }

    document.addEventListener('click', (event) => {
        const btn = event.target.closest('[data-action]');
        if (!btn) return;
        const action = btn.dataset.action;
        if (action === 'learn-start') {
            startLearnSession(btn.dataset.level, btn.dataset.id);
        } else if (action === 'learn-resume') {
            const saved = readSession();
            if (saved) startLearnSession(saved.level, saved.lessonId);
        } else if (action === 'learn-next') {
            nextStep();
        } else if (action === 'learn-quit') {
            clearSession();
            session = null;
            showPath();
            if (course) renderLearnPath(course, { lessons_completed: [] });
        } else if (action === 'learn-flip') {
            btn.classList.toggle('flipped');
            const text = btn.querySelector('small');
            if (text) text.textContent = btn.classList.contains('flipped') ? 'Tap to hide' : text.dataset.original || text.textContent;
        } else if (action === 'learn-speaking') {
            if (typeof setBottomNav === 'function') setBottomNav('speak');
            if (typeof showLearnView === 'function') showLearnView().then(() => startSpeakingMission());
            else startSpeakingMission();
        } else if (action === 'speaking-listen') {
            if (typeof window.startSpeakingListenLearn === 'function') window.startSpeakingListenLearn(btn);
        } else if (action === 'speaking-rate') {
            speakingMission.rating = parseInt(btn.dataset.rating, 10);
            btn.parentElement.querySelectorAll('button').forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
        } else if (action === 'speaking-send') {
            sendSpeakingToPip();
        } else if (action === 'speaking-save') {
            saveSpeakingAttempt();
        } else if (action === 'cp-select') {
            if (!checkpoint || checkpoint.result) return;
            checkpoint.answers[btn.dataset.id] = parseInt(btn.dataset.idx, 10);
            btn.parentElement.querySelectorAll('.quiz-option').forEach(o => o.classList.remove('selected'));
            btn.classList.add('selected');
        } else if (action === 'cp-submit') {
            submitCheckpoint();
        } else if (action === 'unlock-continue') {
            document.querySelector('.unlock-overlay')?.remove();
            showPath();
            (async () => {
                const fresh = await apiFetch('/api/progress').then(r => r.json()).catch(() => ({}));
                await loadLearnLevels();
                if (course) renderLearnPath(course, fresh);
            })();
        } else if (action === 'learn-placement') {
            if (typeof showLearnView === 'function') showLearnView().then(() => startPlacement());
            else startPlacement();
        } else if (action === 'placement-select') {
            if (!placement) return;
            placement.answers[btn.dataset.id] = parseInt(btn.dataset.idx, 10);
            btn.parentElement.querySelectorAll('.quiz-option').forEach(o => o.classList.remove('selected'));
            btn.classList.add('selected');
        } else if (action === 'placement-submit') {
            submitPlacement();
        } else if (action === 'learn-exam') {
            showExamBriefing(btn.dataset.type);
        } else if (action === 'exam-mission') {
            startExamMission(btn.dataset.exam, btn.dataset.skill);
        } else if (action === 'exam-select') {
            if (!examMission) return;
            examMission.answers[btn.dataset.id] = parseInt(btn.dataset.idx, 10);
            btn.parentElement.querySelectorAll('.quiz-option').forEach(o => o.classList.remove('selected'));
            btn.classList.add('selected');
        } else if (action === 'exam-submit') {
            submitExamMission();
        } else if (action === 'learn-explain') {
            askPipWhy();
        } else if (action === 'learn-close-explain') {
            document.getElementById('learnExplainPanel')?.remove();
        } else if (action === 'learn-coach') {
            const mistakes = session?.mistakes?.length ? session.mistakes.join('; ') : 'none';
            askPip(`Give me three short, kind study tips for a French learner who just finished a lesson and missed these items: ${mistakes}. Also suggest one next step. Practice only, no exam score.`, 'Pip · your coach card');
        } else if (action === 'learn-share') {
            recordEvent('share_progress', { source: 'results' });
            const text = `I practised ${session?.title || 'French'} on Parlez — ${session?.correct || 0} correct answers. Practice makes progress!`;
            if (navigator.clipboard) {
                navigator.clipboard.writeText(text).then(() => showToast('Progress card copied to clipboard.'));
            } else {
                showToast(text);
            }
        } else if (action === 'learn-go-path') {
            showLearnView();
        } else if (action === 'learn-go-practice') {
            if (typeof setBottomNav === 'function') setBottomNav('practice');
            if (typeof window.showPractice === 'function') window.showPractice();
            else showToast('Practice is not available yet.');
        } else if (action === 'learn-go-tutor') {
            if (typeof showChatView === 'function') showChatView();
        } else if (action === 'learn-go-rewards') {
            if (typeof setBottomNav === 'function') setBottomNav('rewards');
            if (typeof window.showRewards === 'function') window.showRewards();
        }
    });

    levelEl?.addEventListener('change', () => loadLearnPath(levelEl.value));

    window.startLearnSession = startLearnSession;
    window.startPlacement = startPlacement;

    // Hook the Learn view into app startup once app.js has loaded.
    const originalInit = window.initApp;
    window.initApp = async function() {
        if (typeof originalInit === 'function') await originalInit();
        if (typeof showLearnView === 'function') await showLearnView();
    };
})();
