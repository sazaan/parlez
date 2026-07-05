// ============================================================
// Authentication
// ============================================================
let authToken = localStorage.getItem('parlez_token');
let currentUser = null;

async function checkAuth() {
    if (!authToken) {
        showAuthScreen();
        return false;
    }
    try {
        const r = await fetch('/api/auth/me', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (r.ok) {
            currentUser = await r.json();
            showApp();
            initApp();
            return true;
        } else {
            localStorage.removeItem('parlez_token');
            showAuthScreen();
            return false;
        }
    } catch(e) {
        localStorage.removeItem('parlez_token');
        showAuthScreen();
        return false;
    }
}

function showAuthScreen() {
    document.getElementById('authScreen').style.display = 'flex';
    document.getElementById('appContainer').style.display = 'none';
}

function showApp() {
    document.getElementById('authScreen').style.display = 'none';
    document.getElementById('appContainer').style.display = 'flex';
}

function authHeaders() {
    return { 'Authorization': `Bearer ${authToken}`, 'Content-Type': 'application/json' };
}

async function apiFetch(url, options = {}) {
    const headers = { ...authHeaders(), ...options.headers };
    const r = await fetch(url, { ...options, headers });
    if (r.status === 401) {
        logout();
        throw new Error('Session expired');
    }
    return r;
}

// Auth form handling
let isSignup = false;
const authForm = document.getElementById('authForm');
const authTitle = document.getElementById('authTitle');
const authSubtitle = document.getElementById('authSubtitle');
const authSubmit = document.getElementById('authSubmit');
const authToggleLink = document.getElementById('authToggleLink');
const authToggle = document.getElementById('authToggle');
const authError = document.getElementById('authError');
const nameGroup = document.getElementById('nameGroup');

authToggleLink?.addEventListener('click', (e) => {
    e.preventDefault();
    isSignup = !isSignup;
    authTitle.textContent = isSignup ? 'Create Account' : 'Welcome Back';
    authSubtitle.textContent = isSignup ? 'Sign up to start learning French' : 'Log in to continue learning French';
    authSubmit.textContent = isSignup ? 'Sign Up' : 'Log In';
    authToggle.innerHTML = isSignup ? 'Already have an account? <a href="#" id="authToggleLink">Log In</a>' : 'Don\'t have an account? <a href="#" id="authToggleLink">Sign Up</a>';
    nameGroup.style.display = isSignup ? 'block' : 'none';
    authError.style.display = 'none';
    // Re-bind the toggle link
    document.getElementById('authToggleLink')?.addEventListener('click', (e2) => {
        e2.preventDefault();
        authToggleLink.click();
    });
});

authForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    authError.style.display = 'none';
    
    const username = document.getElementById('authUsername').value.trim();
    const password = document.getElementById('authPassword').value;
    const name = document.getElementById('authName').value.trim();
    
    if (!username || !password) {
        authError.textContent = 'Please fill in all fields';
        authError.style.display = 'block';
        return;
    }
    
    try {
        const endpoint = isSignup ? '/api/auth/signup' : '/api/auth/login';
        const body = isSignup ? { username, password, name } : { username, password };
        
        const r = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        
        const data = await r.json();
        
        if (!r.ok) {
            authError.textContent = data.detail || 'Authentication failed';
            authError.style.display = 'block';
            return;
        }
        
        authToken = data.token;
        currentUser = data.user;
        localStorage.setItem('parlez_token', authToken);
        showApp();
        // Initialize app after auth
        initApp();
    } catch(e) {
        authError.textContent = 'Network error. Please try again.';
        authError.style.display = 'block';
    }
});

async function logout() {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
    } catch(e) {}
    authToken = null;
    currentUser = null;
    localStorage.removeItem('parlez_token');
    showAuthScreen();
}

// ============================================================
// Main App
// ============================================================
const messagesContainer = document.getElementById('messages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const chatTitle = document.getElementById('chatTitle');
const sidebar = document.getElementById('sidebar');
const sidebarBackdrop = document.getElementById('sidebarBackdrop');
const toggleSidebar = document.getElementById('toggleSidebar');
const newChatBtn = document.getElementById('newChat');
const chatList = document.getElementById('chatList');
const courseList = document.getElementById('courseList');
const scenarioList = document.getElementById('scenarioList');
const settingsModal = document.getElementById('settingsModal');
const closeSettings = document.getElementById('closeSettings');
const clearHistoryBtn = document.getElementById('clearHistory');
const levelSelector = document.getElementById('levelSelector');
const btnBackToChat = document.getElementById('btnBackToChat');
const voiceButton = document.getElementById('voiceButton');

let currentConvId = null;
let currentLevel = 'A1';
let isGenerating = false;
let recognition = null;
let isRecording = false;

const LEVEL_NAMES = { 'A1': 'Débutant', 'A2': 'Élémentaire', 'B1': 'Intermédiaire', 'B2': 'Avancé' };

// ============================================================
// TTS
// ============================================================
let currentAudio = null;
let currentSpeakingText = '';

async function speakText(text, lang = 'fr') {
    try {
        // If same text is playing, stop it (toggle behavior)
        if (currentAudio && currentSpeakingText === text) {
            currentAudio.pause();
            currentAudio = null;
            currentSpeakingText = '';
            return;
        }
        
        // Stop any currently playing audio
        if (currentAudio) {
            currentAudio.pause();
            currentAudio = null;
        }
        
        currentSpeakingText = text;
        const response = await fetch('/api/tts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text.substring(0, 500), lang })
        });
        if (!response.ok) return;
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        currentAudio = new Audio(url);
        currentAudio.onended = () => { currentAudio = null; currentSpeakingText = ''; };
        currentAudio.onerror = () => { currentAudio = null; currentSpeakingText = ''; };
        await currentAudio.play();
    } catch (e) { console.error('TTS error:', e); }
}

function stopSpeaking() {
    if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
        currentSpeakingText = '';
    }
}

// ============================================================
// Voice Input
// ============================================================
function initVoice() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return;
    recognition = new SR();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'fr-FR';
    recognition.onstart = () => { isRecording = true; document.getElementById('voiceButton').classList.add('recording'); document.getElementById('voiceStatus').style.display = 'inline'; };
    recognition.onresult = (e) => { messageInput.value = Array.from(e.results).map(r => r[0].transcript).join(''); autoResize(); updateSendButton(); };
    recognition.onend = () => { isRecording = false; document.getElementById('voiceButton').classList.remove('recording'); document.getElementById('voiceStatus').style.display = 'none'; };
    recognition.onerror = () => { isRecording = false; document.getElementById('voiceButton').classList.remove('recording'); document.getElementById('voiceStatus').style.display = 'none'; };
}

function toggleVoice() {
    if (!recognition) { alert('Voice not supported. Use Chrome or Edge.'); return; }
    isRecording ? recognition.stop() : recognition.start();
}

// ============================================================
// Exercise Rendering - All 14 Types
// ============================================================
function renderExercise(d, rawJson) {
    const id = 'ex-' + Math.random().toString(36).substr(2, 8);
    const type = d.type || 'fill_blank';
    
    // Store exercise data for grading
    window._exercises = window._exercises || {};
    window._exercises[id] = d;
    
    let h = `<div class="exercise-container" id="${id}" data-type="${type}">`;
    
    // Type badge
    const typeLabels = {
        'multiple_choice': '📝 Multiple Choice', 'fill_blank': '✏️ Fill in the Blank',
        'translate_to_fr': '🇫🇷 Translate to French', 'translate_to_en': '🇬🇧 Translate to English',
        'true_false': '✅ True or False', 'reorder': '🔀 Reorder Words',
        'matching': '🔗 Matching', 'word_bank': '💬 Word Bank',
        'dictation': '🎧 Dictation', 'conjugation': '🔄 Conjugation',
        'article_choice': '📰 Article Choice', 'pronoun_replace': '🔁 Pronoun Replace',
        'transformation': '⚡ Transformation', 'short_answer': '💬 Short Answer',
    };
    h += `<div class="exercise-type-badge">${typeLabels[type] || '📝 Exercise'}</div>`;
    h += `<div class="exercise-prompt">${d.prompt}</div>`;
    if (d.promptFr) h += `<div class="exercise-prompt-fr">${d.promptFr}</div>`;
    if (d.hint) h += `<div class="exercise-hint">💡 Hint: ${d.hint}</div>`;
    
    switch(type) {
        case 'multiple_choice':
        case 'article_choice':
        case 'pronoun_replace':
            h += '<div class="quiz-options">';
            (d.options || []).forEach((o, j) => {
                h += `<button class="quiz-option" data-correct="${d.answer}" data-selected="${j}" onclick="checkQuizAnswer(this)">${String.fromCharCode(65+j)}. ${o}</button>`;
            });
            h += '</div><div class="quiz-feedback" style="display:none"></div>';
            break;
            
        case 'true_false':
            h += '<div class="quiz-options">';
            (d.options || ['True', 'False']).forEach((o, j) => {
                h += `<button class="quiz-option" data-correct="${d.answer}" data-selected="${j}" onclick="checkQuizAnswer(this)">${o}</button>`;
            });
            h += '</div><div class="quiz-feedback" style="display:none"></div>';
            break;
            
        case 'fill_blank':
        case 'translate_to_fr':
        case 'translate_to_en':
        case 'short_answer':
        case 'transformation':
            h += `<div class="exercise-input-row">`;
            h += `<input class="exercise-input" placeholder="${type.includes('translate') ? 'Type translation...' : 'Type your answer...'}" onkeydown="if(event.key==='Enter')checkExercise('${id}', this)">`;
            h += `<button class="exercise-submit" onclick="checkExercise('${id}', this.previousElementSibling)">Check</button>`;
            h += `</div><div class="exercise-feedback" style="display:none"></div>`;
            break;
            
        case 'conjugation':
            h += `<div class="exercise-input-row">`;
            h += `<input class="exercise-input" placeholder="Type the conjugated form..." onkeydown="if(event.key==='Enter')checkExercise('${id}', this)">`;
            h += `<button class="exercise-submit" onclick="checkExercise('${id}', this.previousElementSibling)">Check</button>`;
            h += `</div><div class="exercise-feedback" style="display:none"></div>`;
            break;
            
        case 'dictation':
            if (d.audioText) {
                h += `<button class="btn-speak" onclick="speakText('${d.audioText.replace(/'/g, "\\'")}')" style="margin:0.5rem 0">🔊 Listen</button>`;
            }
            h += `<div class="exercise-input-row">`;
            h += `<input class="exercise-input" placeholder="Type what you hear..." onkeydown="if(event.key==='Enter')checkExercise('${id}', this)">`;
            h += `<button class="exercise-submit" onclick="checkExercise('${id}', this.previousElementSibling)">Check</button>`;
            h += `</div><div class="exercise-feedback" style="display:none"></div>`;
            break;
            
        case 'reorder':
            if (d.words && d.words.length) {
                const shuffled = [...d.words].sort(() => Math.random() - 0.5);
                h += `<div class="reorder-selected" id="${id}-selected" style="min-height:40px;padding:0.5rem;border:1px dashed var(--border);border-radius:8px;margin-bottom:0.5rem;display:flex;flex-wrap:wrap;gap:0.375rem"></div>`;
                h += `<div class="reorder-bank" id="${id}-bank">`;
                shuffled.forEach(w => {
                    h += `<span class="word-chip reorder-chip" onclick="addReorderWord('${id}', this)">${w}</span>`;
                });
                h += '</div>';
                h += `<button class="exercise-submit" onclick="checkReorder('${id}')" style="margin-top:0.5rem">Check</button>`;
                h += `<div class="exercise-feedback" style="display:none"></div>`;
            }
            break;
            
        case 'word_bank':
            if (d.wordBank && d.wordBank.length) {
                const shuffled = [...d.wordBank].sort(() => Math.random() - 0.5);
                h += `<div class="reorder-selected" id="${id}-selected" style="min-height:40px;padding:0.5rem;border:1px dashed var(--border);border-radius:8px;margin-bottom:0.5rem;display:flex;flex-wrap:wrap;gap:0.375rem"></div>`;
                h += `<div class="reorder-bank" id="${id}-bank">`;
                shuffled.forEach(w => {
                    h += `<span class="word-chip reorder-chip" onclick="addReorderWord('${id}', this)">${w}</span>`;
                });
                h += '</div>';
                h += `<button class="exercise-submit" onclick="checkReorder('${id}')" style="margin-top:0.5rem">Check</button>`;
                h += `<div class="exercise-feedback" style="display:none"></div>`;
            }
            break;
            
        case 'matching':
            if (d.pairs && d.pairs.length) {
                h += '<div class="matching-container">';
                const shuffledRight = [...d.pairs].sort(() => Math.random() - 0.5);
                d.pairs.forEach((p, i) => {
                    h += `<div class="matching-row">`;
                    h += `<span class="matching-left">${p.left}</span>`;
                    h += `<span class="matching-arrow">→</span>`;
                    h += `<select class="matching-select" data-correct="${p.right}" id="${id}-match-${i}">`;
                    h += `<option value="">Select...</option>`;
                    shuffledRight.forEach(rp => {
                        h += `<option value="${rp.right}">${rp.right}</option>`;
                    });
                    h += '</select></div>';
                });
                h += '</div>';
                h += `<button class="exercise-submit" onclick="checkMatching('${id}', ${d.pairs.length})" style="margin-top:0.5rem">Check</button>`;
                h += `<div class="exercise-feedback" style="display:none"></div>`;
            }
            break;
            
        default:
            h += `<div class="exercise-input-row">`;
            h += `<input class="exercise-input" placeholder="Type your answer..." onkeydown="if(event.key==='Enter')checkExercise('${id}', this)">`;
            h += `<button class="exercise-submit" onclick="checkExercise('${id}', this.previousElementSibling)">Check</button>`;
            h += `</div><div class="exercise-feedback" style="display:none"></div>`;
    }
    
    h += '</div>';
    return h;
}

