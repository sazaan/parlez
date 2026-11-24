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

    function h(value) {
        return typeof escapeHtml === 'function' ? escapeHtml(value) : String(value ?? '');
    }

    function showPath() {
        if (!sessionEl) return;
        sessionEl.hidden = true;
        if (pathEl) pathEl.style.display = '';
        document.querySelectorAll('.learn-bottom-nav button').forEach(b => b.classList.remove('active'));
        document.querySelector('[data-action="learn-go-path"]')?.classList.add('active');
    }

    function showSession() {
        if (!sessionEl) return;
        sessionEl.hidden = false;
        if (pathEl) pathEl.style.display = 'none';
    }

    window.showLearnView = async function() {
        if (!viewEl) return;
        document.getElementById('chatView').style.display = 'none';
        document.getElementById('toolView').style.display = 'none';
        viewEl.style.display = 'flex';
        document.getElementById('chatTitle').textContent = 'Learn French — your path';
        document.getElementById('btnBackToChat').style.display = 'none';
        if (typeof setCoursesNavActive === 'function') setCoursesNavActive(false);
        if (!levelEl.options.length) await loadLearnLevels();
        await loadLearnPath(levelEl.value || currentLevel || 'A1');
        const saved = readSession();
        if (saved && saved.lessonId) showResumeBanner(saved);
        else showPath();
    };

    async function loadLearnLevels() {
        try {
            const r = await apiFetch('/api/courses');
            const levels = await r.json();
            const preferred = currentLevel || 'A1';
            levelEl.innerHTML = levels.map(l =>
                `<option value="${h(l.level)}">${h(l.level)} · ${h(l.name || l.title || '')}</option>`
            ).join('');
            if ([...levelEl.options].some(o => o.value === preferred)) levelEl.value = preferred;
        } catch (e) {
            levelEl.innerHTML = '<option value="A1">A1</option>';
        }
    }

    async function loadLearnPath(level) {
        if (!pathEl) return;
        pathEl.innerHTML = '<p class="path-empty">Loading your path…</p>';
        try {
            const [courseRes, progressRes] = await Promise.all([
                apiFetch(`/api/courses/${encodeURIComponent(level)}`),
                apiFetch('/api/progress'),
            ]);
            course = await courseRes.json();
            const progress = await progressRes.json();
            renderLearnPath(course, progress);
        } catch (e) {
            pathEl.innerHTML = '<p class="path-empty">Could not load the course path. Please try again.</p>';
        }
    }

    function renderLearnPath(data, progress) {
        const done = new Set(progress?.lessons_completed || []);
        let html = '<div class="path-intro"><h2>Your learning path</h2><p>Short, focused steps. Tap a lesson to begin — your progress saves automatically.</p></div>';
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
        for (const unit of data.units) {
            html += `<section class="path-unit"><div class="path-unit-head"><h3>${h(unit.title)}</h3><small>${h(unit.titleFr || '')}</small></div>`;
            html += `<p class="session-text">${h(unit.description || '')}</p>`;
            html += '<div class="path-node-list">';
            for (const lesson of unit.lessons || []) {
                const complete = done.has(lesson.id);
                const current = firstUndone && !complete;
                if (current) firstUndone = false;
                const icon = lesson.skillTags?.includes('speaking') ? '🎙️' :
                    lesson.skillTags?.includes('listening') ? '🎧' :
                    lesson.skillTags?.includes('exam') ? '🎯' : '📖';
                html += `<button class="path-node ${complete ? 'done' : ''} ${current ? 'current' : ''}" data-action="learn-start" data-level="${h(data.level)}" data-id="${h(lesson.id)}">
                    <span class="path-node-icon" aria-hidden="true">${icon}</span>
                    <span><strong>${h(lesson.title)}</strong><small>${h(lesson.titleFr || '')} · ${h(lesson.estimatedMinutes || 10)} min</small></span>
                    <span class="path-node-status">${complete ? '✓ Done' : current ? 'Start' : 'Next'}</span>
                </button>`;
            }
            html += '</div></section>';
        }
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
        steps.push({ kind: 'results' });
        return steps;
    }

    async function startLearnSession(level, lessonId, savedSteps) {
        try {
            const r = await apiFetch(`/api/courses/${encodeURIComponent(level)}/lessons/${encodeURIComponent(lessonId)}`);
            const lesson = await r.json();
            session = {
                level, lessonId,
                title: lesson.title || lessonId,
                steps: savedSteps || buildSteps(lesson),
                index: savedSteps ? 0 : 0,
                correct: 0, wrong: 0, mistakes: [],
            };
            saveSession();
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

    // ---------------- Phase C: in-session tutor help ----------------

    async function askPipWhy() {
        if (!session?.lastExercise) return;
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
        const body = panel.querySelector('.explain-body');
        try {
            const message = `Explain this French exercise in two short sentences, then give one correct example. Exercise: ${session.lastExercise.prompt}. Learner answered: ${session.lastExercise.answer || '(no answer)'}. Stay in French-learning scope.`;
            const r = await apiFetch('/api/chat', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message, mode: 'grammar', level: session.level || currentLevel || 'A1' }),
            });
            const data = await r.json();
            if (!r.ok) throw new Error(data.detail || 'failed');
            body.textContent = data.response;
        } catch (e) {
            body.textContent = 'Pip could not answer right now. Try again in a moment.';
        }
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
            renderExamMission(result);
            if (typeof updateXP === 'function') {
                const p = await apiFetch('/api/progress').then(x => x.json()).catch(() => null);
                if (p && p.xp) updateXP(p.xp);
            }
        } catch (e) {
            showToast('Could not grade this mission. Please try again.');
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
            '<button data-action="learn-quit">Back to path</button>');
        clearSession();
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
        } else if (action === 'learn-go-path') {
            showLearnView();
        } else if (action === 'learn-go-practice') {
            if (typeof window.reviewCurrentCard === 'function') window.startFlashcardReview?.();
            else showToast('Practice tools are in the Quick Practice menu.');
        } else if (action === 'learn-go-tutor') {
            if (typeof showChatView === 'function') showChatView();
        } else if (action === 'learn-go-rewards') {
            if (typeof window.showRewards === 'function') window.showRewards();
        }
    });

    levelEl?.addEventListener('change', () => loadLearnPath(levelEl.value));

    // Hook the Learn view into app startup once app.js has loaded.
    const originalInit = window.initApp;
    window.initApp = async function() {
        if (typeof originalInit === 'function') await originalInit();
        if (typeof showLearnView === 'function') await showLearnView();
    };
})();
