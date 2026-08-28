document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements - Sidebar & Views
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
    const sidebarCloseBtn = document.getElementById('sidebar-close-btn');
    const newChatBtn = document.getElementById('new-chat-btn');
    const historyList = document.getElementById('history-list');
    const clearAllHistoryBtn = document.getElementById('clear-all-history-btn');
    const activeChatTitle = document.getElementById('active-chat-title');
    const sidebarLocationName = document.getElementById('sidebar-location-name');
    const sidebarLocationId = document.getElementById('sidebar-location-id');
    const sidebarConnectGhlBtn = document.getElementById('sidebar-connect-ghl');

    // Theme Toggle
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const savedTheme = localStorage.getItem('theme_preference') || 'light';
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
    } else {
        document.body.classList.remove('dark-theme');
    }

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            document.body.classList.toggle('dark-theme');
            const isDark = document.body.classList.contains('dark-theme');
            localStorage.setItem('theme_preference', isDark ? 'dark' : 'light');
        });
    }

    // DOM Elements - Usage Monitor Modal
    const usageModal = document.getElementById('usage-monitor-modal');
    const openUsageModalBtn = document.getElementById('open-usage-modal-btn');
    const sidebarUsageBtn = document.getElementById('sidebar-usage-btn');
    const closeUsageModalBtn = document.getElementById('close-usage-modal');
    const doneUsageModalBtn = document.getElementById('done-usage-modal');
    const usageModelsGrid = document.getElementById('usage-models-grid');
    const activeModelUsagePill = document.getElementById('active-model-usage-pill');

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

    // State Variables
    let ghlConfig = {
        locationId: localStorage.getItem('ghl_location_id') || '',
        accessToken: localStorage.getItem('ghl_access_token') || '',
        locationName: localStorage.getItem('ghl_location_name') || ''
    };

    let chatThreads = loadSavedThreads();
    let currentThreadId = localStorage.getItem('ghl_active_thread_id') || null;
    let cachedModelsData = [];

    // Configure Custom ChatGPT-Style Marked Renderer
    if (typeof marked !== 'undefined') {
        const renderer = new marked.Renderer();

        renderer.code = function (code, language) {
            const lang = (language || 'text').toLowerCase();
            const validLang = (typeof hljs !== 'undefined' && hljs.getLanguage(lang)) ? lang : '';
            const highlightedCode = validLang ? hljs.highlight(code, { language: validLang }).value : escapeHtml(code);
            const displayLang = (language || 'code').toUpperCase();

            return `
                <div class="code-block-wrapper">
                    <div class="code-block-header">
                        <span class="code-lang-tag">${escapeHtml(displayLang)}</span>
                        <button type="button" class="copy-code-btn" data-code="${escapeHtml(code)}">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                            <span>Copy code</span>
                        </button>
                    </div>
                    <pre><code class="hljs ${validLang}">${highlightedCode}</code></pre>
                </div>
            `;
        };

        marked.setOptions({
            renderer: renderer,
            breaks: true,
            gfm: true
        });
    }

    // Delegate copy button clicks
    document.addEventListener('click', (e) => {
        const copyBtn = e.target.closest('.copy-code-btn');
        if (!copyBtn) return;
        const code = copyBtn.getAttribute('data-code') || copyBtn.closest('.code-block-wrapper').querySelector('code').innerText;
        navigator.clipboard.writeText(code).then(() => {
            const textSpan = copyBtn.querySelector('span');
            if (textSpan) textSpan.textContent = 'Copied!';
            copyBtn.classList.add('copied');
            setTimeout(() => {
                if (textSpan) textSpan.textContent = 'Copy code';
                copyBtn.classList.remove('copied');
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy code:', err);
        });
    });

    updateGHLStatusUI();

    // Check initial connection
    if (ghlConfig.locationId && ghlConfig.accessToken) {
        verifyGhlConnection(ghlConfig.locationId, ghlConfig.accessToken, false);
    }

    // Load available models with live usage percentages
    fetchModelsCatalog();

    // Initialize Recent Chats & load active thread if any
    renderRecentChatsList();
    if (currentThreadId && getThreadById(currentThreadId)) {
        loadThread(currentThreadId);
    } else {
        createNewThread(false);
    }

    // ==========================================
    // CHAT THREADS & RECENT CHATS MANAGEMENT
    // ==========================================

    function loadSavedThreads() {
        try {
            return JSON.parse(localStorage.getItem('ghl_chat_threads') || '[]');
        } catch (e) {
            return [];
        }
    }

    function saveThreads() {
        try {
            localStorage.setItem('ghl_chat_threads', JSON.stringify(chatThreads));
        } catch (e) {
            console.warn('Failed to save threads:', e);
        }
    }

    function getThreadById(id) {
        return chatThreads.find(t => t.id === id);
    }

    function createNewThread(shouldFocus = true) {
        currentThreadId = 'thread_' + Date.now();
        localStorage.setItem('ghl_active_thread_id', currentThreadId);
        
        messagesList.innerHTML = '';
        if (welcomeScreen) welcomeScreen.classList.remove('hidden');
        if (activeChatTitle) activeChatTitle.textContent = 'Conversation AI Copilot';
        
        if (userInput) {
            userInput.value = '';
            userInput.style.height = 'auto';
            if (shouldFocus) userInput.focus();
        }
        renderRecentChatsList();
    }

    function loadThread(threadId) {
        const thread = getThreadById(threadId);
        if (!thread) return;

        currentThreadId = thread.id;
        localStorage.setItem('ghl_active_thread_id', currentThreadId);

        if (activeChatTitle) activeChatTitle.textContent = thread.title || 'Conversation AI Copilot';
        messagesList.innerHTML = '';

        if (!thread.messages || thread.messages.length === 0) {
            if (welcomeScreen) welcomeScreen.classList.remove('hidden');
        } else {
            if (welcomeScreen) welcomeScreen.classList.add('hidden');
            thread.messages.forEach(msg => {
                if (msg.role === 'user') {
                    appendMessageUI('user', msg.content);
                } else {
                    renderAssistantMessageUI(msg);
                }
            });
        }

        renderRecentChatsList();
        scrollToBottom();
        if (window.innerWidth <= 768) closeSidebar();
    }

    function addMessageToCurrentThread(role, content, toolBadges = []) {
        let thread = getThreadById(currentThreadId);
        if (!thread) {
            // Generate title from first message
            const title = content.length > 35 ? content.substring(0, 35) + '...' : content;
            thread = {
                id: currentThreadId || ('thread_' + Date.now()),
                title: title,
                createdAt: new Date().toISOString(),
                messages: []
            };
            chatThreads.unshift(thread);
            currentThreadId = thread.id;
            localStorage.setItem('ghl_active_thread_id', currentThreadId);
            if (activeChatTitle) activeChatTitle.textContent = title;
        }

        thread.messages.push({
            role: role,
            content: content,
            toolBadges: toolBadges,
            timestamp: new Date().toISOString()
        });

        saveThreads();
        renderRecentChatsList();
    }

    function deleteThread(threadId, event) {
        if (event) event.stopPropagation();
        chatThreads = chatThreads.filter(t => t.id !== threadId);
        saveThreads();

        if (currentThreadId === threadId) {
            if (chatThreads.length > 0) {
                loadThread(chatThreads[0].id);
            } else {
                createNewThread();
            }
        } else {
            renderRecentChatsList();
        }
    }

    function renderRecentChatsList() {
        if (!historyList) return;

        if (chatThreads.length === 0) {
            historyList.innerHTML = `
                <div class="history-empty-placeholder">
                    No recent chats yet.<br>Start a new conversation!
                </div>
            `;
            return;
        }

        historyList.innerHTML = chatThreads.map(thread => {
            const isActive = thread.id === currentThreadId;
            return `
                <button class="history-item ${isActive ? 'active' : ''}" data-thread-id="${escapeHtml(thread.id)}">
                    <div class="history-item-left">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
                        <span class="history-item-title">${escapeHtml(thread.title || 'Untitled Conversation')}</span>
                    </div>
                    <button class="delete-history-btn" data-delete-id="${escapeHtml(thread.id)}" title="Delete chat">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                    </button>
                </button>
            `;
        }).join('');

        // Attach click listeners to history items
        historyList.querySelectorAll('.history-item').forEach(item => {
            item.addEventListener('click', () => {
                const threadId = item.getAttribute('data-thread-id');
                loadThread(threadId);
            });
        });

        // Attach delete listeners
        historyList.querySelectorAll('.delete-history-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const threadId = btn.getAttribute('data-delete-id');
                deleteThread(threadId, e);
            });
        });
    }

    if (newChatBtn) {
        newChatBtn.addEventListener('click', () => createNewThread(true));
    }

    if (clearAllHistoryBtn) {
        clearAllHistoryBtn.addEventListener('click', () => {
            if (chatThreads.length === 0) return;
            if (confirm('Are you sure you want to clear all chat history?')) {
                chatThreads = [];
                saveThreads();
                createNewThread();
            }
        });
    }

    // ==========================================
    // MODELS CATALOG & USAGE MONITOR
    // ==========================================

    async function fetchModelsCatalog() {
        if (!modelSelector) return;
        try {
            const resp = await fetch('/api/models');
            if (!resp.ok) return;
            const data = await resp.json();
            const models = data.models || [];
            cachedModelsData = models;
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
                    const usagePct = (m.usage && m.usage.usage_percentage !== undefined) ? m.usage.usage_percentage : 0;
                    opt.textContent = `${m.name} (${usagePct}% Used • ${m.badge})`;
                    if (m.id === savedModel) {
                        opt.selected = true;
                    }
                    optGroup.appendChild(opt);
                });
                modelSelector.appendChild(optGroup);
            }

            updateActiveModelUsageDisplay();

            modelSelector.addEventListener('change', () => {
                localStorage.setItem('selected_ai_model', modelSelector.value);
                updateActiveModelUsageDisplay();
            });
        } catch (e) {
            console.error('Failed to load models catalog:', e);
        }
    }

    function updateActiveModelUsageDisplay() {
        if (!modelSelector || !activeModelUsagePill || cachedModelsData.length === 0) return;
        const currentModelId = modelSelector.value;
        const currentModel = cachedModelsData.find(m => m.id === currentModelId);
        if (currentModel && currentModel.usage) {
            const usagePct = currentModel.usage.usage_percentage || 0;
            const remainingPct = currentModel.usage.remaining_percentage || 100;
            activeModelUsagePill.textContent = `${currentModel.name.split(' ')[0]}: ${usagePct}% Used (${remainingPct}% Left)`;
        }
    }

    // Usage Modal Handlers
    if (openUsageModalBtn) openUsageModalBtn.addEventListener('click', openUsageModal);
    if (sidebarUsageBtn) sidebarUsageBtn.addEventListener('click', openUsageModal);
    if (closeUsageModalBtn) closeUsageModalBtn.addEventListener('click', closeUsageModal);
    if (doneUsageModalBtn) doneUsageModalBtn.addEventListener('click', closeUsageModal);

    async function openUsageModal() {
        await fetchModelsCatalog();
        renderUsageModalGrid();
        if (usageModal) usageModal.classList.remove('hidden');
    }

    function closeUsageModal() {
        if (usageModal) usageModal.classList.add('hidden');
    }

    function renderUsageModalGrid() {
        if (!usageModelsGrid) return;
        const currentModelId = modelSelector ? modelSelector.value : '';
        usageModelsGrid.innerHTML = cachedModelsData.map(m => {
            const usage = m.usage || { usage_percentage: 0, remaining_percentage: 100, daily_requests: 0, daily_limit: 100, daily_tokens: 0, status: 'Healthy' };
            const isActive = m.id === currentModelId;
            const usagePct = usage.usage_percentage || 0;
            const barColor = usagePct < 60 ? '#10b981' : (usagePct < 85 ? '#f59e0b' : '#ef4444');

            return `
                <div class="usage-model-card ${isActive ? 'active-model' : ''}">
                    <div class="usage-card-top">
                        <div class="usage-model-info">
                            <h4>${escapeHtml(m.name)}</h4>
                            <span class="usage-model-cat">${escapeHtml(m.category)} • <strong>${escapeHtml(m.badge)}</strong></span>
                        </div>
                        <span class="badge" style="background-color: ${barColor}22; color: ${barColor}; border: 1px solid ${barColor}55;">
                            ${usagePct}% Used
                        </span>
                    </div>

                    <div class="usage-progress-container">
                        <div class="usage-progress-bar-bg">
                            <div class="usage-progress-bar-fill" style="width: ${Math.max(2, usagePct)}%; background-color: ${barColor};"></div>
                        </div>
                        <div class="usage-stats-meta">
                            <span>Reqs: ${usage.daily_requests || 0} / ${usage.daily_limit || 200}</span>
                            <span>Remaining: ${usage.remaining_percentage || 100}%</span>
                        </div>
                    </div>

                    <div class="usage-card-actions">
                        <span style="font-size: 11px; color: var(--text-muted);">Est. Tokens: ${usage.daily_tokens || 0}</span>
                        <button type="button" class="select-model-btn ${isActive ? 'active' : ''}" data-model-id="${escapeHtml(m.id)}">
                            ${isActive ? '✓ Active Model' : 'Switch Model'}
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        const switchBtns = usageModelsGrid.querySelectorAll('.select-model-btn');
        switchBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const targetModelId = btn.getAttribute('data-model-id');
                if (targetModelId && modelSelector) {
                    modelSelector.value = targetModelId;
                    localStorage.setItem('selected_ai_model', targetModelId);
                    updateActiveModelUsageDisplay();
                    renderUsageModalGrid();
                    setTimeout(closeUsageModal, 300);
                }
            });
        });
    }

    // ==========================================
    // SIDEBAR & MODAL HANDLERS
    // ==========================================

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

    // GHL Modal Events
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

                ghlModalSuccess.textContent = `Connected to GHL Sub-Account: ${ghlConfig.locationName}`;
                ghlModalSuccess.classList.remove('hidden');
                updateGHLStatusUI();
                setTimeout(closeGhlModal, 1200);
            } else {
                ghlModalError.textContent = `${res.message}`;
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
        } else {
            ghlStatusPill.className = 'ghl-status-pill disconnected';
            ghlStatusLabel.textContent = 'Disconnected';
            sidebarLocationName.textContent = 'No Sub-Account';
            sidebarLocationId.textContent = 'Connect location to execute actions';
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

    // ==========================================
    // CHAT EXECUTION & PROMPT HANDLING
    // ==========================================

    if (userInput) {
        userInput.addEventListener('input', () => {
            userInput.style.height = 'auto';
            userInput.style.height = Math.min(userInput.scrollHeight, 180) + 'px';
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
                userInput.style.height = Math.min(userInput.scrollHeight, 180) + 'px';
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

        appendMessageUI('user', prompt);
        addMessageToCurrentThread('user', prompt);

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

        let accumulatedText = '';
        let recordedBadges = [];

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
                const errMsg = `⚠️ **Error (${response.status}):** ${errData.detail || 'Execution failed.'}`;
                botBodyEl.innerHTML = marked.parse(errMsg);
                addMessageToCurrentThread('assistant', errMsg);
                return;
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n\n');
                buffer = lines.pop() || '';

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
                                recordedBadges.push({ type: 'tool_start', text: toolBadge.innerHTML });
                                scrollToBottom();
                            } else if (data.type === 'tool_result') {
                                const resultBadge = document.createElement('div');
                                const isSuccess = data.result && data.result.success !== false;
                                resultBadge.className = isSuccess ? 'tool-execution-badge success' : 'tool-execution-badge error';
                                const errMsg = data.result.error || data.result.message || 'Action failed';
                                const isAuthErr = !isSuccess && (errMsg.includes('Location ID') || errMsg.includes('Token') || errMsg.includes('401') || errMsg.includes('404'));
                                
                                resultBadge.innerHTML = isSuccess ? 
                                    `✅ Action Executed: ${data.result.message || 'Asset Created'}` : 
                                    `❌ Action Failed: ${errMsg} ${isAuthErr ? '<button type="button" class="connect-ghl-btn inline-connect-trigger" style="margin-left: 10px; font-size: 11px; padding: 3px 10px;">Connect Location</button>' : ''}`;
                                
                                botBodyEl.appendChild(resultBadge);
                                recordedBadges.push({ type: 'tool_result', text: resultBadge.innerHTML, isSuccess: isSuccess });
                                
                                const inlineTrigger = resultBadge.querySelector('.inline-connect-trigger');
                                if (inlineTrigger) {
                                    inlineTrigger.addEventListener('click', openGhlModal);
                                }
                                scrollToBottom();
                            } else if (data.type === 'chunk') {
                                accumulatedText += data.text || '';
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

            if (accumulatedText) {
                addMessageToCurrentThread('assistant', accumulatedText, recordedBadges);
            }
            fetchModelsCatalog();
        } catch (err) {
            if (loadingIndicator) loadingIndicator.classList.add('hidden');
            const errStr = `⚠️ **Connection Error:** ${err.message}`;
            botBodyEl.innerHTML = marked.parse(errStr);
            addMessageToCurrentThread('assistant', errStr);
        }
        scrollToBottom();
    }

    function appendMessageUI(role, content) {
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

    function renderAssistantMessageUI(msg) {
        const msgWrap = document.createElement('div');
        msgWrap.className = 'message-wrapper assistant';
        let badgesHtml = '';
        if (msg.toolBadges && msg.toolBadges.length > 0) {
            badgesHtml = msg.toolBadges.map(b => `
                <div class="tool-execution-badge ${b.isSuccess === false ? 'error' : (b.isSuccess === true ? 'success' : '')}">${b.text}</div>
            `).join('');
        }

        const parsedContent = typeof marked !== 'undefined' ? marked.parse(msg.content || '') : escapeHtml(msg.content);
        msgWrap.innerHTML = `
            <div class="assistant-avatar">⚡</div>
            <div class="assistant-body">
                ${badgesHtml}
                <div class="agent-markdown-text">${parsedContent}</div>
            </div>
        `;
        messagesList.appendChild(msgWrap);
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
});