// ============================================================
// Markdown & Interactive Block Rendering
// ============================================================
function parseMarkdown(text) {
    let html = text;

    // Vocabulary blocks
    html = html.replace(/```vocabulary\s*([\s\S]*?)```/g, (_, json) => {
        try {
            const d = JSON.parse(json.trim());
            if (!d.words) return _;
            let h = '<div class="vocab-container">';
            let lastCat = '';
            d.words.forEach(w => {
                if (w.category && w.category !== lastCat) {
                    lastCat = w.category;
                    h += `<div class="vocab-category">${w.category}</div>`;
                }
                h += `<div class="vocab-word">`;
                h += `<span class="vocab-fr">${w.fr}</span>`;
                if (w.ipa) h += `<span class="vocab-ipa">${w.ipa}</span>`;
                h += `<span class="vocab-en">${w.en}</span>`;
                h += `</div>`;
                if (w.example) h += `<div class="vocab-example">${w.example}${w.exampleEn ? ' — ' + w.exampleEn : ''}</div>`;
            });
            return h + '</div>';
        } catch(e) { return _; }
    });

    // Conjugation blocks
    html = html.replace(/```conjugation\s*([\s\S]*?)```/g, (_, json) => {
        try {
            const d = JSON.parse(json.trim());
            let h = '<div class="conj-container">';
            h += `<div class="conj-verb">${d.verb} — ${d.tense} (${d.translation})</div>`;
            h += '<table class="conj-table"><thead><tr><th>Pronoun</th><th>Form</th></tr></thead><tbody>';
            d.forms.forEach(f => { h += `<tr><td>${f.pronoun}</td><td><strong>${f.form}</strong></td></tr>`; });
            h += '</tbody></table>';
            if (d.rule) h += `<div class="conj-rule">${d.rule}</div>`;
            return h + '</div>';
        } catch(e) { return _; }
    });

    // Dialogue blocks
    html = html.replace(/```dialogue\s*([\s\S]*?)```/g, (_, json) => {
        try {
            const d = JSON.parse(json.trim());
            let h = '<div class="dialogue-container">';
            d.lines.forEach(l => {
                h += `<div class="dialogue-line">`;
                h += `<span class="dialogue-speaker">${l.name || l.speaker}:</span>`;
                h += `<div><div class="dialogue-fr">${l.fr}</div>`;
                h += `<div class="dialogue-en">${l.en}</div></div>`;
                h += `<button class="btn-speak" onclick="speakText('${l.fr.replace(/'/g, "\\'")}')">🔊</button>`;
                h += `</div>`;
            });
            return h + '</div>';
        } catch(e) { return _; }
    });

    // Quiz blocks
    html = html.replace(/```quiz\s*([\s\S]*?)```/g, (_, json) => {
        try {
            const d = JSON.parse(json.trim());
            let h = '<div class="quiz-container">';
            if (d.title) h += `<div class="quiz-title">${d.title}</div>`;
            d.questions.forEach((q, i) => {
                h += `<div class="quiz-question"><p>${i+1}. ${q.question}</p>`;
                h += '<div class="quiz-options">';
                q.options.forEach((o, j) => {
                    h += `<button class="quiz-option" data-correct="${q.correct}" data-selected="${j}" onclick="checkQuizAnswer(this)">${String.fromCharCode(65+j)}. ${o}</button>`;
                });
                h += '</div><div class="quiz-feedback" style="display:none"></div></div>';
            });
            return h + '</div>';
        } catch(e) { return _; }
    });

    // Exercise blocks - handles all 14 exercise types
    html = html.replace(/```exercise\s*([\s\S]*?)```/g, (_, json) => {
        try {
            const d = JSON.parse(json.trim());
            return renderExercise(d, json);
        } catch(e) { return _; }
    });

    // Practiceset blocks - multiple exercises in a set
    html = html.replace(/```practiceset\s*([\s\S]*?)```/g, (_, json) => {
        try {
            const d = JSON.parse(json.trim());
            let h = '<div class="practiceset-container">';
            if (d.title) h += `<div class="quiz-title">${d.title}</div>`;
            d.exercises.forEach((ex, i) => {
                h += `<div class="practiceset-item">`;
                h += `<div class="practiceset-number">${i+1}</div>`;
                h += renderExercise(ex, JSON.stringify(ex));
                h += '</div>';
            });
            h += '</div>';
            return h;
        } catch(e) { return _; }
    });

    // Cultural notes
    html = html.replace(/```cultural\s*([\s\S]*?)```/g, (_, note) => {
        return `<div class="cultural-note"><div class="cultural-note-title">🇫🇷 Cultural Note</div>${note.trim()}</div>`;
    });

    // Standard markdown
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    html = html.replace(/^\* (.+)$/gm, '<li>$1</li>');
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>[\s\S]*?<\/li>)/gs, '<ul>$1</ul>');
    html = html.replace(/<\/ul>\s*<ul>/g, '');
    html = html.replace(/^---$/gm, '<hr>');
    
    // Markdown tables
    html = html.replace(/^(\|.+\|)\n(\|[-| :]+\|)\n((?:\|.+\|\n?)*)/gm, (_, header, separator, body) => {
        const headers = header.split('|').filter(c => c.trim());
        const rows = body.trim().split('\n').map(r => r.split('|').filter(c => c.trim()));
        let table = '<div style="overflow-x:auto;margin:0.75rem 0"><table class="md-table"><thead><tr>';
        headers.forEach(h => { table += `<th>${h.trim()}</th>`; });
        table += '</tr></thead><tbody>';
        rows.forEach(row => {
            table += '<tr>';
            row.forEach(cell => { table += `<td>${cell.trim()}</td>`; });
            table += '</tr>';
        });
        table += '</tbody></table></div>';
        return table;
    });

    // Paragraphs
    const ps = html.split(/\n\n+/);
    html = ps.map(p => {
        p = p.trim();
        if (!p) return '';
        if (p.startsWith('<h') || p.startsWith('<ul') || p.startsWith('<pre') || p.startsWith('<hr') || p.startsWith('<div')) return p;
        return '<p>' + p.replace(/\n/g, '<br>') + '</p>';
    }).filter(p => p).join('\n');

    return html;
}

// ============================================================
// Interactive Block Handlers
// ============================================================
window.checkQuizAnswer = function(btn) {
    const q = btn.closest('.quiz-question') || btn.closest('.exercise-container');
    if (!q) return;
    const correct = parseInt(btn.dataset.correct);
    const selected = parseInt(btn.dataset.selected);
    const fb = q.querySelector('.quiz-feedback');
    if (!fb) return;
    q.querySelectorAll('.quiz-option').forEach(o => o.disabled = true);
    btn.classList.add('selected');
    if (selected === correct) {
        btn.classList.add('correct');
        fb.textContent = '✓ Correct! Très bien!';
        fb.className = 'quiz-feedback correct';
    } else {
        btn.classList.add('incorrect');
        const options = q.querySelectorAll('.quiz-option');
        if (options[correct]) options[correct].classList.add('correct');
        fb.textContent = '✗ Incorrect. The correct answer is marked above.';
        fb.className = 'quiz-feedback incorrect';
    }
    fb.style.display = 'block';
};

window.checkExercise = function(id, input) {
    const exercise = window._exercises?.[id];
    if (!exercise) return;
    const answer = input.value.trim();
    if (!answer) return;

    apiFetch('/api/check-exercise', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ exercise_id: id, answer, exercise_data: exercise })
    })
    .then(r => r.json())
    .then(d => {
        const container = document.getElementById(id);
        const fb = container.querySelector('.exercise-feedback');
        fb.style.display = 'block';
        if (d.correct) {
            fb.className = 'exercise-feedback';
            fb.style.background = 'rgba(22,163,74,0.1)';
            fb.style.color = 'var(--correct)';
            fb.textContent = '✓ Correct! +10 XP';
        } else {
            fb.className = 'exercise-feedback';
            fb.style.background = 'rgba(220,38,38,0.1)';
            fb.style.color = 'var(--incorrect)';
            fb.textContent = d.explanation || '✗ Incorrect. Try again!';
        }
        updateXP(d.total_xp);
    });
};

// Reorder / Word Bank handlers
window.addReorderWord = function(id, chip) {
    const selected = document.getElementById(id + '-selected');
    if (!selected || chip.classList.contains('used')) return;
    chip.classList.add('used');
    const clone = chip.cloneNode(true);
    clone.onclick = function() { removeReorderWord(id, this, chip); };
    selected.appendChild(clone);
};

function removeReorderWord(id, clone, original) {
    clone.remove();
    if (original) original.classList.remove('used');
}

window.checkReorder = function(id) {
    const exercise = window._exercises?.[id];
    if (!exercise) return;
    const selected = document.getElementById(id + '-selected');
    if (!selected) return;
    const words = Array.from(selected.querySelectorAll('.word-chip')).map(c => c.textContent.trim());
    const userAnswer = words.join(' ');
    
    apiFetch('/api/check-exercise', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ exercise_id: id, answer: userAnswer, exercise_data: exercise })
    })
    .then(r => r.json())
    .then(d => {
        const container = document.getElementById(id);
        const fb = container.querySelector('.exercise-feedback');
        fb.style.display = 'block';
        if (d.correct) {
            fb.className = 'exercise-feedback';
            fb.style.background = 'rgba(22,163,74,0.1)';
            fb.style.color = 'var(--correct)';
            fb.textContent = '✓ Correct! +10 XP';
        } else {
            fb.className = 'exercise-feedback';
            fb.style.background = 'rgba(220,38,38,0.1)';
            fb.style.color = 'var(--incorrect)';
            fb.textContent = d.explanation || `✗ The correct order is: ${exercise.answer || exercise.words?.join(' ')}`;
        }
        updateXP(d.total_xp);
    });
};

// Matching handler
window.checkMatching = function(id, pairCount) {
    const exercise = window._exercises?.[id];
    if (!exercise) return;
    let allCorrect = true;
    for (let i = 0; i < pairCount; i++) {
        const sel = document.getElementById(`${id}-match-${i}`);
        if (!sel || sel.value !== sel.dataset.correct) {
            allCorrect = false;
            break;
        }
    }
    const container = document.getElementById(id);
    const fb = container.querySelector('.exercise-feedback');
    fb.style.display = 'block';
    if (allCorrect) {
        fb.className = 'exercise-feedback';
        fb.style.background = 'rgba(22,163,74,0.1)';
        fb.style.color = 'var(--correct)';
        fb.textContent = '✓ All correct! Très bien! +10 XP';
        // Disable selects
        for (let i = 0; i < pairCount; i++) {
            document.getElementById(`${id}-match-${i}`).disabled = true;
        }
        apiFetch('/api/check-exercise', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ exercise_id: id, answer: 'correct', exercise_data: exercise })
        }).then(r => r.json()).then(d => { if (d.total_xp) updateXP(d.total_xp); });
    } else {
        fb.className = 'exercise-feedback';
        fb.style.background = 'rgba(220,38,38,0.1)';
        fb.style.color = 'var(--incorrect)';
        fb.textContent = '✗ Some matches are incorrect. Try again!';
    }
};

