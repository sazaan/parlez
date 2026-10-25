(() => {
    'use strict';

    const loginView = document.getElementById('loginView');
    const setupView = document.getElementById('setupView');
    const dashboardView = document.getElementById('dashboardView');
    const loginForm = document.getElementById('loginForm');
    const loginMessage = document.getElementById('loginMessage');
    const pageMessage = document.getElementById('pageMessage');
    const aiMessage = document.getElementById('aiMessage');
    const courseMessage = document.getElementById('courseMessage');
    const providerSelect = document.getElementById('providerSelect');
    const modelInput = document.getElementById('modelId');
    const keyStatusTitle = document.getElementById('keyStatusTitle');
    const keyStatusText = document.getElementById('keyStatusText');
    const testProviderButton = document.getElementById('testProviderButton');
    const saveProviderButton = document.getElementById('saveProviderButton');
    const rollbackProviderButton = document.getElementById('rollbackProviderButton');
    let csrfToken = '';
    let currentConfig = null;
    let testedModelKey = '';

    function setVisible(element, visible) {
        element.hidden = !visible;
    }

    function showLogin(message = '') {
        setVisible(loginView, true);
        setVisible(setupView, false);
        setVisible(dashboardView, false);
        loginMessage.textContent = message;
    }

    function escapeHTML(value) {
        return String(value ?? '').replace(/[&<>"']/g, character => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
        })[character]);
    }

    async function readResponse(response) {
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
            const error = new Error(payload.detail || `Request failed (${response.status}).`);
            error.status = response.status;
            throw error;
        }
        return payload;
    }

    async function adminRequest(path, options = {}) {
        const method = (options.method || 'GET').toUpperCase();
        const headers = new Headers(options.headers || {});
        if (method !== 'GET' && csrfToken) headers.set('X-CSRF-Token', csrfToken);
        if (options.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
        const response = await fetch(path, {
            ...options,
            method,
            headers,
            credentials: 'same-origin',
            cache: 'no-store'
        });
        try {
            return await readResponse(response);
        } catch (error) {
            if (error.status === 401) showLogin('Your admin session has expired. Sign in again.');
            throw error;
        }
    }

    function setMessage(element, message, kind = 'error') {
        element.textContent = message || '';
        element.dataset.kind = kind;
    }

    function updateProviderStatus() {
        if (!currentConfig) return;
        const provider = currentConfig.ai.providers.find(item => item.id === providerSelect.value);
        const current = provider && provider.id === currentConfig.ai.provider;
        keyStatusTitle.textContent = provider && provider.configured
            ? 'Provider key configured on server'
            : 'Provider key missing on server';
        keyStatusText.textContent = provider && provider.configured
            ? 'The key is never returned to this page.'
            : 'Add the provider key to the backend environment, then restart the service.';
        document.getElementById('activePill').textContent = current ? 'Current default' : 'New selection';
        document.getElementById('activePill').className = `pill ${provider && provider.configured ? 'pill-neutral' : 'pill-warning'}`;
        const selectionKey = `${providerSelect.value}:${modelInput.value.trim()}`;
        const unchanged = providerSelect.value === currentConfig.ai.provider && modelInput.value.trim() === currentConfig.ai.model;
        testProviderButton.disabled = !(provider && provider.configured);
        saveProviderButton.disabled = !(provider && provider.configured && (unchanged || testedModelKey === selectionKey));
        rollbackProviderButton.disabled = !currentConfig.ai.can_rollback;
    }

    function renderProviderOptions(ai) {
        providerSelect.innerHTML = '';
        ai.providers.forEach(provider => {
            const option = document.createElement('option');
            option.value = provider.id;
            option.textContent = `${provider.label}${provider.configured ? '' : ' · key not configured'}`;
            option.disabled = !provider.configured && provider.id !== ai.provider;
            providerSelect.appendChild(option);
        });
        providerSelect.value = ai.provider;
        modelInput.value = ai.model;
        providerSelect.onchange = () => {
            const selected = ai.providers.find(item => item.id === providerSelect.value);
            if (selected) modelInput.value = selected.default_model || '';
            testedModelKey = '';
            setMessage(aiMessage, '');
            updateProviderStatus();
        };
        updateProviderStatus();
    }

    function renderCourseCards(courseConfig) {
        const grid = document.getElementById('courseGrid');
        grid.innerHTML = '';
        courseConfig.levels.forEach(level => {
            const card = document.createElement('article');
            card.className = 'course-card';
            card.dataset.course = level.level;
            const checked = level.enabled ? 'checked' : '';
            const required = level.level === 'A1';
            const unattestedRelease = !required && level.content_status === 'published_unattested' && level.review_status === 'unattested';
            const pendingReview = !required && level.review_status !== 'reviewed' && !unattestedRelease;
            const outcomes = Array.isArray(level.level_outcomes) ? level.level_outcomes : [];
            const reviewForm = `<label>Reviewer name<input type="text" maxlength="120" data-reviewer-name autocomplete="name"></label><label>Relevant qualification<textarea maxlength="300" data-reviewer-qualification rows="2" placeholder="Describe French-language teaching or curriculum-review experience"></textarea></label><label class="review-confirm"><input type="checkbox" data-review-confirm><span>I confirm the named qualified educator reviewed the lessons, tasks, and answer keys for this version.</span></label><button type="button" class="review-submit" data-course-review="${escapeHTML(level.level)}">Record review attestation</button>`;
            const reviewPanel = required ? '' : (unattestedRelease
                ? `<div class="course-review-panel course-review-complete"><strong>Published without reviewer attestation</strong><p>No reviewer name or qualification is stored. This public practice release does not verify credentials or certify CEFR alignment.</p><details><summary>Record a qualified review if available</summary>${reviewForm}</details></div>`
                : pendingReview
                    ? `<div class="course-review-panel"><strong>Release review required</strong><p>A qualified French educator must review this exact course version before release. This form records an administrator’s self-attestation only; it does not verify credentials or certify CEFR alignment.</p>${reviewForm}</div>`
                    : `<div class="course-review-panel course-review-complete"><strong>Review attestation recorded</strong><p>${escapeHTML(level.reviewer_name || 'Reviewer')} · ${escapeHTML(level.reviewer_qualification || '')}${level.reviewed_at ? ` · ${escapeHTML(new Date(level.reviewed_at).toLocaleString())}` : ''}</p><p>Verify reviewer credentials independently. This attestation is not official certification.</p></div>`);
            const contentStatus = level.content_status === 'published_unattested' ? 'published · no attestation' : (level.content_status || 'draft');
            const toggleStatus = unattestedRelease ? (level.enabled ? 'Live · no attestation' : 'Off · no attestation') : (required ? 'Required' : (pendingReview ? 'Review first' : (level.enabled ? 'Live' : 'Off')));
            const units = level.units.map(unit => `
                <label class="module-row">
                    <span><span class="module-name">${escapeHTML(unit.title)}</span><span class="module-count">${unit.lesson_count} lesson${unit.lesson_count === 1 ? '' : 's'}</span>${unit.capstone ? `<span class="module-capstone">Mission: ${escapeHTML(unit.capstone)}</span>` : ''}</span>
                    <input type="checkbox" data-unit-level="${escapeHTML(level.level)}" data-unit-id="${escapeHTML(unit.id)}" ${unit.enabled ? 'checked' : ''} aria-label="Publish ${escapeHTML(unit.title)}">
                </label>
            `).join('');
            card.innerHTML = `
                <div class="course-card-header">
                    <div class="course-card-title"><span class="level-token">${escapeHTML(level.level)}</span><div><h3>${escapeHTML(level.title)}</h3><div class="course-meta">${level.module_count} modules · ${level.lesson_count} lessons · v${escapeHTML(level.version || '1.0')} · ${escapeHTML(contentStatus)}</div></div></div>
                    <label class="toggle-wrap"><input class="toggle" type="checkbox" data-level-toggle="${escapeHTML(level.level)}" ${checked} ${(required || pendingReview) ? 'disabled' : ''} aria-label="Publish ${escapeHTML(level.level)}">${toggleStatus}</label>
                </div>
                ${level.release_warning ? `<p class="course-card-warning">${escapeHTML(level.release_warning)}</p>` : ''}
                ${reviewPanel}
                ${outcomes.length ? `<div class="course-level-outcomes"><strong>Level outcomes</strong><ul>${outcomes.map(outcome => `<li>${escapeHTML(outcome)}</li>`).join('')}</ul></div>` : ''}
                <div class="module-list">${units}</div>
            `;
            grid.appendChild(card);
        });

        grid.querySelectorAll('[data-level-toggle]').forEach(toggle => {
            toggle.addEventListener('change', () => {
                const label = toggle.closest('.toggle-wrap');
                if (label && toggle.dataset.levelToggle !== 'A1') {
                    label.lastChild.textContent = toggle.checked ? 'Live' : 'Off';
                }
            });
        });

        grid.querySelectorAll('[data-course-review]').forEach(button => {
            button.addEventListener('click', async () => {
                const panel = button.closest('.course-review-panel');
                const reviewer_name = panel.querySelector('[data-reviewer-name]').value.trim();
                const qualification = panel.querySelector('[data-reviewer-qualification]').value.trim();
                const confirm_review = panel.querySelector('[data-review-confirm]').checked;
                if (!confirm_review) {
                    setMessage(courseMessage, 'Confirm the qualified-educator review before recording it.');
                    return;
                }
                button.disabled = true;
                setMessage(courseMessage, 'Recording the version-specific review attestation…', 'info');
                try {
                    const courses = await adminRequest(`/api/admin/courses/${encodeURIComponent(button.dataset.courseReview)}/review`, {
                        method: 'POST',
                        body: JSON.stringify({ reviewer_name, qualification, confirm_review })
                    });
                    currentConfig.courses = courses;
                    renderCourseCards(courses);
                    updateSummary(currentConfig);
                    setMessage(courseMessage, 'Review attestation recorded. Verify the reviewer’s credentials independently, then enable the level if it is ready.', 'success');
                } catch (error) {
                    button.disabled = false;
                    setMessage(courseMessage, error.message);
                }
            });
        });
    }

    function renderAudit(entries) {
        const list = document.getElementById('auditList');
        if (!entries.length) {
            list.innerHTML = '<p class="empty-state">No administrative changes have been recorded yet.</p>';
            return;
        }
        list.innerHTML = entries.map(entry => {
            const date = new Date((entry.created_at || 0) * 1000);
            const details = Object.entries(entry.details || {}).map(([key, value]) => `${key.replaceAll('_', ' ')}: ${Array.isArray(value) ? value.join(', ') : value}`).join(' · ');
            return `<div class="audit-row"><span class="audit-time">${escapeHTML(date.toLocaleString())}</span><span class="audit-action">${escapeHTML(entry.action.replaceAll('_', ' '))}</span><span class="audit-details">${escapeHTML(details || entry.username)}</span></div>`;
        }).join('');
    }

    function updateSummary(config, health = null) {
        const provider = config.ai.providers.find(item => item.id === config.ai.provider);
        document.getElementById('statusProvider').textContent = provider ? provider.label : config.ai.provider;
        document.getElementById('statusModel').textContent = config.ai.model;
        document.getElementById('statusLevels').textContent = config.courses.enabled_levels.join(' · ');
        if (health) {
            const backend = document.getElementById('statusBackend');
            backend.textContent = health.backend === 'healthy' ? 'Healthy' : 'Degraded';
            backend.classList.toggle('status-good', health.backend === 'healthy' && health.database === 'connected');
            backend.classList.toggle('status-bad', health.backend !== 'healthy' || health.database !== 'connected');
            document.getElementById('statusDatabase').textContent = `Database ${health.database} · ${health.provider_key_configured ? 'AI key configured' : 'AI key missing'}`;
        }
        document.getElementById('adminIdentity').textContent = 'Signed in as ' + (document.getElementById('adminIdentity').dataset.username || 'administrator');
    }

    async function loadDashboard() {
        const [config, audit, health] = await Promise.all([
            adminRequest('/api/admin/config'),
            adminRequest('/api/admin/audit?limit=60'),
            adminRequest('/api/admin/health')
        ]);
        currentConfig = config;
        renderProviderOptions(config.ai);
        renderCourseCards(config.courses);
        renderAudit(audit);
        updateSummary(config, health);
        setVisible(loginView, false);
        setVisible(setupView, false);
        setVisible(dashboardView, true);
    }

    async function checkSession() {
        const response = await fetch('/api/admin/session', { credentials: 'same-origin', cache: 'no-store' });
        if (response.status === 503) {
            setVisible(loginView, false);
            setVisible(dashboardView, false);
            setVisible(setupView, true);
            return;
        }
        if (response.status === 401) {
            showLogin();
            return;
        }
        const session = await readResponse(response);
        csrfToken = session.csrf_token;
        document.getElementById('adminIdentity').dataset.username = session.username;
        await loadDashboard();
    }

    loginForm.addEventListener('submit', async event => {
        event.preventDefault();
        setMessage(loginMessage, '');
        const submit = loginForm.querySelector('button[type="submit"]');
        submit.disabled = true;
        try {
            const response = await fetch('/api/admin/login', {
                method: 'POST',
                credentials: 'same-origin',
                cache: 'no-store',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: document.getElementById('adminUsername').value,
                    password: document.getElementById('adminPassword').value,
                    totp: document.getElementById('adminTotp').value
                })
            });
            await readResponse(response);
            document.getElementById('adminPassword').value = '';
            document.getElementById('adminTotp').value = '';
            await checkSession();
        } catch (error) {
            setMessage(loginMessage, error.message || 'Sign in failed.');
        } finally {
            submit.disabled = false;
        }
    });

    providerSelect.addEventListener('change', updateProviderStatus);
    modelInput.addEventListener('input', () => {
        setMessage(aiMessage, '');
        updateProviderStatus();
    });

    testProviderButton.addEventListener('click', async () => {
        setMessage(aiMessage, 'Testing with a short, synthetic prompt…', 'info');
        testProviderButton.disabled = true;
        try {
            const result = await adminRequest('/api/admin/ai/test', {
                method: 'POST',
                body: JSON.stringify({ provider: providerSelect.value, model: modelInput.value.trim() })
            });
            testedModelKey = `${result.provider}:${result.model}`;
            setMessage(aiMessage, `Connection succeeded: ${result.message} You can now save this model.`, 'success');
        } catch (error) {
            testedModelKey = '';
            setMessage(aiMessage, error.message);
        } finally {
            updateProviderStatus();
        }
    });

    saveProviderButton.addEventListener('click', async () => {
        setMessage(aiMessage, '');
        saveProviderButton.disabled = true;
        try {
            const ai = await adminRequest('/api/admin/ai', {
                method: 'PUT',
                body: JSON.stringify({ provider: providerSelect.value, model: modelInput.value.trim() })
            });
            currentConfig.ai = ai;
            testedModelKey = '';
            renderProviderOptions(ai);
            const health = await adminRequest('/api/admin/health');
            updateSummary(currentConfig, health);
            setMessage(aiMessage, 'Active provider and model saved. New AI requests will use this setting.', 'success');
        } catch (error) {
            setMessage(aiMessage, error.message);
        } finally {
            updateProviderStatus();
        }
    });

    rollbackProviderButton.addEventListener('click', async () => {
        if (!currentConfig?.ai.can_rollback) return;
        rollbackProviderButton.disabled = true;
        setMessage(aiMessage, 'Restoring the previous provider/model…', 'info');
        try {
            const ai = await adminRequest('/api/admin/ai/rollback', { method: 'POST' });
            currentConfig.ai = ai;
            testedModelKey = '';
            renderProviderOptions(ai);
            const health = await adminRequest('/api/admin/health');
            updateSummary(currentConfig, health);
            setMessage(aiMessage, 'Previous provider/model restored.', 'success');
        } catch (error) {
            setMessage(aiMessage, error.message);
        } finally {
            updateProviderStatus();
        }
    });

    document.getElementById('saveCoursesButton').addEventListener('click', async event => {
        const button = event.currentTarget;
        button.disabled = true;
        setMessage(courseMessage, '');
        try {
            const enabled_levels = Array.from(document.querySelectorAll('[data-level-toggle]:checked')).map(item => item.dataset.levelToggle);
            const enabled_units = {};
            Object.keys(currentConfig.courses.levels.reduce((map, level) => { map[level.level] = true; return map; }, {})).forEach(level => {
                enabled_units[level] = Array.from(document.querySelectorAll(`[data-unit-level="${CSS.escape(level)}"]:checked`)).map(item => item.dataset.unitId);
            });
            const courses = await adminRequest('/api/admin/courses', {
                method: 'PUT',
                body: JSON.stringify({ enabled_levels, enabled_units })
            });
            currentConfig.courses = courses;
            renderCourseCards(courses);
            updateSummary(currentConfig);
            setMessage(courseMessage, 'Course publication settings saved. Learner APIs now enforce these settings.', 'success');
        } catch (error) {
            setMessage(courseMessage, error.message);
        } finally {
            button.disabled = false;
        }
    });

    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(item => item.classList.toggle('active', item === tab));
            document.querySelectorAll('.panel-section').forEach(section => {
                const active = section.id === `section-${tab.dataset.section}`;
                section.classList.toggle('active', active);
                section.hidden = !active;
            });
        });
    });

    document.getElementById('logoutButton').addEventListener('click', async () => {
        try {
            await adminRequest('/api/admin/logout', { method: 'POST' });
        } catch (_) {
            // Always return to the login view, even if the session just expired.
        }
        csrfToken = '';
        showLogin('You have signed out.');
    });

    checkSession().catch(error => {
        setVisible(dashboardView, false);
        showLogin(error.message || 'Could not load the admin console.');
    });
})();
