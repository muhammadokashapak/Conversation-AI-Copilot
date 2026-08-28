document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements - Sidebar & Views
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
    const sidebarCloseBtn = document.getElementById('sidebar-close-btn');
    const navItems = document.querySelectorAll('.sidebar-nav .nav-item[data-view]');
    const appViews = document.querySelectorAll('.app-view');
    const activeViewTitle = document.getElementById('active-view-title');
    const sidebarLocationName = document.getElementById('sidebar-location-name');
    const sidebarLocationId = document.getElementById('sidebar-location-id');
    const sidebarConnectGhlBtn = document.getElementById('sidebar-connect-ghl');

    // DOM Elements - GHL Connection Modal
    const ghlStatusPill = document.getElementById('ghl-status-pill');
    const ghlStatusLabel = document.getElementById('ghl-status-label');
    const openGhlModalBtn = document.getElementById('open-ghl-modal-btn');
    const ghlModal = document.getElementById('ghl-modal');
    const closeGhlModalBtn = document.getElementById('close-ghl-modal');
    const cancelGhlModalBtn = document.getElementById('cancel-ghl-modal');
    const saveGhlModalBtn = document.getElementById('save-ghl-modal');
    const ghlLocationIdInput = document.getElementById('ghl-location-id');
    const ghlAccessTokenInput = document.getElementById('ghl-access-token');
    const ghlModalError = document.getElementById('ghl-modal-error');
    const ghlModalSuccess = document.getElementById('ghl-modal-success');

    // DOM Elements - Chat & Actions
    const welcomeScreen = document.getElementById('welcome-screen');
    const messagesList = document.getElementById('messages-list');
    const chatContainer = document.getElementById('chat-container');
    const loadingIndicator = document.getElementById('loading-indicator');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const modelSelector = document.getElementById('model-selector');
    const cardItems = document.querySelectorAll('.card-item');
    const chipBtns = document.querySelectorAll('.chip-btn');

    // DOM Elements - Data Views
    const contactsTableBody = document.getElementById('contacts-table-body');
    const pipelineKanbanContainer = document.getElementById('pipeline-kanban-container');

    let ghlConfig = {
        locationId: localStorage.getItem('ghl_location_id') || '',
        accessToken: localStorage.getItem('ghl_access_token') || '',
        locationName: localStorage.getItem('ghl_location_name') || ''
    };

    // Configure Marked Markdown Renderer
    if (typeof marked !== 'undefined') {
        marked.setOptions({
            highlight: function (code, lang) {
                if (lang && typeof hljs !== 'undefined' && hljs.getLanguage(lang)) {
                    return hljs.highlight(code, { language: lang }).value;
                }
                return typeof hljs !== 'undefined' ? hljs.highlightAuto(code).value : code;
            },
            breaks: true
        });
    }

    updateGHLStatusUI();

    // Check & verify initial saved connection
    if (ghlConfig.locationId && ghlConfig.accessToken) {
        verifyGhlConnection(ghlConfig.locationId, ghlConfig.accessToken, false);
    }

    // Load available AI models into dropdown
    fetchModelsCatalog();

    // Fetch and populate AI models from backend catalog
    async function fetchModelsCatalog() {
        if (!modelSelector) return;
        try {
            const resp = await fetch('/api/models');
            if (!resp.ok) return;
            const data = await resp.json();
            const models = data.models || [];
            if (models.length === 0) return;

            const categories = {};
            models.forEach(m => {
                const cat = m.category || 'Other Models';
                if (!categories[cat]) categories[cat] = [];
                categories[cat].push(m);
            });

            const savedModel = localStorage.getItem('selected_ai_model') || data.default_model || 'gemini-3.6-flash';
            modelSelector.innerHTML = '';

            const iconsMap = {
                'Google Gemini': '✨',
                'Groq Ultra-Fast': '⚡',
                'xAI Grok & DeepSeek': '🧠',
                'Free Tier Models': '🎁',
                'Flagship Models': '👑'
            };

            for (const [catName, catModels] of Object.entries(categories)) {
                const optGroup = document.createElement('optgroup');
                optGroup.label = `${iconsMap[catName] || '🔹'} ${catName}`;
                catModels.forEach(m => {
                    const opt = document.createElement('option');
                    opt.value = m.id;
                    opt.textContent = `${m.name} [${m.badge}]`;
                    if (m.id === savedModel) {
                        opt.selected = true;
                    }
                    optGroup.appendChild(opt);
                });
                modelSelector.appendChild(optGroup);
            }

            modelSelector.addEventListener('change', () => {
                localStorage.setItem('selected_ai_model', modelSelector.value);
            });
        } catch (e) {
            console.error('Failed to load models catalog:', e);
        }
    }

    // Sidebar View Navigation
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const viewId = item.getAttribute('data-view');
            navItems.forEach(n => n.classList.remove('active'));
            item.classList.add('active');

            appViews.forEach(v => {
                if (v.id === viewId) {
                    v.classList.remove('hidden');
                } else {
                    v.classList.add('hidden');
                }
            });

            if (viewId === 'view-chat') activeViewTitle.textContent = 'Conversation AI Copilot';
            else if (viewId === 'view-contacts') {
                activeViewTitle.textContent = 'Contacts & CRM Hub';
                fetchContactsData();
            } else if (viewId === 'view-pipelines') {
                activeViewTitle.textContent = 'Pipelines & Sales Deals';
                fetchPipelinesData();
            } else if (viewId === 'view-tags') {
                activeViewTitle.textContent = 'Location Data Dictionary';
                fetchTagsAndFieldsData();
            }

            if (window.innerWidth <= 768) closeSidebar();
        });
    });

    // Sidebar Toggle
    if (sidebarToggleBtn) sidebarToggleBtn.addEventListener('click', toggleSidebar);
    if (sidebarCloseBtn) sidebarCloseBtn.addEventListener('click', closeSidebar);
    if (sidebarOverlay) sidebarOverlay.addEventListener('click', closeSidebar);

    function toggleSidebar() {
        if (sidebar.classList.contains('closed')) openSidebar();
        else closeSidebar();
    }

    function openSidebar() {
        sidebar.classList.remove('closed');
        if (window.innerWidth <= 768) sidebarOverlay.style.display = 'block';
    }

    function closeSidebar() {
        sidebar.classList.add('closed');
        sidebarOverlay.style.display = 'none';
    }

    // Modal Events
    if (openGhlModalBtn) openGhlModalBtn.addEventListener('click', openGhlModal);
    if (sidebarConnectGhlBtn) sidebarConnectGhlBtn.addEventListener('click', openGhlModal);
    if (closeGhlModalBtn) closeGhlModalBtn.addEventListener('click', closeGhlModal);
    if (cancelGhlModalBtn) cancelGhlModalBtn.addEventListener('click', closeGhlModal);

    function openGhlModal() {
        ghlLocationIdInput.value = ghlConfig.locationId;
        ghlAccessTokenInput.value = ghlConfig.accessToken;
        clearGhlModalAlerts();
        ghlModal.classList.remove('hidden');
    }

    function closeGhlModal() {
        ghlModal.classList.add('hidden');
    }

    function clearGhlModalAlerts() {
        ghlModalError.classList.add('hidden');
        ghlModalSuccess.classList.add('hidden');
        ghlModalError.textContent = '';
        ghlModalSuccess.textContent = '';
    }

    if (saveGhlModalBtn) {
        saveGhlModalBtn.addEventListener('click', async () => {
            const locId = ghlLocationIdInput.value.trim();
            const token = ghlAccessTokenInput.value.trim();

            if (!locId || !token) {
                ghlModalError.textContent = 'Please provide both Location ID and Access Token.';
                ghlModalError.classList.remove('hidden');
                return;
            }

            clearGhlModalAlerts();
            setBtnLoading(saveGhlModalBtn, true);

            const res = await verifyGhlConnection(locId, token, true);
            setBtnLoading(saveGhlModalBtn, false);

            if (res.success) {
                ghlConfig.locationId = locId;
                ghlConfig.accessToken = token;
                ghlConfig.locationName = res.location_name || 'Sub-Account';
                localStorage.setItem('ghl_location_id', locId);
                localStorage.setItem('ghl_access_token', token);
                localStorage.setItem('ghl_location_name', ghlConfig.locationName);

                ghlModalSuccess.textContent = `✅ Connected to GHL Sub-Account: ${ghlConfig.locationName}`;
                ghlModalSuccess.classList.remove('hidden');
                updateGHLStatusUI();
                setTimeout(closeGhlModal, 1500);
            } else {
                ghlModalError.textContent = `❌ ${res.message}`;
                ghlModalError.classList.remove('hidden');
            }
        });
    }

    async function verifyGhlConnection(locId, token, isTesting) {
        try {
            const response = await fetch('/api/ghl/verify-token', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ location_id: locId, access_token: token })
            });
            const data = await response.json();
            if (data.success) {
                ghlConfig.locationName = data.location_name || 'Sub-Account';
                updateGHLStatusUI(true);
            } else {
                if (!isTesting) updateGHLStatusUI(false);
            }
            return data;
        } catch (e) {
            return { success: false, message: 'Server connection error.' };
        }
    }

    function updateGHLStatusUI(isConnected) {
        const connected = isConnected !== undefined ? isConnected : Boolean(ghlConfig.locationId && ghlConfig.accessToken);
        if (connected) {
            ghlStatusPill.className = 'ghl-status-pill connected';
            ghlStatusLabel.textContent = ghlConfig.locationName || 'Connected';
            sidebarLocationName.textContent = ghlConfig.locationName || 'Connected Sub-Account';
            sidebarLocationId.textContent = `ID: ${ghlConfig.locationId}`;
            sidebarConnectGhlBtn.innerHTML = `<span>🟢 Connected</span>`;
        } else {
            ghlStatusPill.className = 'ghl-status-pill disconnected';
            ghlStatusLabel.textContent = 'Disconnected';
            sidebarLocationName.textContent = 'No Sub-Account';
            sidebarLocationId.textContent = 'Connect location to execute actions';
            sidebarConnectGhlBtn.innerHTML = `<span>⚡ Connect Sub-Account</span>`;
        }
    }

    function setBtnLoading(btn, isLoading) {
        if (!btn) return;
        if (isLoading) {
            btn.disabled = true;
            btn.setAttribute('data-original-text', btn.textContent);
            btn.textContent = 'Verifying...';
        } else {
            btn.disabled = false;
            btn.textContent = btn.getAttribute('data-original-text') || 'Save Connection';
        }
    }

    // Auto-expand chat textarea
    if (userInput) {
        userInput.addEventListener('input', () => {
            userInput.style.height = 'auto';
            userInput.style.height = Math.min(userInput.scrollHeight, 160) + 'px';
            if (sendBtn) sendBtn.disabled = userInput.value.trim().length === 0;
        });

        userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (userInput.value.trim().length > 0) {
                    handleSendPrompt();
                }
            }
        });
    }

    if (sendBtn) sendBtn.addEventListener('click', handleSendPrompt);

    // Starter Prompt Cards
    cardItems.forEach(card => {
        card.addEventListener('click', () => {
            const prompt = card.getAttribute('data-prompt');
            if (prompt) {
                userInput.value = prompt;
                userInput.style.height = 'auto';
                if (sendBtn) sendBtn.disabled = false;
                handleSendPrompt();
            }
        });
    });

    chipBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tmpl = btn.getAttribute('data-template');
            if (tmpl) {
                userInput.value = tmpl;
                userInput.focus();
                userInput.style.height = 'auto';
                userInput.style.height = Math.min(userInput.scrollHeight, 160) + 'px';
                if (sendBtn) sendBtn.disabled = false;
            }
        });
    });

    async function handleSendPrompt() {
        const prompt = userInput.value.trim();
        if (!prompt) return;

        userInput.value = '';
        userInput.style.height = 'auto';
        if (sendBtn) sendBtn.disabled = true;

        if (welcomeScreen) welcomeScreen.classList.add('hidden');

        appendMessage('user', prompt);
        if (loadingIndicator) loadingIndicator.classList.remove('hidden');
        scrollToBottom();

        const botMsgWrap = document.createElement('div');
        botMsgWrap.className = 'message-wrapper assistant';
        botMsgWrap.innerHTML = `
            <div class="assistant-avatar">⚡</div>
            <div class="assistant-body" id="current-bot-body"></div>
        `;
        messagesList.appendChild(botMsgWrap);
        const botBodyEl = botMsgWrap.querySelector('.assistant-body');

        let accumulatedText = "";

        try {
            const response = await fetch('/api/chat-agent', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: prompt,
                    location_id: ghlConfig.locationId,
                    access_token: ghlConfig.accessToken,
                    selected_model: modelSelector ? modelSelector.value : 'gemini-3.6-flash'
                })
            });

            if (loadingIndicator) loadingIndicator.classList.add('hidden');

            if (!response.ok) {
                const errData = await response.json().catch(() => ({ detail: response.statusText }));
                botBodyEl.innerHTML = marked.parse(`⚠️ **Error (${response.status}):** ${errData.detail || 'Execution failed.'}`);
                return;
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n\n');
                buffer = lines.pop() || "";

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const jsonStr = line.replace('data: ', '').trim();
                        if (!jsonStr) continue;
                        try {
                            const data = JSON.parse(jsonStr);

                            if (data.type === 'tool_start') {
                                const toolBadge = document.createElement('div');
                                toolBadge.className = 'tool-execution-badge';
                                toolBadge.innerHTML = `⚡ Invoking GHL API: <strong>${data.name}</strong> (${escapeHtml(JSON.stringify(data.args))})`;
                                botBodyEl.appendChild(toolBadge);
                                scrollToBottom();
                            } else if (data.type === 'tool_result') {
                                const resultBadge = document.createElement('div');
                                const isSuccess = data.result && data.result.success !== false;
                                resultBadge.className = isSuccess ? 'tool-execution-badge success' : 'tool-execution-badge error';
                                const errMsg = data.result.error || data.result.message || 'Action failed';
                                const isAuthErr = !isSuccess && (errMsg.includes('Location ID') || errMsg.includes('Token') || errMsg.includes('401') || errMsg.includes('404'));
                                
                                resultBadge.innerHTML = isSuccess ? 
                                    `✅ Action Executed: ${data.result.message || 'Asset Created'}` : 
                                    `❌ Action Failed: ${errMsg} ${isAuthErr ? '<button type="button" class="connect-ghl-btn inline-connect-trigger" style="margin-left: 10px; font-size: 11px; padding: 3px 10px;">⚡ Connect Location</button>' : ''}`;
                                
                                botBodyEl.appendChild(resultBadge);
                                
                                const inlineTrigger = resultBadge.querySelector('.inline-connect-trigger');
                                if (inlineTrigger) {
                                    inlineTrigger.addEventListener('click', openGhlModal);
                                }
                                scrollToBottom();
                            } else if (data.type === 'chunk') {
                                accumulatedText += data.text || "";
                                let textContainer = botBodyEl.querySelector('.agent-markdown-text');
                                if (!textContainer) {
                                    textContainer = document.createElement('div');
                                    textContainer.className = 'agent-markdown-text';
                                    botBodyEl.appendChild(textContainer);
                                }
                                textContainer.innerHTML = marked.parse(accumulatedText);
                                scrollToBottom();
                            }
                        } catch (e) {
                            console.warn('JSON parse error:', e);
                        }
                    }
                }
            }
        } catch (err) {
            if (loadingIndicator) loadingIndicator.classList.add('hidden');
            botBodyEl.innerHTML = marked.parse(`⚠️ **Connection Error:** ${err.message}`);
        }
        scrollToBottom();
    }

    function appendMessage(role, content) {
        const msgWrap = document.createElement('div');
        msgWrap.className = `message-wrapper ${role}`;
        if (role === 'user') {
            msgWrap.innerHTML = `
                <div class="user-body">${escapeHtml(content)}</div>
                <div class="user-avatar">👤</div>
            `;
        }
        messagesList.appendChild(msgWrap);
        scrollToBottom();
    }

    function scrollToBottom() {
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }

    function escapeHtml(text) {
        if (!text) return '';
        const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
        return String(text).replace(/[&<>"']/g, m => map[m]);
    }

    // Fetch Live Contacts Data
    async function fetchContactsData() {
        if (!ghlConfig.locationId || !ghlConfig.accessToken || !contactsTableBody) return;
        try {
            const res = await fetch('/api/ghl/contacts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ location_id: ghlConfig.locationId, access_token: ghlConfig.accessToken })
            });
            const data = await res.json();
            if (data.success && data.data && data.data.contacts) {
                const contacts = data.data.contacts;
                if (contacts.length > 0) {
                    contactsTableBody.innerHTML = contacts.map(c => `
                        <tr>
                            <td><strong>${escapeHtml((c.firstName || '') + ' ' + (c.lastName || ''))}</strong></td>
                            <td>${escapeHtml(c.email || 'N/A')}</td>
                            <td>${escapeHtml(c.phone || 'N/A')}</td>
                            <td>${(c.tags || []).map(t => `<span class="tag-chip">${escapeHtml(t)}</span>`).join(' ') || 'None'}</td>
                            <td><code>${escapeHtml(c.locationId || ghlConfig.locationId)}</code></td>
                        </tr>
                    `).join('');
                }
            }
        } catch (e) {
            console.warn('Fetch contacts warning:', e);
        }
    }

    // Fetch Live Pipelines Data
    async function fetchPipelinesData() {
        if (!ghlConfig.locationId || !ghlConfig.accessToken || !pipelineKanbanContainer) return;
        try {
            const res = await fetch('/api/ghl/pipelines', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ location_id: ghlConfig.locationId, access_token: ghlConfig.accessToken })
            });
            const data = await res.json();
            if (data.success && data.data && data.data.pipelines) {
                const pipelines = data.data.pipelines;
                if (pipelines.length > 0) {
                    const firstPipe = pipelines[0];
                    pipelineKanbanContainer.innerHTML = (firstPipe.stages || []).map(st => `
                        <div class="kanban-column">
                            <div class="column-header">
                                <h3>${escapeHtml(st.name)}</h3>
                                <span class="badge count">0</span>
                            </div>
                            <div class="kanban-cards-container">
                                <div class="empty-column-placeholder">No active opportunities</div>
                            </div>
                        </div>
                    `).join('');
                }
            }
        } catch (e) {
            console.warn('Fetch pipelines warning:', e);
        }
    }

    // Fetch Tags & Custom Fields
    async function fetchTagsAndFieldsData() {
        if (!ghlConfig.locationId || !ghlConfig.accessToken) return;
        const tagsPillContainer = document.getElementById('tags-pills-container');
        const fieldsListContainer = document.getElementById('custom-fields-list');

        try {
            const tagsRes = await fetch('/api/ghl/tags', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ location_id: ghlConfig.locationId, access_token: ghlConfig.accessToken })
            });
            const tagsData = await tagsRes.json();
            if (tagsData.success && tagsData.data && tagsPillContainer) {
                const tags = tagsData.data.tags || [];
                tagsPillContainer.innerHTML = tags.map(t => `<span class="tag-chip">${escapeHtml(t.name)}</span>`).join(' ') || '<p class="text-muted">No custom tags created yet.</p>';
            }

            const fieldsRes = await fetch('/api/ghl/custom-fields', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ location_id: ghlConfig.locationId, access_token: ghlConfig.accessToken })
            });
            const fieldsData = await fieldsRes.json();
            if (fieldsData.success && fieldsData.data && fieldsListContainer) {
                const fields = fieldsData.data.customFields || [];
                fieldsListContainer.innerHTML = fields.map(f => `
                    <div class="field-item-card">
                        <span class="field-name"><strong>${escapeHtml(f.name)}</strong></span>
                        <span class="field-type-badge">${escapeHtml(f.dataType || 'TEXT')}</span>
                    </div>
                `).join('') || '<p class="text-muted">No custom fields found.</p>';
            }
        } catch (e) {
            console.warn('Fetch tags & fields error:', e);
        }
    }
});