// ============================================================
// Message Handling
// ============================================================
function addMessage(content, role) {
    const welcome = document.querySelector('.welcome-message');
    if (welcome) welcome.remove();

    const message = document.createElement('div');
    message.className = `message ${role}`;

    if (role === 'assistant') {
        const av = document.createElement('div');
        av.className = 'message-avatar';
        av.textContent = 'P';
        message.appendChild(av);
    }

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.innerHTML = role === 'assistant' ? parseMarkdown(content) : escapeHtml(content);
    contentDiv.appendChild(bubble);

    if (role === 'assistant') {
        const actions = document.createElement('div');
        actions.className = 'message-actions';
        const speakBtn = document.createElement('button');
        speakBtn.className = 'btn-speak';
        speakBtn.innerHTML = '🔊';
        speakBtn.title = 'Listen';
        speakBtn.addEventListener('click', () => {
            const t = content.replace(/```[\s\S]*?```/g, '').replace(/[*_#`]/g, '').trim();
            speakText(t);
        });
        actions.appendChild(speakBtn);
        contentDiv.appendChild(actions);
    }

    message.appendChild(contentDiv);
    if (role === 'user') {
        const av = document.createElement('div');
        av.className = 'message-avatar';
        av.textContent = 'U';
        message.appendChild(av);
    }

    messagesContainer.appendChild(message);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function addTypingIndicator(msg = 'Thinking...') {
    const welcome = document.querySelector('.welcome-message');
    if (welcome) welcome.remove();
    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.id = 'typingIndicator';
    indicator.innerHTML = `<div class="message-avatar" style="background:var(--primary);color:white">P</div><div class="typing-dots"><div class="progress-status"><span class="progress-text">${msg}</span><div class="progress-bar"><div class="progress-fill progress-indeterminate"></div></div></div></div>`;
    messagesContainer.appendChild(indicator);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function removeTypingIndicator() {
    const ind = document.getElementById('typingIndicator');
    if (ind) ind.remove();
}

function updateSendButton() {
    sendButton.disabled = !messageInput.value.trim() || isGenerating;
}

function autoResize() {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 200) + 'px';
}

function updateXP(xp) {
    document.getElementById('xpDisplay').textContent = xp || 0;
}

// ============================================================
// View Management
// ============================================================
function getToolContent() { return document.getElementById('toolContent'); }

function showToolView(title, html) {
    if (typeof examState !== 'undefined' && examState.phase === 'taking' && !examState.paused) {
        pauseExam();
    }
    document.getElementById('chatView').style.display = 'none';
    document.getElementById('toolView').style.display = 'flex';
    getToolContent().innerHTML = `<div class="tool-header"><h2>${title}</h2></div>` + html;
    document.getElementById('chatTitle').textContent = title;
    document.getElementById('btnBackToChat').style.display = 'inline';
    // Reset scroll so the user sees the top of the new view
    getToolContent().scrollTop = 0;
    window.scrollTo(0, 0);
}

function showChatView() {
    // Pause an active mock test instead of clearing its timer
    if (typeof examState !== 'undefined' && examState.phase === 'taking' && !examState.paused) {
        pauseExam();
    }
    document.getElementById('toolView').style.display = 'none';
    document.getElementById('chatView').style.display = 'flex';
    document.getElementById('chatTitle').textContent = 'Parlez — French AI Tutor';
    document.getElementById('btnBackToChat').style.display = 'none';
    // Reset scroll so the user sees the latest messages / welcome
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    window.scrollTo(0, 0);
}

btnBackToChat?.addEventListener('click', showChatView);

// ============================================================
// Welcome message (single source of truth)
// ============================================================
const WELCOME_HTML = '<div class="welcome-message"><div class="welcome-icon">🇫🇷</div><h2>Bonjour! Ready to learn French?</h2><p>I\'m your personal French tutor. I can teach you vocabulary, grammar, pronunciation, and help you practice conversations.</p><div class="quick-actions"><button class="quick-action" onclick="sendQuickMessage(\'Teach me French greetings\')">👋 Learn Greetings</button><button class="quick-action" onclick="sendQuickMessage(\'Show me numbers 1-20 in French\')">🔢 Numbers 1-20</button><button class="quick-action" onclick="sendQuickMessage(\'Practice conversation at a café\')">☕ Café Roleplay</button><button class="quick-action" onclick="sendQuickMessage(\'Give me a French quiz\')">📝 Take a Quiz</button></div></div>';

function resetChatToWelcome() {
    currentConvId = null;
    chatTitle.textContent = 'Parlez — French AI Tutor';
    messagesContainer.innerHTML = WELCOME_HTML;
}

// ============================================================
// Session Management
// ============================================================
async function startActivitySession(title) {
    currentConvId = null;
    await createConversation();
}

// ============================================================
// Chat
// ============================================================
async function sendMessage(text) {
    if (!text.trim() || isGenerating) return;
    isGenerating = true;
    updateSendButton();
    addMessage(text, 'user');
    messageInput.value = '';
    messageInput.placeholder = 'Ask me anything about French...';
    autoResize();
    addTypingIndicator();

    if (!currentConvId) await createConversation();
    
    // Detect content ingestion: long text that looks like French content
    const hasFrenchChars = /[\u00C0-\u024F]/.test(text);
    const isLongText = text.length > 150;
    const isContentIngestion = isLongText && hasFrenchChars;
    
    // Detect writing correction: user explicitly asks for correction or long French text
    const isWritingCorrection = /correct|corriger|corrige|fix|review|check.*writing|rewrite/i.test(text) && hasFrenchChars;
    
    if (isContentIngestion && !isWritingCorrection) {
        try {
            removeTypingIndicator();
            await ingestFrenchContent(text);
        } catch(e) {
            removeTypingIndicator();
            addMessage('Error processing content.', 'assistant');
        } finally {
            isGenerating = false;
            updateSendButton();
        }
        return;
    }
    
    if (isWritingCorrection) {
        try {
            removeTypingIndicator();
            await correctMyWriting(text);
        } catch(e) {
            removeTypingIndicator();
            addMessage('Error correcting writing.', 'assistant');
        } finally {
            isGenerating = false;
            updateSendButton();
        }
        return;
    }

    try {
        const r = await apiFetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, conv_id: currentConvId, level: currentLevel })
        });
        const d = await r.json();
        removeTypingIndicator();
        addMessage(d.response, 'assistant');
        if (d.total_xp) updateXP(d.total_xp);
        await loadConversations();
    } catch (e) {
        removeTypingIndicator();
        addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
    } finally {
        isGenerating = false;
        updateSendButton();
    }
}

window.sendQuickMessage = function(text) {
    sendMessage(text);
};

async function createConversation() {
    const r = await apiFetch('/api/conversations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ level: currentLevel })
    });
    const conv = await r.json();
    currentConvId = conv.id;
    chatTitle.textContent = conv.title;
    await loadConversations();
}

async function loadConversations() {
    try {
        const r = await apiFetch('/api/conversations');
        const convs = await r.json();
        chatList.innerHTML = convs.length ? '' : '<div class="no-data">No conversations</div>';
        convs.forEach(c => {
            const item = document.createElement('div');
            item.className = `chat-item ${c.id === currentConvId ? 'active' : ''}`;
            item.innerHTML = `<span class="chat-item-title">${escapeHtml(c.title||'Untitled')}</span><button class="btn-delete" data-id="${c.id}">×</button>`;
            item.addEventListener('click', (e) => {
                if (!e.target.classList.contains('btn-delete')) loadConversation(c.id);
            });
            item.querySelector('.btn-delete').addEventListener('click', (e) => {
                e.stopPropagation();
                deleteConversation(c.id);
            });
            chatList.appendChild(item);
        });
        if (!currentConvId && convs.length > 0 && messagesContainer.children.length === 0) {
            // Only auto-load the most-recent chat on initial app load,
            // when messages area is empty. After explicit "New Chat" or
            // "Clear All", the welcome screen is already showing, so skip.
            await loadConversation(convs[0].id);
        }
    } catch (e) { console.error(e); }
}

async function loadConversation(convId) {
    currentConvId = convId;
    showChatView(); // bring chat to the front — was getting hidden behind tool view
    const conv = await apiFetch(`/api/conversations/${convId}`).then(r => r.json());
    chatTitle.textContent = conv.title || 'Chat';
    messagesContainer.innerHTML = '';
    (conv.messages || []).forEach(m => addMessage(m.content, m.role));
    await loadConversations();
}

async function deleteConversation(convId) {
    if (!confirm('Delete this conversation?')) return;
    await apiFetch(`/api/conversations/${convId}`, { method: 'DELETE' });
    if (currentConvId === convId) {
        showChatView();
        resetChatToWelcome();
    }
    await loadConversations();
}

// ============================================================
// Courses
// ============================================================
async function loadCourses() {
    try {
        const r = await apiFetch(`/api/courses/${currentLevel}`);
        const course = await r.json();
        courseList.innerHTML = '';

        if (course.units) {
            course.units.forEach(u => {
                const unitDiv = document.createElement('div');
                unitDiv.className = 'course-unit';
                unitDiv.innerHTML = `<div class="course-unit-title">${u.titleFr}</div>`;

                if (u.lessons) {
                    u.lessons.forEach(l => {
                        const lessonItem = document.createElement('div');
                        lessonItem.className = 'lesson-item';
                        // Prefer French title; fall back to English if missing
                        const titleFr = l.titleFr || l.title;
                        const titleEn = l.titleFr ? l.title : '';
                        lessonItem.innerHTML = `
                            <div class="lesson-info">
                                <span class="lesson-title-fr">${titleFr}</span>
                                ${titleEn ? `<span class="lesson-title-en">${titleEn}</span>` : ''}
                                <span class="lesson-time">${l.estimatedMinutes || 30}min</span>
                            </div>
                            <div class="lesson-actions">
                                <button class="lesson-learn-btn" onclick="startLessonView('${currentLevel}', '${l.id}')">📖 Learn</button>
                                <button class="lesson-practice-btn" onclick="startLessonPractice('${currentLevel}', '${l.id}')">Practice</button>
                            </div>
                        `;
                        unitDiv.appendChild(lessonItem);
                    });
                }
                courseList.appendChild(unitDiv);
            });
        }
    } catch (e) { console.error(e); }
}

// ============================================================
// Lesson View — read content (vocab, grammar, conjugation, dialogue, cultural)
// ============================================================
window.startLessonView = async function(level, lessonId) {
    showToolView('📖 Lesson', '<div style="text-align:center;padding:2rem"><div class="typing-dots"><div class="progress-status"><span class="progress-text">Loading lesson…</span></div></div></div>');
    try {
        const r = await apiFetch(`/api/courses/${level}/lessons/${lessonId}`);
        const lesson = await r.json();
        renderLessonView(lesson, level);
    } catch (e) {
        getToolContent().innerHTML = '<div class="tool-header"><h2>📖 Lesson</h2></div><p style="color:var(--incorrect);text-align:center;padding:2rem">Could not load this lesson. Please try again.</p>';
    }
};

