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
    marked.setOptions({
        highlight: function (code, lang) {
            if (lang && hljs.getLanguage(lang)) {
                return hljs.highlight(code, { language: lang }).value;
            }
            return hljs.highlightAuto(code).value;
        },
        breaks: true
    });

    updateGHLStatusUI();

    // Check & verify initial saved connection
    if (ghlConfig.locationId && ghlConfig.accessToken) {
        verifyGhlConnection(ghlConfig.locationId, ghlConfig.accessToken, false);
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

    async function verifyGhlConnection(locId, token, isTesting) {
        try {
            const response = await fetch('/api/ghl/verify-token', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ location_id: locId, access_token: token })
            });
            const data = await response.json();
            if (data.success && !isTesting) {
                ghlConfig.locationName = data.location_name || 'Sub-Account';
                localStorage.setItem('ghl_location_name', ghlConfig.locationName);
                updateGHLStatusUI();
            }
            return data;
        } catch (err) {
            return { success: false, message: err.message };
        }
    }

    function updateGHLStatusUI() {
        if (ghlConfig.locationId && ghlConfig.accessToken) {
            ghlStatusPill.className = 'ghl-status-pill connected';
            ghlStatusLabel.textContent = `Connected: ${ghlConfig.locationName || 'Sub-Account'}`;
            openGhlModalBtn.textContent = 'Manage Location';
            sidebarLocationName.textContent = ghlConfig.locationName || 'Connected Location';
            sidebarLocationId.textContent = `ID: ${ghlConfig.locationId}`;
        } else {
            ghlStatusPill.className = 'ghl-status-pill disconnected';
            ghlStatusLabel.textContent = 'No Sub-Account Connected';
            openGhlModalBtn.textContent = 'Connect Location';
            sidebarLocationName.textContent = 'No Location Connected';
            sidebarLocationId.textContent = 'Set Token & Location ID';
        }
    }

    // Textarea Auto-Resize & Send Button Enable/Disable
    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = Math.min(userInput.scrollHeight, 160) + 'px';
        sendBtn.disabled = userInput.value.trim() === '';
    });

    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (userInput.value.trim() !== '') handleSendPrompt();
        }
    });

    sendBtn.addEventListener('click', handleSendPrompt);

    cardItems.forEach(card => {
        card.addEventListener('click', () => {
            const query = card.getAttribute('data-query');
            if (query) {
                userInput.value = query;
                userInput.style.height = 'auto';
                sendBtn.disabled = false;
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
                sendBtn.disabled = false;
            }
        });
    });

    async function handleSendPrompt() {
        const prompt = userInput.value.trim();
        if (!prompt) return;

        userInput.value = '';
        userInput.style.height = 'auto';
        sendBtn.disabled = true;

        if (welcomeScreen) welcomeScreen.classList.add('hidden');

        appendMessage('user', prompt);
        loadingIndicator.classList.remove('hidden');
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
                    selected_model: modelSelector ? modelSelector.value : 'gemini-2.0-flash'
                })
            });

            loadingIndicator.classList.add('hidden');

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
                                toolBadge.innerHTML = `⚡ Invoking GHL API: <strong>${data.name}</strong> (${JSON.stringify(data.args)})`;
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
            loadingIndicator.classList.add('hidden');
            botBodyEl.innerHTML = marked.parse(`⚠️ **Connection Error:** ${err.message}`);
        }
        if (accumulatedText) {
            saveMessageToCurrentThread('assistant', accumulatedText);
        }
        scrollToBottom();
    }

    // Fetch Live Contacts Data
    async function fetchContactsData() {
        if (!ghlConfig.locationId || !ghlConfig.accessToken) return;
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
        if (!ghlConfig.locationId || !ghlConfig.accessToken) return;
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
                    pipelineKanbanContainer.innerHTML = pipelines.map(p => `
                        <div class="dict-card" style="width: 100%; max-width: 600px;">
                            <h3>📊 Pipeline: ${escapeHtml(p.name)}</h3>
                            <p class="dict-subtext">ID: <code>${escapeHtml(p.id)}</code></p>
                            <div class="tags-cloud">
                                ${(p.stages || []).map(s => `<span class="tag-chip" style="background: rgba(255,255,255,0.06); color: var(--text-primary); border-color: var(--border-color);">${escapeHtml(s.name)}</span>`).join('')}
                            </div>
                        </div>
                    `).join('');
                }
            }
        } catch (e) {
            console.warn('Fetch pipelines warning:', e);
        }
    }

    // Fetch Live Tags & Custom Fields
    async function fetchTagsAndFieldsData() {
        if (!ghlConfig.locationId || !ghlConfig.accessToken) return;
        const dictTagsCloud = document.getElementById('dict-tags-cloud');
        const dictFieldsList = document.getElementById('dict-fields-list');

        try {
            const [tagsRes, fieldsRes] = await Promise.all([
                fetch('/api/ghl/tags', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ location_id: ghlConfig.locationId, access_token: ghlConfig.accessToken })
                }).then(r => r.json()).catch(() => null),
                fetch('/api/ghl/custom-fields', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ location_id: ghlConfig.locationId, access_token: ghlConfig.accessToken })
                }).then(r => r.json()).catch(() => null)
            ]);

            if (tagsRes && tagsRes.success && tagsRes.data && tagsRes.data.tags && dictTagsCloud) {
                dictTagsCloud.innerHTML = tagsRes.data.tags.map(t => `<span class="tag-chip">${escapeHtml(t.name)}</span>`).join('');
            }
            if (fieldsRes && fieldsRes.success && fieldsRes.data && fieldsRes.data.customFields && dictFieldsList) {
                dictFieldsList.innerHTML = fieldsRes.data.customFields.map(f => `
                    <div class="field-item">
                        <span>${escapeHtml(f.name)}</span>
                        <span class="badge">${escapeHtml(f.dataType || 'TEXT')}</span>
                    </div>
                `).join('');
            }
        } catch (e) {
            console.warn('Fetch tags/fields warning:', e);
        }
    }

    // Contact Creation Modal Handlers
    const quickCreateContactBtn = document.getElementById('quick-create-contact-btn');
    const createContactModal = document.getElementById('create-contact-modal');
    const closeContactModalBtn = document.getElementById('close-contact-modal');
    const cancelContactModalBtn = document.getElementById('cancel-contact-modal');
    const saveContactModalBtn = document.getElementById('save-contact-modal');
    const contactFirstName = document.getElementById('contact-first-name');
    const contactLastName = document.getElementById('contact-last-name');
    const contactEmail = document.getElementById('contact-email');
    const contactPhone = document.getElementById('contact-phone');
    const contactTag = document.getElementById('contact-tag');
    const contactModalError = document.getElementById('contact-modal-error');
    const contactModalSuccess = document.getElementById('contact-modal-success');

    if (quickCreateContactBtn) {
        quickCreateContactBtn.addEventListener('click', () => {
            if (!ghlConfig.locationId || !ghlConfig.accessToken) {
                openGhlModal();
                return;
            }
            createContactModal.classList.remove('hidden');
        });
    }
    if (closeContactModalBtn) closeContactModalBtn.addEventListener('click', () => createContactModal.classList.add('hidden'));
    if (cancelContactModalBtn) cancelContactModalBtn.addEventListener('click', () => createContactModal.classList.add('hidden'));

    if (saveContactModalBtn) {
        saveContactModalBtn.addEventListener('click', async () => {
            const fname = contactFirstName.value.trim();
            if (!fname) {
                contactModalError.textContent = 'First name is required.';
                contactModalError.classList.remove('hidden');
                return;
            }

            contactModalError.classList.add('hidden');
            contactModalSuccess.classList.add('hidden');
            setBtnLoading(saveContactModalBtn, true);

            try {
                const res = await fetch('/api/ghl/create-contact', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        location_id: ghlConfig.locationId,
                        access_token: ghlConfig.accessToken,
                        first_name: fname,
                        last_name: contactLastName.value.trim(),
                        email: contactEmail.value.trim(),
                        phone: contactPhone.value.trim(),
                        tag: contactTag.value.trim()
                    })
                });
                const data = await res.json();
                setBtnLoading(saveContactModalBtn, false);

                if (data.success) {
                    contactModalSuccess.textContent = `✅ ${data.message || 'Contact created!'}`;
                    contactModalSuccess.classList.remove('hidden');
                    fetchContactsData();
                    setTimeout(() => createContactModal.classList.add('hidden'), 1200);
                } else {
                    contactModalError.textContent = `❌ ${data.error || 'Failed to create contact'}`;
                    contactModalError.classList.remove('hidden');
                }
            } catch (err) {
                setBtnLoading(saveContactModalBtn, false);
                contactModalError.textContent = `❌ ${err.message}`;
                contactModalError.classList.remove('hidden');
            }
        });
    }

    // Persistent Chat History Management (localStorage)
    const newChatBtn = document.getElementById('new-chat-btn');
    const historyList = document.getElementById('history-list');
    let currentThreadId = localStorage.getItem('ghl_current_thread_id') || ('thread_' + Date.now());

    function getStoredThreads() {
        try {
            return JSON.parse(localStorage.getItem('ghl_chat_threads')) || [];
        } catch (e) {
            return [];
        }
    }

    function saveThreads(threads) {
        localStorage.setItem('ghl_chat_threads', JSON.stringify(threads));
    }

    function renderHistorySidebar() {
        if (!historyList) return;
        const threads = getStoredThreads();
        historyList.innerHTML = '';

        if (threads.length === 0) {
            historyList.innerHTML = `<div style="font-size: 11.5px; color: var(--text-muted); padding: 4px 8px;">No past chats saved</div>`;
            return;
        }

        threads.slice(0, 15).forEach(thread => {
            const item = document.createElement('div');
            item.className = `history-item ${thread.id === currentThreadId ? 'active' : ''}`;
            item.innerHTML = `
                <span class="history-title" title="${escapeHtml(thread.title)}">💬 ${escapeHtml(thread.title)}</span>
                <button type="button" class="history-delete-btn" title="Delete chat">✕</button>
            `;

            item.addEventListener('click', (e) => {
                if (e.target.classList.contains('history-delete-btn')) {
                    e.stopPropagation();
                    deleteThread(thread.id);
                } else {
                    loadThread(thread.id);
                }
            });

            historyList.appendChild(item);
        });
    }

    function createNewChatThread() {
        currentThreadId = 'thread_' + Date.now();
        localStorage.setItem('ghl_current_thread_id', currentThreadId);
        messagesList.innerHTML = '';
        if (welcomeScreen) welcomeScreen.classList.remove('hidden');
        renderHistorySidebar();
    }

    function loadThread(threadId) {
        const threads = getStoredThreads();
        const target = threads.find(t => t.id === threadId);
        if (!target) return;

        currentThreadId = threadId;
        localStorage.setItem('ghl_current_thread_id', threadId);
        messagesList.innerHTML = '';

        if (welcomeScreen) welcomeScreen.classList.add('hidden');

        target.messages.forEach(msg => {
            if (msg.role === 'user') {
                appendMessage('user', msg.text, false);
            } else if (msg.role === 'assistant') {
                const wrap = document.createElement('div');
                wrap.className = 'message-wrapper assistant';
                wrap.innerHTML = `
                    <div class="assistant-avatar">⚡</div>
                    <div class="assistant-body"><div class="agent-markdown-text">${marked.parse(msg.text)}</div></div>
                `;
                messagesList.appendChild(wrap);
            }
        });

        renderHistorySidebar();
        scrollToBottom();
    }

    function saveMessageToCurrentThread(role, text) {
        const threads = getStoredThreads();
        let thread = threads.find(t => t.id === currentThreadId);

        if (!thread) {
            thread = {
                id: currentThreadId,
                title: text.substring(0, 30) + (text.length > 30 ? '...' : ''),
                timestamp: Date.now(),
                messages: []
            };
            threads.unshift(thread);
        }

        thread.messages.push({ role, text });
        thread.timestamp = Date.now();
        saveThreads(threads);
        renderHistorySidebar();
    }

    function deleteThread(threadId) {
        let threads = getStoredThreads();
        threads = threads.filter(t => t.id !== threadId);
        saveThreads(threads);
        if (currentThreadId === threadId) {
            createNewChatThread();
        } else {
            renderHistorySidebar();
        }
    }

    if (newChatBtn) {
        newChatBtn.addEventListener('click', createNewChatThread);
    }

    renderHistorySidebar();
    if (getStoredThreads().find(t => t.id === currentThreadId)) {
        loadThread(currentThreadId);
    }

    function appendMessage(role, text, save = true) {
        const wrap = document.createElement('div');
        wrap.className = `message-wrapper ${role}`;
        if (role === 'user') {
            wrap.innerHTML = `<div class="user-bubble">${escapeHtml(text)}</div>`;
        }
        messagesList.appendChild(wrap);
        if (save) saveMessageToCurrentThread(role, text);
        scrollToBottom();
    }

    function scrollToBottom() {
        setTimeout(() => {
            if (chatContainer) {
                chatContainer.scrollTo({
                    top: chatContainer.scrollHeight + 500,
                    behavior: 'smooth'
                });
            }
        }, 60);
    }

    function setBtnLoading(btn, isLoading) {
        if (!btn) return;
        const txt = btn.querySelector('.btn-text');
        const spinner = btn.querySelector('.btn-spinner');
        if (isLoading) {
            if (txt) txt.style.opacity = '0.5';
            if (spinner) spinner.classList.remove('hidden');
            btn.disabled = true;
        } else {
            if (txt) txt.style.opacity = '1';
            if (spinner) spinner.classList.add('hidden');
            btn.disabled = false;
        }
    }

    function escapeHtml(str) {
        return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    }
});