function escapeHtml(s) {
    if (s == null) return '';
    return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function renderLessonView(lesson, level) {
    const titleFr = lesson.titleFr || lesson.title || 'Leçon';
    const titleEn = lesson.titleFr && lesson.title ? lesson.title : '';

    let html = `<div class="tool-header lesson-tool-header"><h2><span class="lesson-title-fr-large">${escapeHtml(titleFr)}</span>${titleEn ? `<span class="lesson-title-en-sub">${escapeHtml(titleEn)}</span>` : ''}</h2></div>`;
    html += `<div class="lesson-view">`;

    // Tab nav
    const tabs = [];
    tabs.push({ id: 'overview', label: '📋 Overview' });
    if (lesson.vocabulary && lesson.vocabulary.length) tabs.push({ id: 'vocabulary', label: `📚 Vocab (${lesson.vocabulary.length})` });
    if (lesson.grammar && lesson.grammar.length) tabs.push({ id: 'grammar', label: `📖 Grammar (${lesson.grammar.length})` });
    if (lesson.conjugation && lesson.conjugation.verbs && lesson.conjugation.verbs.length) tabs.push({ id: 'conjugation', label: `🔄 Conjugation (${lesson.conjugation.verbs.length})` });
    if (lesson.dialogue && lesson.dialogue.length) tabs.push({ id: 'dialogue', label: `💬 Dialogue (${lesson.dialogue.length})` });
    if (lesson.culturalNote) tabs.push({ id: 'cultural', label: '🇫🇷 Cultural' });
    tabs.push({ id: 'practice', label: '✏️ Practice' });

    html += `<nav class="lesson-tabs">`;
    tabs.forEach((t, i) => {
        html += `<button class="lesson-tab ${i === 0 ? 'active' : ''}" data-tab="${t.id}">${t.label}</button>`;
    });
    html += `</nav>`;

    // Sections — all rendered, only the first visible
    // Overview
    html += `<section class="lesson-section" data-section="overview">`;
    html += `<div class="lesson-overview">`;
    if (lesson.description) html += `<p class="lesson-description">${escapeHtml(lesson.description)}</p>`;
    if (lesson.objectives && lesson.objectives.length) {
        html += `<h3>Learning objectives · Objectifs</h3><ul class="lesson-objectives">`;
        lesson.objectives.forEach(o => { html += `<li>${escapeHtml(o)}</li>`; });
        html += `</ul>`;
    }
    html += `<div class="lesson-overview-meta">⏱️ ${lesson.estimatedMinutes || 30} min · ${(lesson.vocabulary||[]).length} words · ${(lesson.grammar||[]).length} grammar · ${(lesson.exercises||[]).length} exercises</div>`;
    html += `<div class="lesson-cta"><button class="lesson-learn-btn" onclick="startLessonPractice('${level}', '${lesson.id}')">Start Practice →</button></div>`;
    html += `</div></section>`;

    // Vocabulary
    if (lesson.vocabulary && lesson.vocabulary.length) {
        html += `<section class="lesson-section" data-section="vocabulary" style="display:none">`;
        // Group by category for readability
        const byCat = {};
        lesson.vocabulary.forEach(v => {
            const c = v.category || 'Vocabulary';
            if (!byCat[c]) byCat[c] = [];
            byCat[c].push(v);
        });
        Object.keys(byCat).forEach(cat => {
            html += `<h3>${escapeHtml(cat)}</h3>`;
            html += `<div class="lesson-vocab-grid">`;
            byCat[cat].forEach(v => {
                html += `<div class="lesson-vocab-card">`;
                html += `<div class="lesson-vocab-fr">${escapeHtml(v.fr)}</div>`;
                if (v.ipa) html += `<div class="lesson-vocab-ipa">${escapeHtml(v.ipa)}</div>`;
                html += `<div class="lesson-vocab-en">${escapeHtml(v.en)}</div>`;
                if (v.example) html += `<div class="lesson-vocab-example">${escapeHtml(v.example)}${v.exampleEn ? ` — <em>${escapeHtml(v.exampleEn)}</em>` : ''}</div>`;
                html += `<button class="lesson-vocab-speak" onclick="speakText('${escapeHtml(v.fr).replace(/'/g, "\\'")}')" title="Listen">🔊</button>`;
                html += `</div>`;
            });
            html += `</div>`;
        });
        html += `</section>`;
    }

    // Grammar
    if (lesson.grammar && lesson.grammar.length) {
        html += `<section class="lesson-section" data-section="grammar" style="display:none">`;
        lesson.grammar.forEach(g => {
            html += `<div class="lesson-grammar-card">`;
            html += `<h3>${escapeHtml(g.title)}</h3>`;
            if (g.explanation) html += `<p>${escapeHtml(g.explanation)}</p>`;
            if (g.examples && g.examples.length) {
                html += `<div class="lesson-grammar-examples">`;
                g.examples.forEach(ex => {
                    html += `<div class="lesson-grammar-example"><div class="fr">${escapeHtml(ex.fr)}</div><div class="en">${escapeHtml(ex.en)}</div></div>`;
                });
                html += `</div>`;
            }
            if (g.table && g.table.headers && g.table.rows && g.table.rows.length) {
                html += `<table class="lesson-grammar-table"><thead><tr>`;
                g.table.headers.forEach(h => { html += `<th>${escapeHtml(h)}</th>`; });
                html += `</tr></thead><tbody>`;
                g.table.rows.forEach(row => {
                    html += `<tr>`;
                    row.forEach(cell => { html += `<td>${escapeHtml(cell)}</td>`; });
                    html += `</tr>`;
                });
                html += `</tbody></table>`;
                if (g.table.caption) html += `<div class="lesson-grammar-caption">${escapeHtml(g.table.caption)}</div>`;
            }
            if (g.tip) html += `<div class="lesson-grammar-tip">💡 ${escapeHtml(g.tip)}</div>`;
            html += `</div>`;
        });
        html += `</section>`;
    }

    // Conjugation
    if (lesson.conjugation && lesson.conjugation.verbs && lesson.conjugation.verbs.length) {
        html += `<section class="lesson-section" data-section="conjugation" style="display:none">`;
        lesson.conjugation.verbs.forEach(v => {
            html += `<div class="lesson-conj-card">`;
            html += `<h3>${escapeHtml(v.infinitive)} — ${escapeHtml(v.tense || '')} <span class="lesson-conj-translation">(${escapeHtml(v.translation || '')})</span></h3>`;
            // v.conjugations is a list[{pronoun, form}, ...] — iterate, don't Object.entries()
            const forms = Array.isArray(v.conjugations) ? v.conjugations : [];
            if (forms.length) {
                html += `<table class="lesson-conj-table"><tbody>`;
                forms.forEach(entry => {
                    const pronoun = entry && entry.pronoun != null ? entry.pronoun : '';
                    const form = entry && entry.form != null ? entry.form : '';
                    html += `<tr><td class="pronoun">${escapeHtml(String(pronoun))}</td><td><strong>${escapeHtml(String(form))}</strong></td></tr>`;
                });
                html += `</tbody></table>`;
                if (forms.length < 6) {
                    html += `<div class="lesson-conj-note">📝 Partial table — only ${forms.length} form${forms.length === 1 ? '' : 's'} available in this lesson. Full conjugation practice is available in the Practice tab.</div>`;
                }
            } else {
                html += `<div class="lesson-conj-note">No conjugation forms in this lesson.</div>`;
            }
            if (v.sentenceRule) html += `<div class="lesson-conj-rule">${escapeHtml(v.sentenceRule)}</div>`;
            if (v.sentenceExamples && v.sentenceExamples.length) {
                html += `<div class="lesson-conj-examples">`;
                v.sentenceExamples.forEach(ex => {
                    html += `<div class="lesson-conj-example"><div class="fr">${escapeHtml(ex.fr)}</div><div class="en">${escapeHtml(ex.en)}</div></div>`;
                });
                html += `</div>`;
            }
            html += `</div>`;
        });
        html += `</section>`;
    }

    // Dialogue
    if (lesson.dialogue && lesson.dialogue.length) {
        html += `<section class="lesson-section" data-section="dialogue" style="display:none">`;
        html += `<div class="lesson-dialogue">`;
        lesson.dialogue.forEach(d => {
            const speakerLabel = d.name || d.speaker || '';
            html += `<div class="lesson-dialogue-line">`;
            if (speakerLabel) html += `<div class="lesson-dialogue-speaker">${escapeHtml(speakerLabel)}:</div>`;
            html += `<div class="lesson-dialogue-bubble">`;
            html += `<div class="fr">${escapeHtml(d.fr)}</div>`;
            if (d.en) html += `<div class="en">${escapeHtml(d.en)}</div>`;
            html += `<button class="lesson-vocab-speak" onclick="speakText('${escapeHtml(d.fr).replace(/'/g, "\\'")}')" title="Listen">🔊</button>`;
            html += `</div></div>`;
        });
        html += `</div></section>`;
    }

    // Cultural note
    if (lesson.culturalNote) {
        html += `<section class="lesson-section" data-section="cultural" style="display:none">`;
        html += `<div class="lesson-cultural">`;
        html += `<h3>🇫🇷 Note culturelle · Cultural note</h3>`;
        html += `<p>${escapeHtml(lesson.culturalNote)}</p>`;
        html += `</div></section>`;
    }

    // Practice CTA
    html += `<section class="lesson-section" data-section="practice" style="display:none">`;
    html += `<div class="lesson-practice-cta">`;
    html += `<h3>Ready to practice?</h3>`;
    html += `<p>You've reviewed the lesson content. Time to test your understanding with ${(lesson.exercises||[]).length + (lesson.conjugation?.practice?.length || 0) + (lesson.activities||[]).length} exercises.</p>`;
    html += `<button class="lesson-learn-btn" onclick="startLessonPractice('${level}', '${lesson.id}')">✏️ Start Practice</button>`;
    html += `</div></section>`;

    html += `</div>`; // end .lesson-view
    getToolContent().innerHTML = html;

    // Wire up tab clicks
    const tabs_ = getToolContent().querySelectorAll('.lesson-tab');
    const sections_ = getToolContent().querySelectorAll('.lesson-section');
    tabs_.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs_.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            const target = tab.getAttribute('data-tab');
            sections_.forEach(s => {
                s.style.display = s.getAttribute('data-section') === target ? 'block' : 'none';
            });
            // Reset scroll to top of content when switching tabs
            getToolContent().scrollTop = 0;
        });
    });
}

window.startLessonPractice = async function(level, lessonId) {
    showToolView('📝 Lesson Practice', '<div style="text-align:center;padding:2rem"><div class="typing-dots"><div class="progress-status"><span class="progress-text">Loading lesson exercises...</span></div></div></div>');
    try {
        const r = await apiFetch(`/api/practice/lesson/${level}/${lessonId}`, { method: 'POST' });
        const d = await r.json();
        
        if (!d.exercises || d.exercises.length === 0) {
            getToolContent().innerHTML = '<div class="tool-header"><h2>📝 Lesson Practice</h2></div><p style="color:var(--muted-foreground);text-align:center;padding:2rem">No exercises available for this lesson yet.</p>';
            return;
        }
        
        let html = `<div class="tool-header"><h2>📝 Practice: ${d.lesson.title} (${d.lesson.titleFr})</h2></div>`;
        html += `<div class="practiceset-container">`;
        html += `<div style="font-size:0.8rem;color:var(--muted-foreground);margin-bottom:1rem">${d.total} exercises</div>`;
        
        d.exercises.forEach((ex, i) => {
            html += `<div class="practiceset-item">`;
            html += `<div class="practiceset-number">${i+1}</div>`;
            html += renderExercise(ex, JSON.stringify(ex));
            html += '</div>';
        });
        
        html += '</div>';
        getToolContent().innerHTML = html;
    } catch(e) {
        getToolContent().innerHTML = '<div class="tool-header"><h2>📝 Lesson Practice</h2></div><p style="color:var(--incorrect);text-align:center;padding:2rem">Error loading lesson practice. Try again.</p>';
    }
};

// ============================================================
// Scenarios
// ============================================================
async function loadScenarios() {
    try {
        const r = await apiFetch('/api/scenarios');
        const scenarios = await r.json();
        scenarioList.innerHTML = '';
        scenarios.forEach(s => {
            const item = document.createElement('div');
            item.className = 'scenario-item';
            item.innerHTML = `<span class="scenario-item-icon">${s.icon}</span><div class="course-item-info"><div class="course-item-title">${s.labelFr}</div><div class="course-item-desc">${s.description}</div></div>`;
            item.addEventListener('click', () => {
                // Scenario is a chat exercise — switch to chat view first so the message isn't hidden behind tool view
                showChatView();
                sendMessage(`Let's practice a conversation scenario: ${s.labelFr} - ${s.description}`);
            });
            scenarioList.appendChild(item);
        });
    } catch (e) { console.error(e); }
}

// ============================================================
// Settings
// ============================================================
async function loadUser() {
    try {
        const r = await apiFetch('/api/user');
        const user = await r.json();
        currentLevel = user.level || 'A1';
        document.getElementById('currentLevel').textContent = currentLevel;
        document.getElementById('levelName').textContent = LEVEL_NAMES[currentLevel] || '';
        document.getElementById('userName').value = user.name || '';
        // Update level selector
        document.querySelectorAll('.level-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.level === currentLevel);
        });
    } catch(e) {}
}

async function storage_user_level(level) {
    currentLevel = level;
    document.getElementById('currentLevel').textContent = level;
    document.getElementById('levelName').textContent = LEVEL_NAMES[level] || '';
    try {
        await apiFetch('/api/user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ level })
        });
    } catch(e) {}
}

async function loadProgress() {
    try {
        const [p, s, stats] = await Promise.all([
            apiFetch('/api/progress').then(r => r.json()),
            apiFetch('/api/streaks').then(r => r.json()),
            apiFetch('/api/exercise-stats').then(r => r.json()).catch(() => ({accuracy: 0}))
        ]);
        document.getElementById('xpDisplay').textContent = p.xp || 0;
        document.getElementById('streakDisplay').textContent = s.current || 0;
        document.getElementById('accuracyDisplay').textContent = stats.accuracy || 0;
    } catch(e) {}
}

// ============================================================
// Sidebar collapse
// ============================================================
document.querySelectorAll('.section-header').forEach(h => {
    h.addEventListener('click', e => {
        if (e.target.closest('.btn-icon')) return;
        const targetId = h.getAttribute('data-target');
        const content = targetId ? document.getElementById(targetId) : h.nextElementSibling;
        const icon = h.querySelector('.collapse-icon');
        if (content) {
            content.classList.toggle('collapsed');
            if (icon) icon.style.transform = content.classList.contains('collapsed') ? 'rotate(-90deg)' : '';
        }
    });
});

// ============================================================
// Mobile sidebar helpers
// ============================================================
function isMobile() {
    return window.innerWidth <= 768;
}

function openMobileSidebar() {
    sidebar.classList.add('open');
    if (sidebarBackdrop) sidebarBackdrop.classList.add('open');
}

function closeMobileSidebar() {
    sidebar.classList.remove('open');
    if (sidebarBackdrop) sidebarBackdrop.classList.remove('open');
}

function toggleSidebarState() {
    if (isMobile()) {
        sidebar.classList.toggle('open');
        if (sidebarBackdrop) sidebarBackdrop.classList.toggle('open');
    } else {
        sidebar.classList.toggle('collapsed');
    }
}

// ============================================================
// Event Listeners
// ============================================================
toggleSidebar.addEventListener('click', toggleSidebarState);
if (sidebarBackdrop) {
    sidebarBackdrop.addEventListener('click', closeMobileSidebar);
}

// Close mobile sidebar when a navigation item is selected
sidebar.addEventListener('click', (e) => {
    if (!isMobile()) return;
    const clickable = e.target.closest('.chat-item, .course-item, .scenario-item, .practice-item, .lesson-learn-btn, .lesson-practice-btn, .btn-new-chat');
    if (clickable) closeMobileSidebar();
});

window.addEventListener('resize', () => {
    if (!isMobile()) {
        closeMobileSidebar();
    }
});

newChatBtn.addEventListener('click', () => {
    showChatView();        // bring chat to the front
    resetChatToWelcome();
    loadConversations();
});

document.getElementById('btnSettings').addEventListener('click', () => settingsModal.style.display = 'flex');
closeSettings.addEventListener('click', () => settingsModal.style.display = 'none');
document.getElementById('btnLogout')?.addEventListener('click', () => { settingsModal.style.display = 'none'; logout(); });
settingsModal.addEventListener('click', (e) => { if (e.target === settingsModal) settingsModal.style.display = 'none'; });

document.querySelectorAll('.level-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.level-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        storage_user_level(btn.dataset.level);
        loadCourses();
    });
});

document.getElementById('userName').addEventListener('change', async (e) => {
    try {
        await apiFetch('/api/user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: e.target.value })
        });
    } catch(err) {}
});

clearHistoryBtn.addEventListener('click', async () => {
    if (confirm('Clear all conversations?')) {
        await apiFetch('/api/history', { method: 'DELETE' });
        showChatView();
        resetChatToWelcome();
        loadConversations();
    }
});

voiceButton.addEventListener('click', toggleVoice);

sendButton.addEventListener('click', () => sendMessage(messageInput.value));
messageInput.addEventListener('input', () => { autoResize(); updateSendButton(); });
messageInput.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendButton.click(); } });

// ============================================================
// Init
// ============================================================
updateSendButton();
loadUser();
function initApp() {
    loadCourses();
    loadScenarios();
    loadConversations();
    loadProgress();
    initVoice();
    messageInput.focus();
}

// Check auth on page load
checkAuth();

// ============================================================
// Practice Functions
// ============================================================

window.startVocabQuiz = async function() {
    showToolView('📝 Vocabulary Quiz', '<div style="text-align:center;padding:2rem"><div class="typing-dots"><div class="progress-status"><span class="progress-text">Generating quiz...</span><div class="progress-bar"><div class="progress-fill progress-indeterminate"></div></div></div></div></div>');
    try {
        const r = await apiFetch('/api/practice/vocab-quiz', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ level: currentLevel, count: 5 })
        });
        const d = await r.json();
        
        if (!d.quiz) {
            getToolContent().innerHTML = `<div class="tool-header"><h2>📝 Vocabulary Quiz</h2></div><p style="color:var(--muted-foreground);text-align:center;padding:2rem">${d.message || 'No vocabulary available for this level yet.'}</p>`;
            return;
        }
        
        let html = '<div class="tool-header"><h2>📝 Vocabulary Quiz</h2></div>';
        html += '<div class="quiz-container">';
        d.quiz.questions.forEach((q, i) => {
            html += `<div class="quiz-question"><p>${i+1}. ${q.question}</p><div class="quiz-options">`;
            q.options.forEach((o, j) => {
                html += `<button class="quiz-option" data-correct="${q.correct}" data-selected="${j}" onclick="checkQuizAnswer(this)">${String.fromCharCode(65+j)}. ${o}</button>`;
            });
            html += '</div><div class="quiz-feedback" style="display:none"></div></div>';
        });
        html += '</div>';
        
        getToolContent().innerHTML = html;
    } catch(e) {
        getToolContent().innerHTML = '<div class="tool-header"><h2>📝 Vocabulary Quiz</h2></div><p style="color:var(--incorrect)">Error generating quiz. Try again.</p>';
    }
};

window.startConjQuiz = async function() {
    showToolView('🔄 Conjugation Drill', '<div style="text-align:center;padding:2rem"><div class="typing-dots"><div class="progress-status"><span class="progress-text">Generating drill...</span><div class="progress-bar"><div class="progress-fill progress-indeterminate"></div></div></div></div></div>');
    try {
        const r = await apiFetch('/api/practice/conj-quiz', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ level: currentLevel, count: 5 })
        });
        const d = await r.json();
        if (!d.quiz) {
            getToolContent().innerHTML = '<div class="tool-header"><h2>🔄 Conjugation Drill</h2></div><p style="color:var(--muted-foreground);text-align:center;padding:2rem">No conjugation data available.</p>';
            return;
        }
        let html = '<div class="tool-header"><h2>🔄 Conjugation Drill</h2></div><div class="quiz-container">';
        d.quiz.questions.forEach((q, i) => {
            html += `<div class="quiz-question"><p>${i+1}. ${q.question}</p><div class="quiz-options">`;
            q.options.forEach((o, j) => { html += `<button class="quiz-option" data-correct="${q.correct}" data-selected="${j}" onclick="checkQuizAnswer(this)">${String.fromCharCode(65+j)}. ${o}</button>`; });
            html += '</div><div class="quiz-feedback" style="display:none"></div></div>';
        });
        html += '</div>';
        getToolContent().innerHTML = html;
    } catch(e) {
        getToolContent().innerHTML = '<div class="tool-header"><h2>🔄 Conjugation Drill</h2></div><p style="color:var(--incorrect)">Error. Try again.</p>';
    }
};

window.startFlashcardReview = async function() {
    showToolView('🃏 Flashcard Review', '<div style="text-align:center;padding:2rem"><div class="typing-dots"><div class="progress-status"><span class="progress-text">Loading flashcards...</span><div class="progress-bar"><div class="progress-fill progress-indeterminate"></div></div></div></div></div>');
    try {
        const [dueRes, statsRes] = await Promise.all([
            apiFetch('/api/flashcards/due').then(r => r.json()),
            apiFetch('/api/flashcards/stats').then(r => r.json())
        ]);
        
        if (dueRes.length === 0) {
            getToolContent().innerHTML = '<div class="tool-header"><h2>🃏 Flashcard Review</h2></div><p style="color:var(--muted-foreground);text-align:center;padding:2rem">No flashcards due for review! 🎉 Create flashcards by learning vocabulary, or ask me to generate some flashcards for you.</p>';
            return;
        }
        
        renderFlashcardReview(dueRes, statsRes);
    } catch(e) {
        getToolContent().innerHTML = '<div class="tool-header"><h2>🃏 Flashcard Review</h2></div><p style="color:var(--incorrect)">Error loading flashcards. Try again.</p>';
    }
};

let currentFlashcards = [];
let flashcardIndex = 0;

function renderFlashcardReview(cards, stats) {
    currentFlashcards = cards;
    flashcardIndex = 0;
    
    let html = '<div class="tool-header"><h2>🃏 Flashcard Review</h2></div>';
    html += '<div class="flashcard-review">';
    html += '<div class="flashcard-stats">';
    html += `<div class="flashcard-stat"><div class="flashcard-stat-value">${stats.due}</div><div class="flashcard-stat-label">Due</div></div>`;
    html += `<div class="flashcard-stat"><div class="flashcard-stat-value">${stats.learning}</div><div class="flashcard-stat-label">Learning</div></div>`;
    html += `<div class="flashcard-stat"><div class="flashcard-stat-value">${stats.mature}</div><div class="flashcard-stat-label">Mature</div></div>`;
    html += '</div>';
    html += renderFlashcard(cards[0]);
    html += `<div class="flashcard-progress">${flashcardIndex + 1} of ${cards.length}</div>`;
    html += '</div>';
    
    getToolContent().innerHTML = html;
}

function renderFlashcard(card) {
    return `
        <div class="flashcard-card" onclick="this.classList.toggle('flipped')" id="currentFlashcard">
            <div class="flashcard-inner">
                <div class="flashcard-front">
                    <div class="flashcard-word">${card.front}</div>
                    ${card.meta?.ipa ? `<div class="flashcard-ipa">${card.meta.ipa}</div>` : ''}
                    <div class="flashcard-tap">Tap to reveal</div>
                </div>
                <div class="flashcard-back">
                    <div class="flashcard-translation">${card.back}</div>
                    ${card.meta?.example ? `<div class="flashcard-example">${card.meta.example}</div>` : ''}
                </div>
            </div>
        </div>
        <div class="flashcard-actions">
            <button class="flashcard-btn hard" onclick="reviewCurrentCard(1)">😠 Hard</button>
            <button class="flashcard-btn good" onclick="reviewCurrentCard(3)">😊 Good</button>
            <button class="flashcard-btn easy" onclick="reviewCurrentCard(5)">🤩 Easy</button>
        </div>
    `;
}

window.reviewCurrentCard = async function(quality) {
    if (flashcardIndex >= currentFlashcards.length) return;
    
    const card = currentFlashcards[flashcardIndex];
    try {
        const r = await apiFetch(`/api/flashcards/${card.id}/review`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ quality })
        });
        const d = await r.json();
        if (d.total_xp) updateXP(d.total_xp);
    } catch(e) {}
    
    flashcardIndex++;
    if (flashcardIndex >= currentFlashcards.length) {
        getToolContent().innerHTML = '<div class="tool-header"><h2>🃏 Flashcard Review</h2></div><p style="text-align:center;padding:2rem;font-size:1.2rem">🎉 Session complete! Great work reviewing your flashcards!</p>';
        return;
    }
    
    const cardHtml = '<div class="tool-header"><h2>🃏 Flashcard Review</h2></div><div class="flashcard-review">' +
        renderFlashcard(currentFlashcards[flashcardIndex]) +
        `<div class="flashcard-progress">${flashcardIndex + 1} of ${currentFlashcards.length}</div>` +
        '</div>';
    getToolContent().innerHTML = cardHtml;
};

window.showWordOfDay = async function() {
    showToolView('📅 Word of the Day', '<div style="text-align:center;padding:2rem"><div class="typing-dots"><div class="progress-status"><span class="progress-text">Loading...</span></div></div></div>');
    try {
        const r = await apiFetch('/api/practice/word-of-day');
        const d = await r.json();
        
        if (!d.word) {
            getToolContent().innerHTML = '<div class="tool-header"><h2>📅 Word of the Day</h2></div><p style="color:var(--muted-foreground);text-align:center;padding:2rem">No vocabulary available yet. Start learning to build your word bank!</p>';
            return;
        }
        
        let html = '<div class="tool-header"><h2>📅 Word of the Day</h2></div>';
        html += '<div style="text-align:center;padding:2rem">';
        html += `<div style="font-size:1.5rem;font-weight:700;color:var(--primary);font-family:'Playfair Display',serif">${d.word.fr}</div>`;
        if (d.word.ipa) html += `<div style="font-size:0.9rem;color:var(--muted-foreground);font-style:italic">${d.word.ipa}</div>`;
        html += `<div style="font-size:1.1rem;margin:0.5rem 0">${d.word.en}</div>`;
        if (d.word.example) html += `<div style="font-size:0.85rem;color:var(--muted-foreground);font-style:italic">"${d.word.example}"</div>`;
        html += `<button class="btn-speak" onclick="speakText('${d.word.fr.replace(/'/g, "\\'")}')">🔊 Listen</button>`;
        html += '</div>';
        
        getToolContent().innerHTML = html;
    } catch(e) {
        getToolContent().innerHTML = '<div class="tool-header"><h2>📅 Word of the Day</h2></div><p style="color:var(--incorrect)">Error loading word of the day.</p>';
    }
};

// ============================================================
// French Content Ingestion
// ============================================================
window.promptContentIngest = function() {
    showToolView('📄 French Content Tool', '<div style="text-align:center;padding:2rem"><p style="color:var(--muted-foreground)">Paste any French text below (article, lyrics, recipe, etc.) and I\'ll extract vocabulary, create flashcards, and generate a quiz for you!</p><textarea id="contentInput" style="width:100%;min-height:150px;padding:1rem;border:1px solid var(--border);border-radius:10px;font-family:inherit;font-size:0.95rem;resize:vertical;background:var(--input);color:var(--foreground)" placeholder="Paste French content here..."></textarea><div style="margin-top:1rem"><select id="contentLevel" style="padding:0.5rem;border:1px solid var(--border);border-radius:8px;background:var(--input);color:var(--foreground);margin-right:0.5rem"><option value="A1">A1</option><option value="A2">A2</option><option value="B1" selected>B1</option><option value="B2">B2</option></select><button class="btn-primary" onclick="submitContentIngest()">Analyze Content</button></div></div>');
};

window.submitContentIngest = async function() {
    const text = document.getElementById('contentInput')?.value;
    if (!text || !text.trim()) return;
    const level = document.getElementById('contentLevel')?.value || currentLevel;
    
    getToolContent().innerHTML = '<div class="tool-header"><h2>📄 French Content Tool</h2></div><div style="text-align:center;padding:2rem"><div class="typing-dots"><div class="progress-status"><span class="progress-text">Analyzing content...</span></div></div></div>';
    
    try {
        const r = await apiFetch('/api/content/ingest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, level })
        });
        const d = await r.json();
        
        let html = '<div class="tool-header"><h2>📄 Content Analysis</h2></div><div class="content-ingestion">';
        
        // Summary
        html += `<div style="margin:0.75rem 0;padding:0.75rem;background:rgba(0,0,0,0.02);border-radius:8px">`;
        html += `<div style="font-weight:600;margin-bottom:0.25rem">Summary</div>`;
        html += `<div style="font-size:0.85rem">📝 ${d.summary.word_count} words • ${d.summary.sentence_count} sentences</div>`;
        html += `<div style="font-size:0.85rem">📚 ${d.summary.vocabulary_found} vocabulary items found • 🃏 ${d.summary.flashcards_generated} flashcards created</div>`;
        html += '</div>';
        
        if (d.vocabulary && d.vocabulary.length > 0) {
            html += '<div style="margin:0.75rem 0"><div style="font-weight:600;margin-bottom:0.5rem">Vocabulary Found</div><div style="display:flex;flex-wrap:wrap;gap:0.375rem">';
            d.vocabulary.forEach(v => {
                html += `<span style="padding:0.25rem 0.5rem;background:var(--card);border:1px solid var(--border);border-radius:6px;font-size:0.85rem"><strong>${v.fr}</strong> = ${v.en}</span>`;
            });
            html += '</div></div>';
        }
        
        if (d.flashcards_count > 0) {
            html += `<div style="margin:0.75rem 0;padding:0.5rem;background:rgba(45,106,79,0.08);border-radius:6px;font-size:0.85rem">✅ ${d.flashcards_count} flashcards added to your deck!</div>`;
        }
        
        if (d.quiz && d.quiz.exercises && d.quiz.exercises.length > 0) {
            html += `<div style="margin:0.75rem 0"><div style="font-weight:600;margin-bottom:0.5rem">📝 Content Quiz</div>`;
            d.quiz.exercises.forEach((ex, i) => {
                const id = 'ci-' + Math.random().toString(36).substr(2, 8);
                html += `<div class="exercise-container" id="${id}">`;
                html += `<div class="exercise-prompt">${i+1}. ${ex.prompt}</div>`;
                html += `<div class="exercise-input-row">`;
                html += `<input class="exercise-input" placeholder="Type your answer..." onkeydown="if(event.key==='Enter')checkExercise('${id}', this)">`;
                html += `<button class="exercise-submit" onclick="checkExercise('${id}', this.previousElementSibling)">Check</button>`;
                html += `</div><div class="exercise-feedback" style="display:none"></div>`;
                html += `<script>window._exercises = window._exercises || {}; window._exercises['${id}'] = ${JSON.stringify(ex)};<\/script>`;
                html += '</div>';
            });
            html += '</div>';
        }
        
        html += '</div>';
        getToolContent().innerHTML = html;
    } catch(e) {
        getToolContent().innerHTML = '<div class="tool-header"><h2>📄 French Content Tool</h2></div><p style="color:var(--incorrect);text-align:center;padding:2rem">Error processing content. Try again.</p>';
    }
};

// ============================================================
// Adaptive Difficulty Analysis
// ============================================================
window.showAdaptiveAnalysis = async function() {
    showToolView('📊 Learning Analysis', '<div style="text-align:center;padding:2rem"><div class="typing-dots"><div class="progress-status"><span class="progress-text">Analyzing your performance...</span></div></div></div>');
    try {
        const r = await apiFetch('/api/adaptive/analysis');
        const d = await r.json();
        
        const { analysis, adjustments } = d;
        
        let html = '<div class="tool-header"><h2>📊 Your Learning Profile</h2></div><div class="adaptive-analysis">';
        
        html += `<div style="margin:0.75rem 0;padding:0.75rem;background:rgba(0,0,0,0.02);border-radius:8px">`;
        html += `<div class="flashcard-stats">`;
        html += `<div class="flashcard-stat"><div class="flashcard-stat-value">${analysis.total_exercises}</div><div class="flashcard-stat-label">Exercises Done</div></div>`;
        html += `<div class="flashcard-stat"><div class="flashcard-stat-value">${analysis.overall_accuracy}%</div><div class="flashcard-stat-label">Accuracy</div></div>`;
        html += `<div class="flashcard-stat"><div class="flashcard-stat-value">${analysis.recent_trend === 'improving' ? '📈' : analysis.recent_trend === 'declining' ? '📉' : '➡️'}</div><div class="flashcard-stat-label">Trend</div></div>`;
        html += '</div></div>';
        
        if (analysis.weak_types.length > 0) {
            html += '<div style="margin:0.75rem 0"><div style="font-weight:600;margin-bottom:0.5rem;color:var(--incorrect)">Areas to Improve</div>';
            analysis.weak_types.forEach(w => {
                html += `<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.375rem;font-size:0.85rem">`;
                html += `<span style="min-width:120px">${w.type.replace(/_/g, ' ')}</span>`;
                html += `<div style="flex:1;height:6px;background:var(--border);border-radius:3px;overflow:hidden"><div style="width:${w.accuracy}%;height:100%;background:var(--incorrect);border-radius:3px"></div></div>`;
                html += `<span style="min-width:40px;text-align:right">${w.accuracy}%</span></div>`;
            });
            html += '</div>';
        }
        
        if (analysis.strong_types.length > 0) {
            html += '<div style="margin:0.75rem 0"><div style="font-weight:600;margin-bottom:0.5rem;color:var(--correct)">Strengths</div>';
            analysis.strong_types.forEach(s => {
                html += `<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.375rem;font-size:0.85rem">`;
                html += `<span style="min-width:120px">${s.type.replace(/_/g, ' ')}</span>`;
                html += `<div style="flex:1;height:6px;background:var(--border);border-radius:3px;overflow:hidden"><div style="width:${s.accuracy}%;height:100%;background:var(--correct);border-radius:3px"></div></div>`;
                html += `<span style="min-width:40px;text-align:right">${s.accuracy}%</span></div>`;
            });
            html += '</div>';
        }
        
        if (analysis.recommendations.length > 0) {
            html += '<div style="margin:0.75rem 0"><div style="font-weight:600;margin-bottom:0.5rem">💡 Recommendations</div>';
            analysis.recommendations.forEach(rec => {
                html += `<div style="padding:0.5rem;background:rgba(45,106,79,0.08);border-radius:6px;font-size:0.85rem;margin-bottom:0.375rem">${rec}</div>`;
            });
            html += '</div>';
        }
        
        html += '<div style="margin:0.75rem 0;padding:0.5rem;background:rgba(0,0,0,0.02);border-radius:6px;font-size:0.8rem">';
        html += `<div>🎯 Practice exercises: ${adjustments.practice_count} per concept</div>`;
        html += `<div>🌐 Language ratio: ${Math.round(adjustments.french_ratio * 100)}% French / ${Math.round((1 - adjustments.french_ratio) * 100)}% English</div>`;
        html += `<div>📈 Complexity: ${adjustments.complexity}</div></div>`;
        
        html += '</div>';
        getToolContent().innerHTML = html;
    } catch(e) {
        getToolContent().innerHTML = '<div class="tool-header"><h2>📊 Learning Analysis</h2></div><p style="color:var(--incorrect);text-align:center;padding:2rem">Error loading analysis.</p>';
    }
};

// ============================================================
// Writing Correction Mode
// ============================================================
window.correctMyWriting = async function(text) {
    if (!text.trim()) return;
    
    showToolView('✍️ Writing Correction', '<div style="text-align:center;padding:2rem"><div class="typing-dots"><div class="progress-status"><span class="progress-text">Correcting your French writing...</span><div class="progress-bar"><div class="progress-fill progress-indeterminate"></div></div></div></div></div>');
    try {
        const r = await apiFetch('/api/writing/correct', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        const d = await r.json();
        
        let html = '<div class="tool-header"><h2>✍️ Writing Correction</h2></div>';
        
        if (d.formatted) {
            html += d.formatted;
        } else if (d.response) {
            html += '<div class="writing-correction">' + parseMarkdown(d.response) + '</div>';
        }
        
        if (d.total_xp) {
            html += `<div style="text-align:center;margin-top:1rem;padding:0.5rem;background:rgba(22,163,74,0.1);border-radius:8px;color:var(--correct);font-weight:500">+${d.xp_earned || 0} XP</div>`;
            updateXP(d.total_xp);
        }
        
        getToolContent().innerHTML = html;
    } catch(e) {
        getToolContent().innerHTML = '<div class="tool-header"><h2>✍️ Writing Correction</h2></div><p style="color:var(--incorrect);text-align:center;padding:2rem">Error correcting writing. Try again.</p>';
    }
};

// ============================================================
// Exam Simulation Mode
// ============================================================
let examState = { testType: null, sectionId: null, setNum: null, questions: [], answers: {}, timer: null, timeLeft: 0, startTime: 0, phase: 'idle', paused: false, currentIdx: 0 };

window.startMockTest = async function(testType) {
    showToolView(`📝 ${testType} Exam`, '<div style="text-align:center;padding:2rem"><div class="typing-dots"><div class="progress-status"><span class="progress-text">Loading exam...</span></div></div></div>');
    try {
        const r = await apiFetch(`/api/exam/sets/${testType}`);
        const exam = await r.json();
        
        let html = '';
        html += `<div class="exam-header" style="border-left:4px solid ${exam.color};padding-left:1rem;margin-bottom:1rem">`;
        html += `<div style="font-size:1.1rem;font-weight:700;color:${exam.color}">${exam.fullName}</div>`;
        html += `<div style="font-size:0.85rem;color:var(--muted-foreground)">${exam.description}</div>`;
        html += `<div style="font-size:0.8rem;margin-top:0.25rem">📋 ${exam.administeredBy} | 🎯 ${exam.usedFor}</div>`;
        html += '</div>';
        
        html += '<div style="margin-bottom:1rem;padding:0.75rem;background:rgba(0,0,0,0.02);border-radius:8px">';
        html += '<div style="font-weight:600;margin-bottom:0.5rem">📋 Official Exam Format</div>';
        for (const [sid, section] of Object.entries(exam.sections)) {
            html += `<div style="display:flex;align-items:center;gap:0.5rem;padding:0.375rem 0;font-size:0.85rem">`;
            html += `<span>${section.icon}</span>`;
            html += `<span style="flex:1"><strong>${section.title}</strong> <span style="color:var(--muted-foreground)">${section.titleFr}</span></span>`;
            html += `<span style="color:var(--muted-foreground)">${section.durationMinutes}min</span>`;
            html += '</div>';
        }
        html += '</div>';
        
        for (const [sid, section] of Object.entries(exam.sections)) {
            html += `<div style="margin-bottom:1rem">`;
            html += `<div style="font-weight:600;margin-bottom:0.5rem">${section.icon} ${section.title}</div>`;
            html += '<div style="display:flex;flex-wrap:wrap;gap:0.375rem">';
            for (const set of section.sets) {
                const label = set.isAI ? '🤖 AI' : `Set ${set.setNum}`;
                const cls = set.isAI ? 'exam-set-btn ai' : 'exam-set-btn';
                html += `<button class="${cls}" onclick="startExamSection('${testType}', '${sid}', ${set.setNum})" style="border-color:${exam.color}">${label}<br><small>${set.questionCount}Q</small></button>`;
            }
            html += '</div></div>';
        }
        
        getToolContent().innerHTML = `<div class="tool-header"><h2>📝 ${exam.fullName}</h2></div>` + html;
    } catch(e) {
        getToolContent().innerHTML = `<div class="tool-header"><h2>📝 ${testType} Exam</h2></div><p style="color:var(--incorrect);text-align:center;padding:2rem">Error loading exam. Try again.</p>`;
    }
};

window.startExamSection = async function(testType, sectionId, setNum) {
    getToolContent().innerHTML = '<div style="text-align:center;padding:2rem"><div class="typing-dots"><div class="progress-status"><span class="progress-text">Loading questions...</span></div></div></div>';
    try {
        const r = await apiFetch(`/api/exam/questions/${testType}/${sectionId}/${setNum}`);
        const data = await r.json();
        
        if (!data.questions || data.questions.length === 0) {
            getToolContent().innerHTML = `<div class="tool-header"><h2>📝 Exam</h2></div><p style="color:var(--muted-foreground);text-align:center;padding:2rem">${data.message || 'No questions available for this set.'}</p>`;
            return;
        }
        
        examState = { testType, sectionId, setNum, questions: data.questions, answers: {}, timer: null, timeLeft: 0, startTime: Date.now(), phase: 'taking', paused: false, currentIdx: 0 };
        
        const examR = await apiFetch(`/api/exam/sets/${testType}`);
        const exam = await examR.json();
        const section = exam.sections[sectionId];
        examState.timeLeft = (section?.durationMinutes || 15) * 60;
        
        renderExamQuestion(0);
        startExamTimer();
    } catch(e) {
        getToolContent().innerHTML = '<div class="tool-header"><h2>📝 Exam</h2></div><p style="color:var(--incorrect);text-align:center;padding:2rem">Error loading questions.</p>';
    }
};

function renderExamQuestion(idx) {
    if (idx >= examState.questions.length) {
        submitExam();
        return;
    }
    
    const q = examState.questions[idx];
    const total = examState.questions.length;
    
    let html = `<div class="exam-container" id="examContainer">`;
    
    examState.currentIdx = idx;

    // Header with timer and progress
    html += `<div class="exam-toolbar">`;
    html += `<div style="display:flex;align-items:center;gap:0.75rem">`;
    html += `<div class="test-timer" id="examTimer">⏱️ ${formatTime(examState.timeLeft)}</div>`;
    html += `<button class="exam-nav-btn" id="examPauseBtn" onclick="toggleExamPause()" title="Pause/resume test">${examState.paused ? '▶️ Resume' : '⏸️ Pause'}</button>`;
    html += `</div>`;
    html += `<div style="font-size:0.85rem;color:var(--muted-foreground)">Question ${idx+1} of ${total}</div>`;
    html += '</div>';
    
    // Question navigation
    html += '<div class="exam-nav">';
    examState.questions.forEach((eq, i) => {
        const answered = examState.answers[eq.id] !== undefined;
        const current = i === idx;
        html += `<button class="exam-nav-btn ${current ? 'current' : ''} ${answered ? 'answered' : ''}" onclick="goToExamQuestion(${i})">${i+1}</button>`;
    });
    html += '</div>';
    
    // Question content
    html += `<div class="test-question" id="examQuestion">`;
    if (q.audioText) {
        html += `<button class="btn-speak" onclick="speakText('${q.audioText.replace(/'/g, "\\'")}')">🔊 Listen to audio</button>`;
    }
    html += `<div class="test-question-level">${q.level}</div>`;
    html += `<p style="margin-bottom:0.75rem">${q.prompt}</p>`;
    html += '<div class="quiz-options">';
    q.options.forEach((o, j) => {
        const selected = examState.answers[q.id] === j;
        html += `<button class="quiz-option ${selected ? 'selected' : ''}" onclick="selectExamAnswer('${q.id}', ${j}, this)">${String.fromCharCode(65+j)}. ${o}</button>`;
    });
    html += '</div></div>';
    
    // Navigation buttons
    html += '<div class="exam-nav-buttons">';
    if (idx > 0) html += `<button class="exam-nav-btn prev" onclick="goToExamQuestion(${idx-1})">← Previous</button>`;
    if (idx < total - 1) {
        html += `<button class="exam-nav-btn next" onclick="goToExamQuestion(${idx+1})">Next →</button>`;
    } else {
        html += `<button class="exam-nav-btn submit" onclick="submitExam()">Submit Test</button>`;
    }
    html += '</div>';
    
    html += '</div>';
    
    const container = document.getElementById('examContainer');
    if (container) {
        container.outerHTML = html;
    } else {
        getToolContent().innerHTML = `<div class="tool-header"><h2>📝 Exam</h2></div>` + html;
    }
}

function startExamTimer() {
    if (examState.paused) return;
    if (examState.timer) clearInterval(examState.timer);
    examState.timer = setInterval(() => {
        if (examState.paused) return;
        examState.timeLeft--;
        const timerEl = document.getElementById('examTimer');
        if (timerEl) timerEl.textContent = '⏱️ ' + formatTime(examState.timeLeft);
        if (examState.timeLeft <= 0) {
            clearInterval(examState.timer);
            submitExam();
        }
    }, 1000);
}

function stopExamTimer() {
    if (examState.timer) {
        clearInterval(examState.timer);
        examState.timer = null;
    }
}

window.toggleExamPause = function() {
    if (examState.paused) {
        resumeExam();
    } else {
        pauseExam();
    }
};

function pauseExam() {
    if (examState.phase !== 'taking' || examState.paused) return;
    examState.paused = true;
    stopExamTimer();

    const container = document.getElementById('examContainer');
    if (!container) return;

    let overlay = document.getElementById('examPausedOverlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'examPausedOverlay';
        overlay.className = 'exam-paused-overlay';
        overlay.innerHTML = `
            <div class="exam-paused-card">
                <div style="font-size:2rem;margin-bottom:0.5rem">⏸️</div>
                <div style="font-size:1.1rem;font-weight:600;margin-bottom:0.25rem">Test Paused</div>
                <div style="font-size:0.85rem;color:var(--muted-foreground);margin-bottom:1rem">Take your time. Your progress is saved.</div>
                <button class="exam-nav-btn" onclick="resumeExam()" style="font-size:1rem;padding:0.6rem 1.25rem">▶️ Resume Test</button>
            </div>
        `;
        container.appendChild(overlay);
    } else {
        overlay.style.display = 'flex';
    }

    const pauseBtn = document.getElementById('examPauseBtn');
    if (pauseBtn) pauseBtn.textContent = '▶️ Resume';
}

window.resumeExam = function() {
    if (examState.phase !== 'taking' || !examState.paused) return;
    examState.paused = false;

    const overlay = document.getElementById('examPausedOverlay');
    if (overlay) overlay.style.display = 'none';

    const pauseBtn = document.getElementById('examPauseBtn');
    if (pauseBtn) pauseBtn.textContent = '⏸️ Pause';

    startExamTimer();
};

window.selectExamAnswer = function(qid, idx, btn) {
    examState.answers[qid] = idx;
    const q = btn.closest('.test-question');
    q.querySelectorAll('.quiz-option').forEach(o => o.classList.remove('selected'));
    btn.classList.add('selected');
};

window.goToExamQuestion = function(idx) {
    renderExamQuestion(idx);
};

async function submitExam() {
    if (examState.timer) clearInterval(examState.timer);
    
    const durationSec = Math.round((Date.now() - examState.startTime) / 1000);
    
    try {
        getToolContent().innerHTML = '<div style="text-align:center;padding:2rem"><div class="typing-dots"><div class="progress-status"><span class="progress-text">Grading your test...</span></div></div></div>';
        const r = await apiFetch(`/api/exam/submit/${examState.testType}/${examState.sectionId}/${examState.setNum}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ answers: examState.answers, duration_sec: durationSec })
        });
        const result = await r.json();
        
        renderExamResults(result);
    } catch(e) {
        getToolContent().innerHTML = '<div class="tool-header"><h2>📝 Exam Results</h2></div><p style="color:var(--incorrect);text-align:center;padding:2rem">Error submitting test.</p>';
    }
}

function renderExamResults(result) {
    let html = `<div class="tool-header"><h2>📝 Exam Results</h2></div>`;
    
    html += `<div class="test-results-header">`;
    html += `<div class="test-score-ring">`;
    html += `<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="45" fill="none" stroke="#e5e7eb" stroke-width="8"/><circle cx="50" cy="50" r="45" fill="none" stroke="${result.score >= 60 ? 'var(--correct)' : 'var(--incorrect)'}" stroke-width="8" stroke-dasharray="${result.score * 2.83} 283" transform="rotate(-90 50 50)"/></svg>`;
    html += `<div class="test-score-value">${result.score}%</div>`;
    html += '</div>';
    html += `<div class="test-score-details">`;
    html += `<div style="font-size:1.1rem;font-weight:600">✅ ${result.correct}/${result.total} correct</div>`;
    html += `<div>⏱️ Time: ${formatTime(result.durationSec)}</div>`;
    html += `<div>📊 Estimated Level: <strong style="color:var(--primary)">${result.level}</strong></div>`;
    html += '</div></div>';
    
    if (result.levelBreakdown && Object.keys(result.levelBreakdown).length > 0) {
        html += '<div style="margin:1rem 0;padding:0.75rem;background:rgba(0,0,0,0.02);border-radius:8px">';
        html += '<div style="font-weight:600;margin-bottom:0.5rem">📊 Performance by Level</div>';
        for (const [lvl, stats] of Object.entries(result.levelBreakdown)) {
            const pct = stats.accuracy;
            const color = pct >= 80 ? 'var(--correct)' : pct >= 60 ? 'var(--secondary)' : 'var(--incorrect)';
            html += `<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.375rem">`;
            html += `<span style="min-width:30px;font-weight:600">${lvl}</span>`;
            html += `<div style="flex:1;height:8px;background:var(--border);border-radius:4px;overflow:hidden"><div style="width:${pct}%;height:100%;background:${color};border-radius:4px"></div></div>`;
            html += `<span style="min-width:40px;text-align:right;font-size:0.85rem">${stats.correct}/${stats.total}</span></div>`;
        }
        html += '</div>';
    }
    
    html += '<div style="margin-top:1rem"><div style="font-weight:600;margin-bottom:0.5rem">📝 Question Review</div>';
    result.details.forEach((d, i) => {
        html += `<div class="test-review-item ${d.correct ? 'correct' : 'incorrect'}">`;
        html += `<div class="test-review-num">${i+1} ${d.correct ? '✅' : '❌'}</div>`;
        html += `<div style="flex:1"><div style="font-size:0.85rem">${d.prompt || 'Question ' + (i+1)}</div>`;
        if (!d.correct && d.explanation) {
            html += `<div style="font-size:0.8rem;color:var(--correct);margin-top:0.25rem">${d.explanation}</div>`;
        }
        html += '</div></div>';
    });
    html += '</div>';
    
    html += '<div style="display:flex;gap:0.5rem;margin-top:1rem">';
    html += `<button class="exercise-submit" onclick="startMockTest('${result.testType}')" style="flex:1">Try Another Set</button>`;
    html += `<button class="exam-nav-btn" onclick="showTestStats()" style="flex:1">View History</button>`;
    html += '</div>';
    
    getToolContent().innerHTML = html;
}

window.showTestStats = async function() {
    showToolView('📊 Test History', '<div style="text-align:center;padding:2rem"><div class="typing-dots"><div class="progress-status"><span class="progress-text">Loading test history...</span></div></div></div>');
    try {
        const [tefStats, tcfStats] = await Promise.all([
            apiFetch('/api/exam/stats/TEF').then(r => r.json()),
            apiFetch('/api/exam/stats/TCF').then(r => r.json()),
        ]);
        
        let html = '<div class="tool-header"><h2>📊 Test History</h2></div><div class="test-stats">';
        html += '<div class="quiz-title">📊 Exam Statistics</div>';
        
        for (const [type, stats] of [['TEF', tefStats], ['TCF', tcfStats]]) {
            if (stats.total === 0) continue;
            html += `<div style="margin:1rem 0;padding:1rem;background:rgba(0,0,0,0.02);border-radius:8px">`;
            html += `<div style="font-weight:600;font-size:1rem;margin-bottom:0.5rem">${type} — ${stats.total} tests taken</div>`;
            html += `<div class="flashcard-stats">`;
            html += `<div class="flashcard-stat"><div class="flashcard-stat-value">${stats.avg_score}%</div><div class="flashcard-stat-label">Avg Score</div></div>`;
            html += `<div class="flashcard-stat"><div class="flashcard-stat-value">${stats.best_score}%</div><div class="flashcard-stat-label">Best Score</div></div>`;
            html += '</div>';
            
            // Level breakdown
            if (stats.by_level && Object.keys(stats.by_level).length > 0) {
                html += '<div style="margin-top:0.75rem">';
                for (const [lvl, s] of Object.entries(stats.by_level)) {
                    html += `<div style="display:flex;align-items:center;gap:0.5rem;font-size:0.85rem;margin-bottom:0.25rem">`;
                    html += `<span style="min-width:30px;font-weight:600">${lvl}</span>`;
                    html += `<div style="flex:1;height:6px;background:var(--border);border-radius:3px;overflow:hidden">`;
                    html += `<div style="width:${s.accuracy}%;height:100%;background:${s.accuracy >= 80 ? 'var(--correct)' : s.accuracy >= 60 ? 'var(--secondary)' : 'var(--incorrect)'};border-radius:3px"></div>`;
                    html += '</div>';
                    html += `<span style="min-width:40px;text-align:right">${s.correct}/${s.total}</span>`;
                    html += '</div>';
                }
                html += '</div>';
            }
            html += '</div>';
        }
        
        if (tefStats.total === 0 && tcfStats.total === 0) {
            html += '<p style="color:var(--muted-foreground);text-align:center;padding:1rem">No test results yet. Take a practice test to see your stats!</p>';
        }
        
        html += '</div>';
        getToolContent().innerHTML = html;
    } catch(e) {
        getToolContent().innerHTML = '<div class="tool-header"><h2>📊 Test History</h2></div><p style="color:var(--incorrect);text-align:center;padding:2rem">Error loading test stats.</p>';
    }
};

function formatTime(seconds) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
}

// ============================================================
// Phase 4: Collaboration — Comments, Share, Export
// ============================================================

// --- Comments ---
const commentsModal = document.getElementById('commentsModal');
const closeComments = document.getElementById('closeComments');
const commentInput = document.getElementById('commentInput');
const addCommentBtn = document.getElementById('addComment');
const commentsList = document.getElementById('commentsList');
const btnComments = document.getElementById('btnComments');

btnComments?.addEventListener('click', async () => {
    if (!currentConvId) {
        alert('Start a conversation first!');
        return;
    }
    await loadComments();
    commentsModal.style.display = 'flex';
});

closeComments?.addEventListener('click', () => { commentsModal.style.display = 'none'; });
commentsModal?.addEventListener('click', (e) => { if (e.target === commentsModal) commentsModal.style.display = 'none'; });

addCommentBtn?.addEventListener('click', async () => {
    const msg = commentInput.value.trim();
    if (!msg || !currentConvId) return;
    
    try {
        await apiFetch('/api/comments', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ conv_id: currentConvId, message: msg })
        });
        commentInput.value = '';
        await loadComments();
    } catch (e) {
        console.error('Error adding comment:', e);
    }
});

commentInput?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') addCommentBtn?.click();
});

async function loadComments() {
    if (!currentConvId) return;
    try {
        const r = await apiFetch(`/api/comments/${currentConvId}`);
        const comments = await r.json();
        
        if (comments.length === 0) {
            commentsList.innerHTML = '<p class="no-comments">No notes yet. Add one below!</p>';
            return;
        }
        
        commentsList.innerHTML = comments.map(c => `
            <div class="comment-item">
                <div class="comment-header">
                    <span class="comment-author">${escapeHtml(c.author || 'You')}</span>
                    <span class="comment-time">${new Date(c.created_at * 1000).toLocaleString()}</span>
                    <button class="comment-delete" onclick="deleteComment('${c.id}')">×</button>
                </div>
                <div class="comment-message">${escapeHtml(c.message)}</div>
            </div>
        `).join('');
    } catch (e) {
        console.error('Error loading comments:', e);
        commentsList.innerHTML = '<p class="no-comments">Error loading comments.</p>';
    }
}

window.deleteComment = async function(commentId) {
    if (!currentConvId || !confirm('Delete this comment?')) return;
    try {
        await apiFetch(`/api/comments/${currentConvId}/${commentId}`, { method: 'DELETE' });
        await loadComments();
    } catch (e) {
        console.error('Error deleting comment:', e);
    }
};

// --- Share ---
const shareModal = document.getElementById('shareModal');
const closeShare = document.getElementById('closeShare');
const btnShare = document.getElementById('btnShare');
const generateShareLink = document.getElementById('generateShareLink');
const shareLinkContainer = document.getElementById('shareLinkContainer');
const shareLinkInput = document.getElementById('shareLink');
const copyShareLink = document.getElementById('copyShareLink');
const sharedList = document.getElementById('sharedList');

btnShare?.addEventListener('click', async () => {
    if (!currentConvId) {
        alert('Start a conversation first!');
        return;
    }
    shareLinkContainer.style.display = 'none';
    await loadSharedList();
    shareModal.style.display = 'flex';
});

closeShare?.addEventListener('click', () => { shareModal.style.display = 'none'; });
shareModal?.addEventListener('click', (e) => { if (e.target === shareModal) shareModal.style.display = 'none'; });

generateShareLink?.addEventListener('click', async () => {
    try {
        const r = await apiFetch('/api/share', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ conv_id: currentConvId })
        });
        const data = await r.json();
        shareLinkInput.value = `${window.location.origin}${data.url}`;
        shareLinkContainer.style.display = 'flex';
        addMessage(`🔗 Share link created! Anyone with this link can view this conversation.`, 'assistant');
        await loadSharedList();
    } catch (e) {
        console.error('Error creating share link:', e);
        addMessage('Error creating share link.', 'assistant');
    }
});

copyShareLink?.addEventListener('click', () => {
    shareLinkInput.select();
    navigator.clipboard.writeText(shareLinkInput.value).then(() => {
        copyShareLink.textContent = '✓ Copied!';
        setTimeout(() => { copyShareLink.textContent = 'Copy'; }, 2000);
    });
});

async function loadSharedList() {
    try {
        const r = await apiFetch('/api/shared');
        const shared = await r.json();
        
        if (shared.length === 0) {
            sharedList.innerHTML = '';
            return;
        }
        
        sharedList.innerHTML = `
            <h4 class="shared-list-title">Previously Shared</h4>
            ${shared.map(s => `
                <div class="shared-item">
                    <span class="shared-title">${escapeHtml(s.title)}</span>
                    <button class="shared-copy" onclick="navigator.clipboard.writeText('${window.location.origin}/share/${s.id}')">Copy Link</button>
                    <button class="shared-delete" onclick="deleteShare('${s.id}')">×</button>
                </div>
            `).join('')}
        `;
    } catch (e) {
        console.error('Error loading shared list:', e);
    }
}

window.deleteShare = async function(shareId) {
    if (!confirm('Delete this shared link?')) return;
    try {
        await apiFetch(`/api/share/${shareId}`, { method: 'DELETE' });
        await loadSharedList();
    } catch (e) {
        console.error('Error deleting share:', e);
    }
};

// --- Export ---
const exportModal = document.getElementById('exportModal');
const closeExport = document.getElementById('closeExport');
const btnExport = document.getElementById('btnExport');
const exportMarkdown = document.getElementById('exportMarkdown');
const exportJson = document.getElementById('exportJson');
const exportPreview = document.getElementById('exportPreview');
const exportPreviewText = document.getElementById('exportPreviewText');
const downloadExport = document.getElementById('downloadExport');

let currentExportData = null;
let currentExportFormat = 'markdown';

btnExport?.addEventListener('click', async () => {
    if (!currentConvId) {
        alert('Start a conversation first!');
        return;
    }
    exportPreview.style.display = 'none';
    exportModal.style.display = 'flex';
});

closeExport?.addEventListener('click', () => { exportModal.style.display = 'none'; });
exportModal?.addEventListener('click', (e) => { if (e.target === exportModal) exportModal.style.display = 'none'; });

exportMarkdown?.addEventListener('click', async () => {
    await fetchExport('markdown');
});

exportJson?.addEventListener('click', async () => {
    await fetchExport('json');
});

async function fetchExport(format) {
    try {
        const r = await apiFetch('/api/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ conv_id: currentConvId, format })
        });
        const data = await r.json();
        currentExportData = data;
        currentExportFormat = format;
        
        if (format === 'markdown') {
            exportPreviewText.value = data.content;
        } else {
            exportPreviewText.value = JSON.stringify(data, null, 2);
        }
        exportPreview.style.display = 'block';
        addMessage(`📥 Export ready as ${format}. You can preview and download below.`, 'assistant');
    } catch (e) {
        console.error('Error exporting:', e);
        addMessage('Error exporting conversation.', 'assistant');
    }
}

downloadExport?.addEventListener('click', () => {
    if (!currentExportData) return;
    
    const blob = new Blob(
        [currentExportFormat === 'markdown' ? currentExportData.content : JSON.stringify(currentExportData, null, 2)],
        { type: currentExportFormat === 'markdown' ? 'text/markdown' : 'application/json' }
    );
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${currentExportData.title || 'chat'}.${currentExportFormat === 'markdown' ? 'md' : 'json'}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    addMessage('📥 Download started!', 'assistant');
});
