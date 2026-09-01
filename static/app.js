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
    const savedTheme = localStorage.getItem('theme_preference') || 'dark';
    if (savedTheme === 'light') {
        document.body.classList.remove('dark-theme');
    } else {
        document.body.classList.add('dark-theme');
    }

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            document.body.classList.toggle('dark-theme');
            const isDark = document.body.classList.contains('dark-theme');
            localStorage.setItem('theme_preference', isDark ? 'dark' : 'light');
        });
    }

    // Sidebar Toggle & Overlay Logic
    function toggleSidebar() {
        if (!sidebar) return;
        if (sidebar.classList.contains('closed')) {
            openSidebar();
        } else {
            closeSidebar();
        }
    }

    function openSidebar() {
        if (!sidebar) return;
        sidebar.classList.remove('closed');
        if (sidebarOverlay) {
            if (window.innerWidth <= 768) {
                sidebarOverlay.classList.add('active');
                sidebarOverlay.classList.remove('hidden');
            }
        }
        localStorage.setItem('sidebar_closed', 'false');
    }

    function closeSidebar() {
        if (!sidebar) return;
        sidebar.classList.add('closed');
        if (sidebarOverlay) {
            sidebarOverlay.classList.remove('active');
            sidebarOverlay.classList.add('hidden');
        }
        localStorage.setItem('sidebar_closed', 'true');
    }

    if (sidebarToggleBtn) sidebarToggleBtn.addEventListener('click', toggleSidebar);
    if (sidebarCloseBtn) sidebarCloseBtn.addEventListener('click', closeSidebar);
    if (sidebarOverlay) sidebarOverlay.addEventListener('click', closeSidebar);


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
    // DOM Elements - Prompt Queue & Generation Controls
    const stopGeneratingBtn = document.getElementById('stop-generating-btn');
    const promptQueueContainer = document.getElementById('prompt-queue-container');
    const queueStatusText = document.getElementById('queue-status-text');
    const queueCancelBtn = document.getElementById('queue-cancel-btn');

    // State Variables
    let isGenerating = false;
    let promptQueue = []; // [{ prompt: string, elementId: string }]
    let currentAbortController = null;

    function updateQueueUI() {
        if (!promptQueueContainer) return;
        if (promptQueue.length === 0) {
            promptQueueContainer.classList.add('hidden');
        } else {
            promptQueueContainer.classList.remove('hidden');
            if (queueStatusText) {
                queueStatusText.textContent = `${promptQueue.length} prompt${promptQueue.length > 1 ? 's' : ''} queued (Auto-executing next)`;
            }
        }
    }

    function clearPromptQueue() {
        if (promptQueue && promptQueue.length > 0) {
            promptQueue.forEach(item => {
                const el = document.getElementById(item.elementId);
                if (el) el.remove();
            });
        }
        promptQueue = [];
        updateQueueUI();
    }

    function updateSendButtonState() {
        if (!sendBtn) return;
        if (isGenerating) {
            sendBtn.disabled = false;
            sendBtn.classList.add('generating-stop-mode');
            sendBtn.title = 'Stop Generating Response (or Esc)';
            sendBtn.innerHTML = `
                <span style="display:flex; align-items:center; gap:5px; color:#fff; font-weight:600; font-size:12px;">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><rect x="4" y="4" width="16" height="16" rx="2"></rect></svg>
                    <span>Stop</span>
                </span>
            `;
        } else {
            sendBtn.classList.remove('generating-stop-mode');
            sendBtn.title = 'Send Prompt';
            sendBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="22" y1="2" x2="11" y2="13"></line>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                </svg>
            `;
            const hasText = (userInput && userInput.value.trim().length > 0);
            const hasAttachments = (typeof pendingAttachments !== 'undefined' && pendingAttachments.length > 0);
            sendBtn.disabled = !hasText && !hasAttachments;
        }
    }

    function abortCurrentGeneration() {
        if (currentAbortController) {
            currentAbortController.abort();
            currentAbortController = null;
        }
        if (window._stopActiveStream) {
            window._stopActiveStream();
        }
        isGenerating = false;
        updateSendButtonState();
        if (loadingIndicator) loadingIndicator.classList.add('hidden');
    }

    if (stopGeneratingBtn) stopGeneratingBtn.addEventListener('click', abortCurrentGeneration);
    if (queueCancelBtn) queueCancelBtn.addEventListener('click', clearPromptQueue);

    const sidebarProfileCard = document.getElementById('sidebar-profile-card');
    const sidebarConnectGhl = sidebarConnectGhlBtn;


    let ghlConfig = {
        locationId: localStorage.getItem('ghl_location_id') || '',
        accessToken: localStorage.getItem('ghl_access_token') || '',
        locationName: localStorage.getItem('ghl_location_name') || ''
    };

    function updateGhlUI() {
        const isConnected = !!(ghlConfig.locationId && ghlConfig.accessToken);
        if (ghlStatusPill) {
            ghlStatusPill.className = `ghl-status-pill ${isConnected ? 'connected' : 'disconnected'}`;
        }
        if (ghlStatusLabel) {
            ghlStatusLabel.textContent = isConnected ? 'Connected' : 'Disconnected';
        }
        if (openGhlModalBtn) {
            openGhlModalBtn.textContent = isConnected ? (ghlConfig.locationName || 'Settings') : 'Connect Location';
        }
        if (sidebarLocationName) {
            sidebarLocationName.textContent = isConnected ? (ghlConfig.locationName || 'Connected Sub-Account') : 'No Sub-Account';
        }
        if (sidebarLocationId) {
            sidebarLocationId.textContent = isConnected ? (ghlConfig.locationId.substring(0, 14) + '...') : 'Click to Connect';
        }
    }

    function openGhlModal() {
        if (!ghlModal) return;
        if (ghlLocationIdInput) ghlLocationIdInput.value = ghlConfig.locationId || '';
        if (ghlAccessTokenInput) ghlAccessTokenInput.value = ghlConfig.accessToken || '';
        if (ghlModalError) ghlModalError.classList.add('hidden');
        if (ghlModalSuccess) ghlModalSuccess.classList.add('hidden');
        ghlModal.classList.remove('hidden');
    }

    function closeGhlModal() {
        if (ghlModal) ghlModal.classList.add('hidden');
    }

    async function handleSaveGhlCredentials() {
        const locId = ghlLocationIdInput ? ghlLocationIdInput.value.trim() : '';
        const token = ghlAccessTokenInput ? ghlAccessTokenInput.value.trim() : '';

        if (!locId || !token) {
            if (ghlModalError) {
                ghlModalError.textContent = 'Please enter both Location ID and API Key / Access Token.';
                ghlModalError.classList.remove('hidden');
            }
            return;
        }

        if (saveGhlModalBtn) {
            saveGhlModalBtn.disabled = true;
            saveGhlModalBtn.textContent = 'Verifying...';
        }

        try {
            const res = await fetch('/api/ghl/verify-token', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ location_id: locId, access_token: token })
            });
            const data = await res.json();

            if (res.ok && data.success) {
                ghlConfig.locationId = locId;
                ghlConfig.accessToken = token;
                ghlConfig.locationName = data.location_name || data.company_name || 'GHL Sub-Account';

                localStorage.setItem('ghl_location_id', ghlConfig.locationId);
                localStorage.setItem('ghl_access_token', ghlConfig.accessToken);
                localStorage.setItem('ghl_location_name', ghlConfig.locationName);

                if (ghlModalSuccess) {
                    ghlModalSuccess.textContent = `✓ Successfully connected to ${ghlConfig.locationName}!`;
                    ghlModalSuccess.classList.remove('hidden');
                }
                if (ghlModalError) ghlModalError.classList.add('hidden');

                updateGhlUI();
                setTimeout(closeGhlModal, 1200);
            } else {
                if (ghlModalError) {
                    ghlModalError.textContent = data.message || data.detail || 'Failed to verify GHL credentials. Please check token permissions.';
                    ghlModalError.classList.remove('hidden');
                }
                if (ghlModalSuccess) ghlModalSuccess.classList.add('hidden');
            }
        } catch (e) {
            if (ghlModalError) {
                ghlModalError.textContent = 'Network error verifying GHL connection: ' + e.message;
                ghlModalError.classList.remove('hidden');
            }
        } finally {
            if (saveGhlModalBtn) {
                saveGhlModalBtn.disabled = false;
                saveGhlModalBtn.textContent = 'Save & Connect';
            }
        }
    }

    if (openGhlModalBtn) openGhlModalBtn.addEventListener('click', openGhlModal);
    if (sidebarConnectGhl) sidebarConnectGhl.addEventListener('click', openGhlModal);
    if (sidebarProfileCard) sidebarProfileCard.addEventListener('click', openGhlModal);
    if (closeGhlModalBtn) closeGhlModalBtn.addEventListener('click', closeGhlModal);
    if (cancelGhlModalBtn) cancelGhlModalBtn.addEventListener('click', closeGhlModal);
    if (saveGhlModalBtn) saveGhlModalBtn.addEventListener('click', handleSaveGhlCredentials);

    // Initialize GHL UI state
    updateGhlUI();

    // =========================================================================
    // Multimodal Attachments & Web Speech API Voice Recognition
    // =========================================================================
    const attachFileBtn = document.getElementById('attach-file-btn');
    const fileAttachmentInput = document.getElementById('file-attachment-input');
    const voiceInputBtn = document.getElementById('voice-input-btn');
    const attachmentsPreview = document.getElementById('input-attachments-preview');

    let pendingAttachments = []; // [{ name, type, mime_type, data, size }]
    let speechRecognition = null;
    let isListeningVoice = false;

    function renderAttachmentPreviews() {
        if (!attachmentsPreview) return;
        if (pendingAttachments.length === 0) {
            attachmentsPreview.classList.add('hidden');
            attachmentsPreview.innerHTML = '';
            updateSendButtonState();
            return;
        }

        attachmentsPreview.classList.remove('hidden');
        attachmentsPreview.innerHTML = pendingAttachments.map((att, idx) => {
            const isImg = att.type === 'image' || (att.mime_type && att.mime_type.startsWith('image/'));
            const thumbHtml = isImg ? 
                `<img src="${att.data}" class="att-thumb" alt="${escapeHtml(att.name)}">` : 
                `<span class="att-icon">${getFileIcon(att.name)}</span>`;

            return `
                <div class="attachment-chip" data-idx="${idx}">
                    ${thumbHtml}
                    <span class="att-name" title="${escapeHtml(att.name)}">${escapeHtml(att.name)}</span>
                    <button type="button" class="att-remove-btn" data-idx="${idx}" title="Remove file">✕</button>
                </div>
            `;
        }).join('');

        attachmentsPreview.querySelectorAll('.att-remove-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const idx = parseInt(btn.getAttribute('data-idx'), 10);
                pendingAttachments.splice(idx, 1);
                renderAttachmentPreviews();
            });
        });

        updateSendButtonState();
    }

    function getFileIcon(filename) {
        const ext = (filename.split('.').pop() || '').toLowerCase();
        if (['png', 'jpg', 'jpeg', 'webp', 'gif', 'svg'].includes(ext)) return '🖼️';
        if (['pdf'].includes(ext)) return '📕';
        if (['csv', 'xlsx', 'xls'].includes(ext)) return '📊';
        if (['json', 'yaml', 'yml'].includes(ext)) return '⚙️';
        if (['html', 'htm'].includes(ext)) return '🌐';
        if (['css', 'scss'].includes(ext)) return '🎨';
        if (['js', 'ts', 'jsx', 'tsx', 'py'].includes(ext)) return '⚡';
        return '📄';
    }

    function handleFilesSelected(files) {
        if (!files || files.length === 0) return;

        Array.from(files).forEach(file => {
            const isImg = file.type.startsWith('image/');
            const reader = new FileReader();

            reader.onload = (e) => {
                const dataUrl = e.target.result;
                pendingAttachments.push({
                    name: file.name,
                    type: isImg ? 'image' : 'file',
                    mime_type: file.type || (isImg ? 'image/png' : 'text/plain'),
                    data: dataUrl,
                    size: file.size
                });
                renderAttachmentPreviews();
            };

            reader.readAsDataURL(file);
        });
    }

    if (attachFileBtn && fileAttachmentInput) {
        attachFileBtn.addEventListener('click', () => {
            fileAttachmentInput.click();
        });

        fileAttachmentInput.addEventListener('change', (e) => {
            handleFilesSelected(e.target.files);
            fileAttachmentInput.value = '';
        });
    }

    // Drag and drop onto input area
    const inputBoxWrapper = document.getElementById('input-box-wrapper');
    if (inputBoxWrapper) {
        inputBoxWrapper.addEventListener('dragover', (e) => {
            e.preventDefault();
            inputBoxWrapper.style.borderColor = 'var(--primary-color)';
        });
        inputBoxWrapper.addEventListener('dragleave', () => {
            inputBoxWrapper.style.borderColor = '';
        });
        inputBoxWrapper.addEventListener('drop', (e) => {
            e.preventDefault();
            inputBoxWrapper.style.borderColor = '';
            if (e.dataTransfer && e.dataTransfer.files) {
                handleFilesSelected(e.dataTransfer.files);
            }
        });
    }

    // Paste images from clipboard (Ctrl + V)
    if (userInput) {
        userInput.addEventListener('paste', (e) => {
            const items = (e.clipboardData || e.originalEvent.clipboardData)?.items;
            if (items) {
                for (let i = 0; i < items.length; i++) {
                    if (items[i].type.indexOf('image') !== -1) {
                        const blob = items[i].getAsFile();
                        if (blob) {
                            handleFilesSelected([blob]);
                        }
                    }
                }
            }
        });
    }

    // Web Speech API Voice Dictation
    function setupVoiceRecognition() {
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRec) {
            if (voiceInputBtn) {
                voiceInputBtn.title = 'Speech-to-Text not supported in this browser (Use Chrome or Edge)';
                voiceInputBtn.style.opacity = '0.5';
            }
            return;
        }

        speechRecognition = new SpeechRec();
        speechRecognition.continuous = true;
        speechRecognition.interimResults = true;
        speechRecognition.lang = 'en-US';

        speechRecognition.onstart = () => {
            isListeningVoice = true;
            if (voiceInputBtn) {
                voiceInputBtn.classList.add('recording');
                voiceInputBtn.title = 'Listening... Click to stop voice dictation';
            }
        };

        speechRecognition.onresult = (event) => {
            let transcript = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {
                transcript += event.results[i][0].transcript;
            }
            if (userInput && transcript) {
                const prev = userInput.value.trim();
                userInput.value = (prev ? prev + ' ' : '') + transcript;
                userInput.style.height = 'auto';
                userInput.style.height = Math.min(userInput.scrollHeight, 180) + 'px';
                updateSendButtonState();
            }
        };

        speechRecognition.onerror = (event) => {
            console.warn('Speech recognition error:', event.error);
            stopVoiceRecognition();
        };

        speechRecognition.onend = () => {
            stopVoiceRecognition();
        };

        if (voiceInputBtn) {
            voiceInputBtn.addEventListener('click', () => {
                if (isListeningVoice) {
                    speechRecognition.stop();
                } else {
                    try {
                        speechRecognition.start();
                    } catch (e) {
                        console.warn('Recognition already started:', e);
                    }
                }
            });
        }
    }

    function stopVoiceRecognition() {
        isListeningVoice = false;
        if (voiceInputBtn) {
            voiceInputBtn.classList.remove('recording');
            voiceInputBtn.title = 'Voice Dictation (Speech to Text)';
        }
    }

    setupVoiceRecognition();

    let chatThreads = loadSavedThreads();
    let currentThreadId = localStorage.getItem('ghl_active_thread_id') || null;
    let cachedModelsData = [];

    // Active artifacts storage for Claude-Style Side Drawer Code Studio
    window.activeArtifacts = {};

    function getArtifactMeta(lang, code) {
        const lowerCode = code.trim().toLowerCase();
        let filename = `code_snippet.${lang || 'txt'}`;
        let icon = '📄';
        let cleanLang = lang || 'text';

        if (cleanLang === 'html' || lowerCode.includes('<!doctype html') || lowerCode.includes('<html')) {
            filename = 'landing_page.html';
            icon = '🌐';
            cleanLang = 'html';
        } else if (cleanLang === 'css' || lowerCode.includes(':root {') || lowerCode.includes('body {')) {
            filename = 'styles.css';
            icon = '🎨';
            cleanLang = 'css';
        } else if (cleanLang === 'javascript' || cleanLang === 'js') {
            filename = 'script.js';
            icon = '⚡';
            cleanLang = 'javascript';
        } else if (cleanLang === 'json') {
            filename = 'ghl_schema.json';
            icon = '⚙️';
            cleanLang = 'json';
        } else if (cleanLang === 'python' || cleanLang === 'py') {
            filename = 'app.py';
            icon = '🐍';
            cleanLang = 'python';
        }

        const lines = code.trim().split('\n').length;
        return { filename, icon, lang: cleanLang, lines };
    }

    // Configure Custom Claude-Style Marked Renderer
    if (typeof marked !== 'undefined') {
        const renderer = new marked.Renderer();

        renderer.code = function (code, language) {
            const rawLang = (language || '').toLowerCase().trim();

            // Clean unclosed HTML leaks: If code contains </html>, strip everything after </html>
            let cleanCode = code;
            let trailingMarkdown = '';
            if ((rawLang === 'html' || code.includes('<html') || code.includes('<!DOCTYPE')) && code.includes('</html>')) {
                const endIdx = code.indexOf('</html>') + 7;
                cleanCode = code.substring(0, endIdx).trim();
                const rest = code.substring(endIdx).trim();
                if (rest && rest.length > 5) {
                    try {
                        trailingMarkdown = `<div class="agent-markdown-text" style="margin-top: 18px;">${marked.parse(rest)}</div>`;
                    } catch(e) {
                        trailingMarkdown = `<div class="agent-markdown-text" style="margin-top: 18px;">${escapeHtml(rest)}</div>`;
                    }
                }
            }

            const meta = getArtifactMeta(rawLang, cleanCode);
            const artifactId = 'art_' + Math.random().toString(36).substring(2, 9);
            
            window.activeArtifacts[artifactId] = {
                id: artifactId,
                title: meta.filename,
                lang: meta.lang,
                icon: meta.icon,
                code: cleanCode
            };

            const validLang = (typeof hljs !== 'undefined' && hljs.getLanguage(meta.lang)) ? meta.lang : '';
            const highlightedCode = validLang ? hljs.highlight(cleanCode, { language: validLang }).value : escapeHtml(cleanCode);
            const displayLang = meta.lang.toUpperCase();

            // If it's a substantive code file (> 6 lines or html/css/js/json), render a Claude-style Artifact Card Widget!
            if (meta.lines >= 6 || ['html', 'css', 'javascript', 'json', 'python'].includes(meta.lang)) {
                return `
                    <div class="claude-artifact-card" data-artifact-id="${artifactId}">
                        <div class="artifact-card-left">
                            <div class="artifact-card-icon-box">${meta.icon}</div>
                            <div class="artifact-card-info">
                                <span class="artifact-card-title">${escapeHtml(meta.filename)}</span>
                                <span class="artifact-card-meta">
                                    <span class="meta-badge">${escapeHtml(displayLang)}</span>
                                    <span>${meta.lines} lines</span>
                                    <span>• Click to open Code Studio</span>
                                </span>
                            </div>
                        </div>
                        <div class="artifact-card-right">
                            <button type="button" class="open-artifact-btn" data-artifact-id="${artifactId}">
                                <span>Open Code</span>
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
                            </button>
                        </div>
                    </div>
                    <details class="inline-code-details">
                        <summary>View code inline (${meta.lines} lines)</summary>
                        <div class="code-block-wrapper">
                            <div class="code-block-header">
                                <span class="code-lang-tag">${escapeHtml(displayLang)}</span>
                                <button type="button" class="copy-code-btn" data-code="${escapeHtml(cleanCode)}">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                                    <span>Copy code</span>
                                </button>
                            </div>
                            <pre><code class="hljs ${validLang}">${highlightedCode}</code></pre>
                        </div>
                    </details>
                    ${trailingMarkdown}
                `;
            }

            return `
                <div class="code-block-wrapper">
                    <div class="code-block-header">
                        <span class="code-lang-tag">${escapeHtml(displayLang)}</span>
                        <button type="button" class="copy-code-btn" data-code="${escapeHtml(cleanCode)}">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                            <span>Copy code</span>
                        </button>
                    </div>
                    <pre><code class="hljs ${validLang}">${highlightedCode}</code></pre>
                </div>
                ${trailingMarkdown}
            `;
        };

        marked.setOptions({
            renderer: renderer,
            breaks: true,
            gfm: true
        });
    }

    // DOM Elements - Artifact Drawer
    const artifactDrawer = document.getElementById('artifact-drawer');
    const artifactTitle = document.getElementById('artifact-title');
    const artifactLangBadge = document.getElementById('artifact-lang-badge');
    const artifactFileIcon = document.getElementById('artifact-file-icon');
    const artifactCodeDisplay = document.getElementById('artifact-code-display');
    const artifactPreviewIframe = document.getElementById('artifact-preview-iframe');
    const artifactCodeView = document.getElementById('artifact-code-view');
    const artifactPreviewView = document.getElementById('artifact-preview-view');
    const artifactTabCode = document.getElementById('artifact-tab-code');
    const artifactTabPreview = document.getElementById('artifact-tab-preview');
    const artifactTabsPill = document.getElementById('artifact-tabs-pill');
    const artifactCopyBtn = document.getElementById('artifact-copy-btn');
    const artifactDownloadBtn = document.getElementById('artifact-download-btn');
    const closeArtifactBtn = document.getElementById('close-artifact-btn');
    const mainContentArea = document.querySelector('.main-content');

    let currentOpenArtifact = null;

    window.openArtifactDrawer = function (artifactId) {
        const art = window.activeArtifacts[artifactId];
        if (!art) return;
        currentOpenArtifact = art;

        if (artifactTitle) artifactTitle.textContent = art.title;
        if (artifactLangBadge) artifactLangBadge.textContent = art.lang.toUpperCase();
        if (artifactFileIcon) artifactFileIcon.textContent = art.icon;

        if (artifactCodeDisplay) {
            artifactCodeDisplay.textContent = art.code;
            if (typeof hljs !== 'undefined') {
                artifactCodeDisplay.className = `hljs ${art.lang}`;
                hljs.highlightElement(artifactCodeDisplay);
            }
        }

        // Check if HTML for live preview tab
        if (art.lang === 'html' || art.code.includes('<html') || art.code.includes('<!DOCTYPE')) {
            if (artifactTabsPill) artifactTabsPill.classList.remove('hidden');
            
            let previewHtml = art.code;
            // If code contains placeholder GHL calendar iframe that fails in local sandbox,
            // replace with a beautiful interactive glassmorphic calendar mockup for preview!
            if (previewHtml.includes('YOUR_CALENDAR_ID') || previewHtml.includes('api.leadconnectorhq.com/widget/booking') || previewHtml.includes('services.leadconnectorhq.com')) {
                const calendarMockup = `
                <div id="interactive-ghl-calendar" style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 16px; padding: 24px; color: #fff; font-family: 'Plus Jakarta Sans', system-ui, sans-serif; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.5); user-select: none;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 12px;">
                        <span style="font-weight: 700; color: #38bdf8; font-size: 1.05rem;">📅 Select Assessment Date & Time</span>
                        <span style="font-size: 0.75rem; background: rgba(56, 189, 248, 0.15); color: #38bdf8; padding: 4px 10px; border-radius: 12px; font-weight: 600;">15 Min Slot</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #94a3b8; margin-bottom: 8px; text-align: left;">1. Select Date (October 2026):</div>
                    <div style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; margin-bottom: 18px; font-size: 0.8rem;" id="cal-dates-grid">
                        <span style="color: #94a3b8; font-weight: 600; padding: 4px 0;">M</span>
                        <span style="color: #94a3b8; font-weight: 600; padding: 4px 0;">T</span>
                        <span style="color: #94a3b8; font-weight: 600; padding: 4px 0;">W</span>
                        <span style="color: #94a3b8; font-weight: 600; padding: 4px 0;">T</span>
                        <span style="color: #94a3b8; font-weight: 600; padding: 4px 0;">F</span>
                        <span style="color: #94a3b8; font-weight: 600; padding: 4px 0;">S</span>
                        <span style="color: #94a3b8; font-weight: 600; padding: 4px 0;">S</span>
                        <button type="button" class="mock-date-btn" data-date="Oct 14" style="padding: 8px 4px; border-radius: 8px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); color: #cbd5e1; cursor: pointer; transition: all 0.15s;">14</button>
                        <button type="button" class="mock-date-btn" data-date="Oct 15" style="padding: 8px 4px; border-radius: 8px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); color: #cbd5e1; cursor: pointer; transition: all 0.15s;">15</button>
                        <button type="button" class="mock-date-btn active-date" data-date="Oct 16" style="padding: 8px 4px; border-radius: 8px; background: #0284c7; border: 1px solid #38bdf8; color: #fff; font-weight: 700; cursor: pointer; box-shadow: 0 0 10px rgba(2,132,199,0.5); transition: all 0.15s;">16</button>
                        <button type="button" class="mock-date-btn" data-date="Oct 17" style="padding: 8px 4px; border-radius: 8px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); color: #cbd5e1; cursor: pointer; transition: all 0.15s;">17</button>
                        <button type="button" class="mock-date-btn" data-date="Oct 18" style="padding: 8px 4px; border-radius: 8px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); color: #cbd5e1; cursor: pointer; transition: all 0.15s;">18</button>
                        <button type="button" class="mock-date-btn" data-date="Oct 19" style="padding: 8px 4px; border-radius: 8px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); color: #cbd5e1; cursor: pointer; transition: all 0.15s;">19</button>
                        <button type="button" class="mock-date-btn" data-date="Oct 20" style="padding: 8px 4px; border-radius: 8px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); color: #cbd5e1; cursor: pointer; transition: all 0.15s;">20</button>
                    </div>
                    <div style="font-size: 0.8rem; color: #94a3b8; margin-bottom: 8px; text-align: left;">2. Select Time Slot (EST):</div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 18px;" id="cal-slots-grid">
                        <button type="button" class="mock-time-btn" data-time="09:30 AM" style="background: rgba(255,255,255,0.06); border: 1px solid rgba(56, 189, 248, 0.3); color: #fff; padding: 10px; border-radius: 8px; cursor: pointer; font-size: 0.85rem; transition: all 0.15s;">09:30 AM</button>
                        <button type="button" class="mock-time-btn" data-time="11:00 AM" style="background: rgba(255,255,255,0.06); border: 1px solid rgba(56, 189, 248, 0.3); color: #fff; padding: 10px; border-radius: 8px; cursor: pointer; font-size: 0.85rem; transition: all 0.15s;">11:00 AM</button>
                        <button type="button" class="mock-time-btn active-time" data-time="02:00 PM" style="background: #0284c7; border: 1px solid #38bdf8; color: #fff; padding: 10px; border-radius: 8px; cursor: pointer; font-weight: 700; font-size: 0.85rem; box-shadow: 0 0 10px rgba(2,132,199,0.4); transition: all 0.15s;">02:00 PM ✓</button>
                        <button type="button" class="mock-time-btn" data-time="04:30 PM" style="background: rgba(255,255,255,0.06); border: 1px solid rgba(56, 189, 248, 0.3); color: #fff; padding: 10px; border-radius: 8px; cursor: pointer; font-size: 0.85rem; transition: all 0.15s;">04:30 PM</button>
                    </div>
                    <button type="button" id="mock-confirm-booking-btn" style="width: 100%; background: linear-gradient(135deg, #0ea5e9, #2563eb); border: none; color: #fff; padding: 12px; border-radius: 10px; font-weight: 700; font-size: 0.95rem; cursor: pointer; box-shadow: 0 4px 12px rgba(14,165,233,0.3); transition: transform 0.15s;">Confirm Assessment Time ➔</button>
                    <p style="font-size: 0.72rem; color: #94a3b8; margin-top: 10px;">⚡ HighLevel native calendar will load your live slots once deployed with your Calendar ID.</p>
                </div>
                `;
                previewHtml = previewHtml.replace(/<iframe[^>]*api\.leadconnectorhq\.com[^>]*>.*?<\/iframe>/gis, calendarMockup)
                                         .replace(/<iframe[^>]*YOUR_CALENDAR_ID[^>]*>.*?<\/iframe>/gis, calendarMockup)
                                         .replace(/<iframe[^>]*leadconnectorhq\.com[^>]*><\/iframe>/gis, calendarMockup);
            }

            // Inject Live Preview form submit & calendar click interceptor
            const formInterceptScript = `
            <script>
            (function() {
                var selectedDate = 'Oct 16';
                var selectedTime = '02:00 PM';

                document.addEventListener('click', function(e) {
                    var dateBtn = e.target.closest('.mock-date-btn');
                    if (dateBtn) {
                        var allDates = document.querySelectorAll('.mock-date-btn');
                        for (var i = 0; i < allDates.length; i++) {
                            allDates[i].style.background = 'rgba(255,255,255,0.04)';
                            allDates[i].style.border = '1px solid rgba(255,255,255,0.08)';
                            allDates[i].style.color = '#cbd5e1';
                            allDates[i].style.fontWeight = 'normal';
                            allDates[i].style.boxShadow = 'none';
                        }
                        dateBtn.style.background = '#0284c7';
                        dateBtn.style.border = '1px solid #38bdf8';
                        dateBtn.style.color = '#fff';
                        dateBtn.style.fontWeight = 'bold';
                        dateBtn.style.boxShadow = '0 0 10px rgba(2,132,199,0.5)';
                        selectedDate = dateBtn.getAttribute('data-date') || dateBtn.textContent.trim();
                    }

                    var timeBtn = e.target.closest('.mock-time-btn');
                    if (timeBtn) {
                        var allTimes = document.querySelectorAll('.mock-time-btn');
                        for (var j = 0; j < allTimes.length; j++) {
                            allTimes[j].style.background = 'rgba(255,255,255,0.06)';
                            allTimes[j].style.border = '1px solid rgba(56, 189, 248, 0.3)';
                            allTimes[j].style.color = '#fff';
                            allTimes[j].style.fontWeight = 'normal';
                            allTimes[j].style.boxShadow = 'none';
                            allTimes[j].textContent = allTimes[j].getAttribute('data-time') || allTimes[j].textContent.replace('✓', '').trim();
                        }
                        timeBtn.style.background = '#0284c7';
                        timeBtn.style.border = '1px solid #38bdf8';
                        timeBtn.style.color = '#fff';
                        timeBtn.style.fontWeight = 'bold';
                        timeBtn.style.boxShadow = '0 0 10px rgba(2,132,199,0.4)';
                        var t = timeBtn.getAttribute('data-time') || timeBtn.textContent.trim();
                        timeBtn.textContent = t + ' ✓';
                        selectedTime = t;
                    }

                    var confirmBtn = e.target.closest('#mock-confirm-booking-btn');
                    if (confirmBtn) {
                        var calWrapper = document.getElementById('interactive-ghl-calendar');
                        if (calWrapper) {
                            calWrapper.innerHTML = '<div style="text-align: center; padding: 32px 14px; font-family: sans-serif;">' +
                                '<div style="width: 60px; height: 60px; border-radius: 50%; background: linear-gradient(135deg, #10b981, #059669); color: #fff; font-size: 30px; display: flex; align-items: center; justify-content: center; margin: 0 auto 16px auto; box-shadow: 0 0 24px rgba(16, 185, 129, 0.5);">🎉</div>' +
                                '<h3 style="color: #fff; font-size: 1.4rem; font-weight: 800; margin-bottom: 8px;">Assessment Confirmed!</h3>' +
                                '<p style="color: #38bdf8; font-weight: 700; font-size: 1rem; margin-bottom: 12px;">' + selectedDate + ' at ' + selectedTime + ' EST</p>' +
                                '<p style="color: #94a3b8; font-size: 0.85rem; line-height: 1.5; margin-bottom: 18px;">A calendar invite and SMS confirmation with your dedicated coach details have been dispatched to your phone.</p>' +
                                '<div style="background: rgba(14, 165, 233, 0.12); border: 1px solid rgba(14, 165, 233, 0.35); border-radius: 12px; padding: 12px; color: #38bdf8; font-size: 0.8rem; text-align: left;">' +
                                    '⚡ <strong>Live Demo:</strong> In your GoHighLevel CRM, this booking automatically moves the opportunity stage to <em>"Appointment Scheduled"</em> and activates the 24-Hour Reminder Sequence!' +
                                '</div>' +
                            '</div>';
                        }
                    }
                });

                document.addEventListener('DOMContentLoaded', function() {
                    var forms = document.querySelectorAll('form');
                    forms.forEach(function(form) {
                        form.addEventListener('submit', function(e) {
                            e.preventDefault();
                            
                            var fNameInput = form.querySelector('[name="first_name"]');
                            var phoneInput = form.querySelector('[name="phone"]');
                            var goalInput = form.querySelector('[name="fitness_goal"], [name="service_type"], [name="membership_tier_interest"]');
                            
                            var fName = (fNameInput && fNameInput.value) ? fNameInput.value.trim() : 'Champion';
                            var phone = (phoneInput && phoneInput.value) ? phoneInput.value.trim() : 'your mobile phone';
                            var goal = (goalInput && goalInput.value) ? goalInput.value.trim() : 'your program';

                            var submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
                            if (submitBtn) {
                                submitBtn.disabled = true;
                                submitBtn.innerHTML = '⚡ Dispatching Call...';
                            }

                            setTimeout(function() {
                                var formCard = form.closest('.glass-card, .glass-form-card') || form.parentElement;
                                if (formCard) {
                                    formCard.innerHTML = '<div style="text-align: center; padding: 20px 10px; font-family: sans-serif; position: relative;">' +
                                        '<style>' +
                                        '@keyframes radarPulse { 0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); } 70% { transform: scale(1.05); box-shadow: 0 0 0 20px rgba(16, 185, 129, 0); } 100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); } }' +
                                        '@keyframes slideInSms { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }' +
                                        '</style>' +
                                        '<div style="width: 70px; height: 70px; border-radius: 50%; background: linear-gradient(135deg, #10b981, #059669); color: #fff; font-size: 32px; display: flex; align-items: center; justify-content: center; margin: 0 auto 16px auto; animation: radarPulse 2s infinite; cursor: pointer;" title="Active Outbound Ring">📞</div>' +
                                        '<h3 style="color: #fff; font-size: 1.4rem; font-weight: 800; margin-bottom: 4px;">Calling You Right Now!</h3>' +
                                        '<p style="color: #10b981; font-weight: 700; font-size: 0.95rem; margin-bottom: 14px;">⚡ Live Priority Callback Dispatched</p>' +
                                        
                                        '<div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 12px; padding: 12px 16px; margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between;">' +
                                            '<div style="text-align: left;"><span style="font-size: 0.75rem; color: #94a3b8; text-transform: uppercase;">Connecting In:</span><div style="font-size: 1.2rem; font-weight: 800; color: #10b981;" id="live-call-timer">00:48s</div></div>' +
                                            '<div style="display: flex; gap: 4px; align-items: center;"><span style="width: 8px; height: 8px; border-radius: 50%; background: #10b981; display: inline-block; animation: radarPulse 1s infinite;"></span><span style="font-size: 0.8rem; color: #cbd5e1; font-weight: 600;">Dialing Rep...</span></div>' +
                                        '</div>' +

                                        '<p style="color: #cbd5e1; font-size: 0.9rem; line-height: 1.5; margin-bottom: 16px;">Hey <strong>' + fName + '</strong>, Coach Alex is dialing <strong>' + phone + '</strong> regarding your <em>' + goal + '</em>. Please answer when your phone rings!</p>' +

                                        '<!-- Simulated HighLevel SMS Inbound Demo Card -->' +
                                        '<div id="simulated-sms-box" style="background: rgba(18, 24, 38, 0.95); border: 1px solid rgba(59, 130, 246, 0.4); border-radius: 12px; padding: 12px 14px; text-align: left; margin-bottom: 16px; animation: slideInSms 0.4s ease; box-shadow: 0 8px 20px rgba(0,0,0,0.4);">' +
                                            '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">' +
                                                '<span style="font-size: 0.75rem; font-weight: 700; color: #60a5fa; display: flex; align-items: center; gap: 6px;">💬 HighLevel Instant SMS Dispatched (T+0s)</span>' +
                                                '<span style="font-size: 0.7rem; color: #94a3b8;">Just Now</span>' +
                                            '</div>' +
                                            '<p style="font-size: 0.82rem; color: #f8fafc; line-height: 1.4; margin: 0;">"Hey ' + fName + '! This is Coach Alex from IronPulse Fitness. Dialing your phone right now for your ' + goal + ' consultation. Keep phone handy!"</p>' +
                                        '</div>' +

                                        '<div style="display: flex; gap: 8px; margin-bottom: 14px;">' +
                                            '<button type="button" id="switch-to-cal-btn" style="flex: 1; background: rgba(255,255,255,0.06); border: 1px solid rgba(56, 189, 248, 0.35); color: #38bdf8; padding: 10px; border-radius: 8px; font-size: 0.82rem; font-weight: 700; cursor: pointer; transition: all 0.15s;">📅 Pick a Specific Time on Calendar ➔</button>' +
                                        '</div>' +

                                        '<div style="border-top: 1px solid rgba(255,255,255,0.08); padding-top: 12px; font-size: 0.78rem; color: #94a3b8; display: flex; justify-content: space-between;">' +
                                            '<span>Response Guarantee: <strong>&lt; 60s</strong></span>' +
                                            '<span>Status: <strong style="color: #10b981;">Active Outbound Call</strong></span>' +
                                        '</div>' +
                                    '</div>';

                                    // Start Live Countdown Timer
                                    var timeLeft = 48;
                                    var timerInterval = setInterval(function() {
                                        timeLeft--;
                                        var timerEl = document.getElementById('live-call-timer');
                                        if (timerEl) {
                                            timerEl.textContent = '00:' + (timeLeft < 10 ? '0' : '') + timeLeft + 's';
                                            if (timeLeft <= 0) {
                                                clearInterval(timerInterval);
                                                timerEl.textContent = 'Connected!';
                                                timerEl.style.color = '#38bdf8';
                                            }
                                        } else {
                                            clearInterval(timerInterval);
                                        }
                                    }, 1000);

                                    // Switch to Calendar Handler
                                    var switchCalBtn = document.getElementById('switch-to-cal-btn');
                                    if (switchCalBtn) {
                                        switchCalBtn.addEventListener('click', function() {
                                            clearInterval(timerInterval);
                                            formCard.innerHTML = '<div style="text-align: left; animation: fadeIn 0.35s ease; font-family: sans-serif;">' +
                                                '<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 14px; background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.4); padding: 8px 12px; border-radius: 8px; color: #10b981; font-size: 0.8rem; font-weight: 700;">' +
                                                    '<span>✓ Details Captured for ' + fName + ' (' + phone + ')</span>' +
                                                '</div>' +
                                                '<h3 style="color: #fff; font-size: 1.25rem; font-weight: 700; margin-bottom: 4px;">Select Consultation Date & Time</h3>' +
                                                '<p style="color: #94a3b8; font-size: 0.82rem; margin-bottom: 14px;">Pick a 15-minute 1-on-1 coaching slot with Head Coach Alex:</p>' +
                                                '<div id="interactive-ghl-calendar" style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 14px; padding: 18px; color: #fff; text-align: center;">' +
                                                    '<div style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; margin-bottom: 14px; font-size: 0.8rem;">' +
                                                        '<span style="color: #94a3b8; font-weight: 600;">M</span><span style="color: #94a3b8; font-weight: 600;">T</span><span style="color: #94a3b8; font-weight: 600;">W</span><span style="color: #94a3b8; font-weight: 600;">T</span><span style="color: #94a3b8; font-weight: 600;">F</span><span style="color: #94a3b8; font-weight: 600;">S</span><span style="color: #94a3b8; font-weight: 600;">S</span>' +
                                                        '<button type="button" class="mock-date-btn" data-date="Oct 14" style="padding: 7px 4px; border-radius: 6px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); color: #cbd5e1; cursor: pointer;">14</button>' +
                                                        '<button type="button" class="mock-date-btn" data-date="Oct 15" style="padding: 7px 4px; border-radius: 6px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); color: #cbd5e1; cursor: pointer;">15</button>' +
                                                        '<button type="button" class="mock-date-btn" data-date="Oct 16" style="padding: 7px 4px; border-radius: 6px; background: #0284c7; border: 1px solid #38bdf8; color: #fff; font-weight: 700; cursor: pointer;">16</button>' +
                                                        '<button type="button" class="mock-date-btn" data-date="Oct 17" style="padding: 7px 4px; border-radius: 6px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); color: #cbd5e1; cursor: pointer;">17</button>' +
                                                        '<button type="button" class="mock-date-btn" data-date="Oct 18" style="padding: 7px 4px; border-radius: 6px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); color: #cbd5e1; cursor: pointer;">18</button>' +
                                                        '<button type="button" class="mock-date-btn" data-date="Oct 19" style="padding: 7px 4px; border-radius: 6px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); color: #cbd5e1; cursor: pointer;">19</button>' +
                                                        '<button type="button" class="mock-date-btn" data-date="Oct 20" style="padding: 7px 4px; border-radius: 6px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); color: #cbd5e1; cursor: pointer;">20</button>' +
                                                    '</div>' +
                                                    '<div style="font-size: 0.8rem; color: #cbd5e1; margin-bottom: 8px; text-align: left;">Available Consultation Times (EST):</div>' +
                                                    '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 16px;">' +
                                                        '<button type="button" class="mock-time-btn" data-time="09:30 AM" style="background: rgba(255,255,255,0.06); border: 1px solid rgba(56, 189, 248, 0.3); color: #fff; padding: 9px; border-radius: 8px; cursor: pointer; font-size: 0.85rem;">09:30 AM</button>' +
                                                        '<button type="button" class="mock-time-btn" data-time="11:00 AM" style="background: rgba(255,255,255,0.06); border: 1px solid rgba(56, 189, 248, 0.3); color: #fff; padding: 9px; border-radius: 8px; cursor: pointer; font-size: 0.85rem;">11:00 AM</button>' +
                                                        '<button type="button" class="mock-time-btn" data-time="02:00 PM" style="background: #0284c7; border: 1px solid #38bdf8; color: #fff; padding: 9px; border-radius: 8px; cursor: pointer; font-weight: 700; font-size: 0.85rem;">02:00 PM ✓</button>' +
                                                        '<button type="button" class="mock-time-btn" data-time="04:30 PM" style="background: rgba(255,255,255,0.06); border: 1px solid rgba(56, 189, 248, 0.3); color: #fff; padding: 9px; border-radius: 8px; cursor: pointer; font-size: 0.85rem;">04:30 PM</button>' +
                                                    '</div>' +
                                                    '<button type="button" id="mock-confirm-booking-btn" style="width: 100%; background: linear-gradient(135deg, #0ea5e9, #2563eb); border: none; color: #fff; padding: 11px; border-radius: 8px; font-weight: 700; font-size: 0.9rem; cursor: pointer;">Confirm Consultation Time ➔</button>' +
                                                '</div>' +
                                            '</div>';
                                        });
                                    }
                                }
                            }, 500);
                        });
                    });
                });
            })();
            <\/script>
            `;

            if (previewHtml.includes('</body>')) {
                previewHtml = previewHtml.replace('</body>', formInterceptScript + '</body>');
            } else {
                previewHtml += formInterceptScript;
            }

            if (artifactPreviewIframe) artifactPreviewIframe.srcdoc = previewHtml;
            setArtifactTab('preview');
        } else {
            if (artifactTabsPill) artifactTabsPill.classList.add('hidden');
            setArtifactTab('code');
        }

        if (artifactDrawer) artifactDrawer.classList.remove('hidden');
        if (mainContentArea) mainContentArea.classList.add('artifact-drawer-open');
    };

    window.closeArtifactDrawer = function () {
        if (artifactDrawer) artifactDrawer.classList.add('hidden');
        if (mainContentArea) mainContentArea.classList.remove('artifact-drawer-open');
        currentOpenArtifact = null;
    };

    function setArtifactTab(tab) {
        if (tab === 'preview') {
            if (artifactTabPreview) artifactTabPreview.classList.add('active');
            if (artifactTabCode) artifactTabCode.classList.remove('active');
            if (artifactPreviewView) artifactPreviewView.classList.remove('hidden');
            if (artifactCodeView) artifactCodeView.classList.add('hidden');
        } else {
            if (artifactTabCode) artifactTabCode.classList.add('active');
            if (artifactTabPreview) artifactTabPreview.classList.remove('active');
            if (artifactCodeView) artifactCodeView.classList.remove('hidden');
            if (artifactPreviewView) artifactPreviewView.classList.add('hidden');
        }
    }

    if (artifactTabCode) artifactTabCode.addEventListener('click', () => setArtifactTab('code'));
    if (artifactTabPreview) artifactTabPreview.addEventListener('click', () => setArtifactTab('preview'));
    if (closeArtifactBtn) closeArtifactBtn.addEventListener('click', window.closeArtifactDrawer);

    if (artifactCopyBtn) {
        artifactCopyBtn.addEventListener('click', () => {
            if (!currentOpenArtifact) return;
            navigator.clipboard.writeText(currentOpenArtifact.code).then(() => {
                const span = artifactCopyBtn.querySelector('span');
                if (span) span.textContent = 'Copied!';
                setTimeout(() => { if (span) span.textContent = 'Copy'; }, 2000);
            });
        });
    }

    if (artifactDownloadBtn) {
        artifactDownloadBtn.addEventListener('click', () => {
            if (!currentOpenArtifact) return;
            const blob = new Blob([currentOpenArtifact.code], { type: 'text/plain;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = currentOpenArtifact.title;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        });
    }

    // Delegate clicks on artifact cards
    document.addEventListener('click', (e) => {
        const card = e.target.closest('.claude-artifact-card');
        if (card) {
            const id = card.getAttribute('data-artifact-id');
            if (id) window.openArtifactDrawer(id);
        }
    });

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

    // ==========================================
    // CONFIRMATION & RENAME MODAL ENGINE
    // ==========================================
    let pendingConfirmCallback = null;
    const confirmActionModal = document.getElementById('confirm-action-modal');
    const confirmModalTitle = document.getElementById('confirm-modal-title');
    const confirmModalDesc = document.getElementById('confirm-modal-desc');
    const confirmModalIcon = document.getElementById('confirm-modal-icon');
    const executeConfirmBtn = document.getElementById('execute-confirm-btn');
    const cancelConfirmBtn = document.getElementById('cancel-confirm-btn');
    const closeConfirmModalBtn = document.getElementById('close-confirm-modal');

    function showConfirmModal({ title, desc, icon = '🗑️', confirmText = 'Delete', onConfirm }) {
        if (confirmModalTitle) confirmModalTitle.textContent = title;
        if (confirmModalDesc) confirmModalDesc.textContent = desc;
        if (confirmModalIcon) confirmModalIcon.textContent = icon;
        if (executeConfirmBtn) executeConfirmBtn.textContent = confirmText;
        pendingConfirmCallback = onConfirm;
        if (confirmActionModal) confirmActionModal.classList.remove('hidden');
    }

    function hideConfirmModal() {
        if (confirmActionModal) confirmActionModal.classList.add('hidden');
        pendingConfirmCallback = null;
    }

    if (cancelConfirmBtn) cancelConfirmBtn.addEventListener('click', hideConfirmModal);
    if (closeConfirmModalBtn) closeConfirmModalBtn.addEventListener('click', hideConfirmModal);
    if (executeConfirmBtn) {
        executeConfirmBtn.addEventListener('click', () => {
            if (pendingConfirmCallback) {
                const cb = pendingConfirmCallback;
                hideConfirmModal();
                cb();
            } else {
                hideConfirmModal();
            }
        });
    }

    // Rename Modal Elements
    const renameChatModal = document.getElementById('rename-chat-modal');
    const renameInputTitle = document.getElementById('rename-input-title');
    const saveRenameBtn = document.getElementById('save-rename-btn');
    const cancelRenameBtn = document.getElementById('cancel-rename-btn');
    const closeRenameModalBtn = document.getElementById('close-rename-modal');

    function openRenameModal() {
        const thread = getThreadById(currentThreadId);
        if (renameInputTitle) {
            renameInputTitle.value = (thread && thread.title) ? thread.title : 'Conversation AI Copilot';
        }
        if (renameChatModal) renameChatModal.classList.remove('hidden');
        if (renameInputTitle) setTimeout(() => renameInputTitle.focus(), 50);
    }

    function hideRenameModal() {
        if (renameChatModal) renameChatModal.classList.add('hidden');
    }

    function saveRenamedTitle() {
        const newTitle = renameInputTitle ? renameInputTitle.value.trim() : '';
        if (!newTitle) return;
        let thread = getThreadById(currentThreadId);
        if (thread) {
            thread.title = newTitle;
            saveThreads();
        }
        if (activeChatTitle) activeChatTitle.textContent = newTitle;
        renderRecentChatsList();
        hideRenameModal();
    }

    if (saveRenameBtn) saveRenameBtn.addEventListener('click', saveRenamedTitle);
    if (cancelRenameBtn) cancelRenameBtn.addEventListener('click', hideRenameModal);
    if (closeRenameModalBtn) closeRenameModalBtn.addEventListener('click', hideRenameModal);
    if (renameInputTitle) {
        renameInputTitle.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                saveRenamedTitle();
            }
        });
    }

    // Header Chat Actions & Dropdown
    const headerNewChatBtn = document.getElementById('header-new-chat-btn');
    const chatOptionsTriggerBtn = document.getElementById('chat-options-trigger-btn');
    const chatOptionsDropdown = document.getElementById('chat-options-dropdown');
    const dropdownRenameChatBtn = document.getElementById('dropdown-rename-chat-btn');
    const dropdownCloseChatBtn = document.getElementById('dropdown-close-chat-btn');
    const dropdownClearMsgsBtn = document.getElementById('dropdown-clear-msgs-btn');
    const dropdownDeleteChatBtn = document.getElementById('dropdown-delete-chat-btn');

    if (headerNewChatBtn) {
        headerNewChatBtn.addEventListener('click', () => createNewThread(true));
    }

    if (chatOptionsTriggerBtn && chatOptionsDropdown) {
        chatOptionsTriggerBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            chatOptionsDropdown.classList.toggle('hidden');
        });

        document.addEventListener('click', (e) => {
            if (!chatOptionsDropdown.contains(e.target) && e.target !== chatOptionsTriggerBtn) {
                chatOptionsDropdown.classList.add('hidden');
            }
        });
    }

    if (dropdownRenameChatBtn) {
        dropdownRenameChatBtn.addEventListener('click', () => {
            if (chatOptionsDropdown) chatOptionsDropdown.classList.add('hidden');
            openRenameModal();
        });
    }

    if (dropdownCloseChatBtn) {
        dropdownCloseChatBtn.addEventListener('click', () => {
            if (chatOptionsDropdown) chatOptionsDropdown.classList.add('hidden');
            closeCurrentChat();
        });
    }

    if (dropdownClearMsgsBtn) {
        dropdownClearMsgsBtn.addEventListener('click', () => {
            if (chatOptionsDropdown) chatOptionsDropdown.classList.add('hidden');
            clearCurrentChatMessages();
        });
    }

    if (dropdownDeleteChatBtn) {
        dropdownDeleteChatBtn.addEventListener('click', () => {
            if (chatOptionsDropdown) chatOptionsDropdown.classList.add('hidden');
            deleteCurrentChat();
        });
    }

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
        abortCurrentGeneration();
        clearPromptQueue();
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
        updateSendButtonState();
        renderRecentChatsList();
    }

    function closeCurrentChat() {
        createNewThread(true);
    }

    function clearCurrentChatMessages() {
        showConfirmModal({
            title: 'Clear Messages',
            desc: 'Are you sure you want to clear all messages in this conversation?',
            icon: '🧹',
            confirmText: 'Clear Messages',
            onConfirm: () => {
                abortCurrentGeneration();
                clearPromptQueue();
                let thread = getThreadById(currentThreadId);
                if (thread) {
                    thread.messages = [];
                    saveThreads();
                }
                messagesList.innerHTML = '';
                if (welcomeScreen) welcomeScreen.classList.remove('hidden');
                updateSendButtonState();
                renderRecentChatsList();
            }
        });
    }

    function deleteCurrentChat() {
        showConfirmModal({
            title: 'Delete Conversation',
            desc: 'Are you sure you want to permanently delete this conversation?',
            icon: '🗑️',
            confirmText: 'Delete',
            onConfirm: () => {
                deleteThread(currentThreadId);
            }
        });
    }

    function loadThread(threadId) {
        abortCurrentGeneration();
        clearPromptQueue();
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
                    appendMessageUI('user', msg.content, msg.id);
                } else {
                    renderAssistantMessageUI(msg);
                }
            });
        }

        updateSendButtonState();


        renderRecentChatsList();
        scrollToBottom();
        if (window.innerWidth <= 768) closeSidebar();
    }

    function addMessageToCurrentThread(role, content, toolBadges = [], messageId = null) {
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

        const msgObj = {
            id: messageId || ('msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5)),
            role: role,
            content: content,
            toolBadges: toolBadges,
            timestamp: new Date().toISOString()
        };

        thread.messages.push(msgObj);
        saveThreads();
        renderRecentChatsList();
        return msgObj.id;
    }

    function deleteMessageFromThread(messageId, msgElement) {
        let thread = getThreadById(currentThreadId);
        if (thread && thread.messages) {
            thread.messages = thread.messages.filter(m => m.id !== messageId && m.content !== msgElement?.getAttribute('data-content'));
            saveThreads();
        }
        if (msgElement) msgElement.remove();
        if (messagesList.children.length === 0 && welcomeScreen) {
            welcomeScreen.classList.remove('hidden');
        }
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
                <div class="history-item ${isActive ? 'active' : ''}" data-thread-id="${escapeHtml(thread.id)}">
                    <div class="history-item-left">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
                        <span class="history-item-title">${escapeHtml(thread.title || 'Untitled Conversation')}</span>
                    </div>
                    <button class="delete-history-btn" data-delete-id="${escapeHtml(thread.id)}" title="Delete chat">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                    </button>
                </div>
            `;
        }).join('');

        // Attach click listeners to history items
        historyList.querySelectorAll('.history-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.closest('.delete-history-btn')) return;
                const threadId = item.getAttribute('data-thread-id');
                loadThread(threadId);
            });
        });

        // Attach delete listeners with confirm modal
        historyList.querySelectorAll('.delete-history-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const threadId = btn.getAttribute('data-delete-id');
                showConfirmModal({
                    title: 'Delete Chat',
                    desc: 'Are you sure you want to delete this chat thread?',
                    icon: '🗑️',
                    confirmText: 'Delete',
                    onConfirm: () => deleteThread(threadId)
                });
            });
        });
    }

    if (newChatBtn) {
        newChatBtn.addEventListener('click', () => createNewThread(true));
    }

    if (clearAllHistoryBtn) {
        clearAllHistoryBtn.addEventListener('click', () => {
            if (chatThreads.length === 0) return;
            showConfirmModal({
                title: 'Clear All Chat History',
                desc: 'Are you sure you want to delete ALL conversations permanently?',
                icon: '⚠️',
                confirmText: 'Clear All History',
                onConfirm: () => {
                    chatThreads = [];
                    saveThreads();
                    createNewThread();
                }
            });
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

            if (modelSelector) {
                modelSelector.addEventListener('change', () => {
                    localStorage.setItem('selected_ai_model', modelSelector.value);
                    updateActiveModelUsageDisplay();
                });
            }
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
        if (usageModal) usageModal.classList.remove('hidden');
        await fetchModelsCatalog();
        renderUsageModalGrid();
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
    // DYNAMIC MULTI-NICHE BUILDER WIZARD ENGINE
    // ==========================================
    const wizardModal = document.getElementById('builder-wizard-modal');
    const openWizardChipBtn = document.getElementById('open-wizard-chip-btn');
    const closeWizardModalBtn = document.getElementById('close-wizard-modal');
    const cancelWizardModalBtn = document.getElementById('cancel-wizard-modal');
    const wizardNextBtn = document.getElementById('wizard-next-btn');
    const wizardBackBtn = document.getElementById('wizard-back-btn');
    const wizardQuickBtn = document.getElementById('wizard-quick-btn');
    const wizardValidationBar = document.getElementById('wizard-validation-bar');
    const wizardValidationText = document.getElementById('wizard-validation-text');
    const btnModeFunnel = document.getElementById('btn-mode-funnel');
    const btnModeLanding = document.getElementById('btn-mode-landing');

    const TOTAL_WIZARD_STEPS = 6;
    let currentWizardStep = 1;
    let currentNicheKey = 'fitness';
    let currentWizardMode = 'funnel'; // 'funnel' | 'landing_page'

    // Mode Toggle Events
    if (btnModeFunnel) {
        btnModeFunnel.addEventListener('click', () => {
            currentWizardMode = 'funnel';
            btnModeFunnel.classList.add('active');
            if (btnModeLanding) btnModeLanding.classList.remove('active');
            applyNicheConfiguration(currentNicheKey);
        });
    }

    if (btnModeLanding) {
        btnModeLanding.addEventListener('click', () => {
            currentWizardMode = 'landing_page';
            btnModeLanding.classList.add('active');
            if (btnModeFunnel) btnModeFunnel.classList.remove('active');
            applyNicheConfiguration(currentNicheKey);
        });
    }

    // Comprehensive Niche-Specific Configurations & Tailored Questions
    const NICHE_CONFIGURATIONS = {
        'fitness': {
            key: 'fitness',
            name: 'Fitness & Gym Studio',
            icon: '🏋️',
            matchKeywords: ['gym', 'fitness', 'workout', 'trainer', 'training', 'crossfit', 'yoga', 'pilates', 'bodybuilding', 'weight loss', 'muscle'],
            step2_funnel: {
                title: 'Step 2: Choose your Multi-Step Fitness Funnel Flow',
                desc: 'Select the complete multi-step funnel progression (Opt-in ➔ VSL/Sales ➔ Checkout/Booking ➔ Upsell ➔ Thank You).',
                aiRecIdx: 0,
                aiRecText: 'AI Recommends: VSL & 1-on-1 Assessment Funnel converts 3.8x higher for personal training and boutique gyms.',
                options: [
                    {
                        icon: '🎬',
                        title: 'VSL & 1-on-1 Assessment Funnel',
                        desc: 'Step 1: Squeeze Page ➔ Step 2: VSL & Transformation Case Studies ➔ Step 3: Calendar Booking ➔ Step 4: VIP Assessment Upsell ➔ Step 5: Confirmation',
                        value: 'VSL & 1-on-1 Assessment Funnel (Squeeze ➔ VSL ➔ Calendar Booking ➔ VIP Upsell ➔ Confirmation)'
                    },
                    {
                        icon: '🎟️',
                        title: '7-Day VIP Pass Lead Magnet Funnel',
                        desc: 'Step 1: Opt-in Page ➔ Step 2: Instant SMS Pass Delivery & Studio Tour Video ➔ Step 3: $19 Kickstart Nutrition Upsell (OTO) ➔ Step 4: Thank You',
                        value: '7-Day VIP Pass Lead Magnet Funnel (Opt-in ➔ SMS Voucher ➔ $19 Kickstart Upsell ➔ Thank You)'
                    },
                    {
                        icon: '💳',
                        title: '6-Week Transformation Paid Challenge Funnel',
                        desc: 'Step 1: Long-Form Sales VSL ➔ Step 2: 2-Step Order Form ($97 Deposit) ➔ Step 3: 1-Click VIP Meal Plan Upsell ($37) ➔ Step 4: Member Portal Access',
                        value: '6-Week Challenge Paid Funnel (Long-Form VSL ➔ 2-Step Order Form ➔ 1-Click Upsell ➔ Portal Access)'
                    },
                    {
                        icon: '📱',
                        title: 'High-Ticket Personal Training Application Funnel',
                        desc: 'Step 1: Client Transformation Case Study ➔ Step 2: 6-Question Intake Application ➔ Step 3: Strategy Call Calendar ➔ Step 4: Confirmation',
                        value: 'High-Ticket PT Application Funnel (Case Study ➔ Application Form ➔ Calendar Booking ➔ Confirmation)'
                    }
                ]
            },
            step2_landing: {
                title: 'Step 2: What offer should your Fitness Landing Page promote?',
                desc: 'Select the primary single-page conversion hook for gym visitors.',
                aiRecIdx: 0,
                aiRecText: 'AI Recommends: 7-Day VIP Guest Pass converts 3.2x higher than standard forms for local gyms.',
                options: [
                    {
                        icon: '🎟️',
                        title: '7-Day Free VIP Pass / Trial Pass',
                        desc: 'Zero-friction lead magnet: Name, Phone & Email to claim instant digital guest pass',
                        value: '7-Day Free VIP Pass / Digital Guest Pass (Instant SMS Voucher)'
                    },
                    {
                        icon: '🏋️',
                        title: 'Free 1-on-1 Fitness Assessment',
                        desc: 'Direct calendar booking for InBody body composition scan & coaching session',
                        value: 'Free 1-on-1 Fitness & Body Scan Assessment (GHL Booking Calendar)'
                    },
                    {
                        icon: '⚡',
                        title: 'Speed-to-Lead Priority Callback',
                        desc: 'Instant 60s phone callback to claim limited-spot discounted membership',
                        value: 'Speed-to-Lead Priority Callback (Instant Auto-Dial & SMS Voucher)'
                    },
                    {
                        icon: '💳',
                        title: '6-Week Transformation Challenge',
                        desc: 'Direct registration page: Opt-in ➔ Direct checkout / Challenge deposit',
                        value: '6-Week Transformation Challenge (Opt-in ➔ Direct Checkout)'
                    }
                ]
            },
            step3: {
                title: 'Step 3: Choose your Fitness Visual Theme & Styling',
                desc: 'Select an aesthetic that matches your gym vibe and commands high perceived value.',
                aiRecIdx: 0,
                aiRecText: 'AI Recommends: Dark Neon Glassmorphism with electric lime accents drives maximum gym engagement.',
                options: [
                    {
                        icon: '🌙',
                        title: 'Dark Neon Athletic (High Energy)',
                        desc: 'Sleek matte dark UI, glowing neon lime/cyan accents, bold gym typography',
                        value: 'Dark Neon Athletic (High Energy Dark Palette with Electric Lime Accents)'
                    },
                    {
                        icon: '🔥',
                        title: 'Aggressive High-Contrast Beast Mode',
                        desc: 'Jet black background, fiery red/orange gradients, bold countdown banners',
                        value: 'Aggressive High-Contrast (Jet Black & Fiery Orange/Red Accents)'
                    },
                    {
                        icon: '🧘',
                        title: 'Clean Wellness & Holistic Yoga',
                        desc: 'Soft sage green & warm neutral palette, airy layout, mindful serene typography',
                        value: 'Clean Wellness & Holistic Yoga (Sage Green, Minimalist Warm Whites)'
                    },
                    {
                        icon: '💎',
                        title: 'Luxury Boutique Fitness Club',
                        desc: 'Matte slate, brushed gold highlights, high-end editorial club aesthetics',
                        value: 'Luxury Boutique Fitness Club (Matte Slate & Brushed Gold Editorial)'
                    }
                ]
            },
            step4_funnel: {
                title: 'Step 4: Multi-Step Funnel Automations & Recovery Workflows',
                desc: 'Select multi-step funnel triggers: 2-step abandoned cart, VSL watch triggers, and 1-click upsell fulfillments.',
                checkboxes: [
                    {
                        id: 'wiz-auto-sms',
                        label: '⚡ Instant Speed-to-Lead SMS with VIP Pass Voucher & Video Link',
                        desc: 'Dispatches personalized text with unique voucher & dials rep within 60s of opt-in',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-pipeline',
                        label: '📊 Funnel Stages Pipeline (Opt-in ➔ VSL Watched ➔ Checkout ➔ Upsell Won)',
                        desc: 'Stages: Step 1 Lead ➔ Step 2 VSL Engaged ➔ Step 3 Cart Started ➔ Step 4 Upsell Taken ➔ Member Active',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-tag',
                        label: '🛒 2-Step Order Form Abandoned Cart Recovery Sequence (T+15m, 4h, 24h)',
                        desc: 'Automated SMS/Email follow-up recovering unconverted Step 2 checkout drop-offs',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-reminders',
                        label: '⏰ VSL Watch-Progress Trigger (Unhides Buy Button at 80% mark)',
                        desc: 'Dynamically reveals pricing CTA and tags lead as `vsl:watched-high-intent` in CRM',
                        checked: true
                    }
                ]
            },
            step4_landing: {
                title: 'Step 4: Fitness CRM Automations & Qualification Fields',
                desc: 'Select the HighLevel workflows, pipelines, and intake fields to deploy.',
                checkboxes: [
                    {
                        id: 'wiz-auto-sms',
                        label: '⚡ Instant Speed-to-Lead SMS with VIP Pass Voucher Code',
                        desc: 'Dispatches personalized text with unique pass code & dials rep within 60s',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-pipeline',
                        label: '📊 Gym Sales Pipeline (8-Stage Member Conversion)',
                        desc: 'Stages: New Lead ➔ Pass Claimed ➔ Tour Booked ➔ Showed Up ➔ Active Member',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-tag',
                        label: '🏷️ Fitness Custom Fields (Goals, Preferred Workout Time)',
                        desc: 'Captures `fitness_goal`, `preferred_workout_time`, `past_injuries` into CRM',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-reminders',
                        label: '⏰ 24h & 48h Missed Workout / No-Show Recovery Cadence',
                        desc: 'Automated 3-touch reminder sequence to recover unconverted trial leads',
                        checked: true
                    }
                ]
            },
            step5: {
                title: 'Step 5: Gym Brand Customization',
                desc: 'Personalize with your gym details or use the AI-tailored fitness defaults.',
                brandNamePlaceholder: 'e.g. IronPulse Athletic Club',
                taglinePlaceholder: 'e.g. Transform Your Body in 90 Days — First Class Free',
                defaultBrandName: 'IronPulse Fitness',
                defaultTagline: 'Transform Your Body in 90 Days',
                defaultColor: '#10b981',
                colorPresets: ['#10b981', '#06b6d4', '#f97316', '#ef4444', '#8b5cf6', '#eab308']
            }
        },
        'local-services': {
            key: 'local-services',
            name: 'Local & Home Services',
            icon: '🏡',
            matchKeywords: ['contractor', 'roofing', 'solar', 'plumbing', 'hvac', 'electrician', 'cleaning', 'landscaping', 'home service', 'remodel', 'painter', 'pest control'],
            step2_funnel: {
                title: 'Step 2: Choose your Home Service Multi-Step Funnel Flow',
                desc: 'Select the complete multi-step funnel progression (Opt-in ➔ Estimate ➔ Booking ➔ Confirmation).',
                aiRecIdx: 0,
                aiRecText: 'AI Recommends: 2-Step Instant Quote & Consultation Funnel maximizes qualified contractor appointments.',
                options: [
                    {
                        icon: '📋',
                        title: '2-Step Instant Quote & Project Estimator Funnel',
                        desc: 'Step 1: Zip Code & Scope Squeeze ➔ Step 2: Multi-Step Project Form ➔ Step 3: Direct Calendar Booking ➔ Step 4: SMS Confirmation',
                        value: '2-Step Instant Quote Funnel (Zip Scope ➔ Project Form ➔ Calendar Booking ➔ Confirmation)'
                    },
                    {
                        icon: '🚨',
                        title: '24/7 Emergency Dispatch Speed-to-Lead Funnel',
                        desc: 'Step 1: Urgent Call Squeeze ➔ Step 2: 60s Auto-Dial Dispatch ➔ Step 3: Address Confirmation ➔ Step 4: Technician ETA Tracking',
                        value: 'Emergency Dispatch Funnel (Urgent Squeeze ➔ Auto-Dial ➔ Address Confirmed ➔ Live ETA)'
                    },
                    {
                        icon: '💵',
                        title: '$500 Off Seasonal Project Voucher Funnel',
                        desc: 'Step 1: Claim $500 Voucher ➔ Step 2: Book Site Inspection ➔ Step 3: Annual Maintenance Plan Upsell (OTO) ➔ Step 4: Voucher Card Delivery',
                        value: 'Seasonal Voucher Funnel (Claim Voucher ➔ Book Estimate ➔ Maintenance Upsell ➔ Voucher Delivery)'
                    },
                    {
                        icon: '🏢',
                        title: 'Commercial Contract B2B Quote Funnel',
                        desc: 'Step 1: Facility Size Assessment ➔ Step 2: Proposal Scope Request ➔ Step 3: Executive Walkthrough Booking ➔ Step 4: Proposal Won',
                        value: 'Commercial Quote Funnel (Facility Scope ➔ Proposal Request ➔ Walkthrough Calendar ➔ Retainer)'
                    }
                ]
            },
            step2_landing: {
                title: 'Step 2: What offer should your Service Landing Page promote?',
                desc: 'Select the primary conversion hook for homeowners and local clients.',
                aiRecIdx: 0,
                aiRecText: 'AI Recommends: Instant Free Quote Calculator produces the highest form completion for local contractors.',
                options: [
                    {
                        icon: '📋',
                        title: 'Instant Free Online Quote / Estimate',
                        desc: 'Fast 4-field lead form: Name, Address, Service Needed & Estimated Budget',
                        value: 'Instant Free Online Quote / Estimate Form (Address & Project Scope)'
                    },
                    {
                        icon: '🛠️',
                        title: 'Free On-Site Inspection & Consultation',
                        desc: 'Direct calendar booking for a licensed technician / estimator site visit',
                        value: 'Free On-Site Inspection & Estimate Booking (GHL Calendar Schedule)'
                    },
                    {
                        icon: '🚨',
                        title: '24/7 Emergency Dispatch Priority Line',
                        desc: 'High-urgency click-to-call routing with automated SMS dispatch confirmation',
                        value: '24/7 Emergency Dispatch Priority Line (Instant SMS & Call Routing)'
                    },
                    {
                        icon: '💵',
                        title: '$500 Off Project / Rebate Voucher',
                        desc: '2-step promotion claiming seasonal rebate or instant coupon savings',
                        value: '$500 Project Rebate / Coupon Voucher Claim (SMS Verification)'
                    }
                ]
            },
            step3: {
                title: 'Step 3: Choose your Home Service Visual Theme',
                desc: 'Select a theme built for local consumer trust, credibility, and verified reviews.',
                aiRecIdx: 0,
                aiRecText: 'AI Recommends: Clean Trust Light theme with security badges maximizes homeowner confidence.',
                options: [
                    {
                        icon: '☀️',
                        title: 'Clean Trust Light (Navy & Crisp White)',
                        desc: 'High credibility, prominent license/insurance badges, customer reviews carousel',
                        value: 'Clean Trust Light (Navy Blue, Safety Badges & Crisp White Layout)'
                    },
                    {
                        icon: '⚡',
                        title: 'High-Urgency Emergency Service',
                        desc: 'High-visibility caution amber/red accents, sticky click-to-call bar, live dispatcher pulse',
                        value: 'High-Urgency Emergency (High-Contrast Amber/Red & Sticky Call Bar)'
                    },
                    {
                        icon: '🏡',
                        title: 'Modern Contractor Blueprint Slate',
                        desc: 'Charcoal slate background, architectural grid accents, before/after project gallery',
                        value: 'Modern Contractor Blueprint Slate (Charcoal & Tech Blue Accents)'
                    },
                    {
                        icon: '🌿',
                        title: 'Eco-Friendly & Energy Modern',
                        desc: 'Clean forest green & sky blue accents, solar savings calculator aesthetics',
                        value: 'Eco-Friendly Modern (Forest Green, Clean White & Energy Stats)'
                    }
                ]
            },
            step4_funnel: {
                title: 'Step 4: Contractor Funnel Automations & Dispatch Workflows',
                desc: 'Deploy automated estimate follow-ups, contractor pipelines, and address tracking.',
                checkboxes: [
                    {
                        id: 'wiz-auto-sms',
                        label: '⚡ Instant SMS with Estimator Dispatch & Photo Upload Link',
                        desc: 'Sends instant SMS confirmation asking homeowner for project photos',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-pipeline',
                        label: '📊 Contractor Funnel Pipeline (Lead ➔ Quote Sent ➔ Deposit ➔ Won)',
                        desc: 'Stages: Quote Requested ➔ Site Visit Set ➔ Quote Sent ➔ Deposit Paid ➔ Completed',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-tag',
                        label: '🏷️ Incomplete Quote Recovery Cadence (T+15m SMS Reminder)',
                        desc: 'Automated SMS nudging homeowners who filled Step 1 address but dropped at Step 2',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-reminders',
                        label: '⏰ 3-Day Automated Estimate Follow-Up & Review Request',
                        desc: 'Follows up on pending quotes and triggers 5-star Google review request on job completion',
                        checked: true
                    }
                ]
            },
            step4_landing: {
                title: 'Step 4: Home Service Automations & Project Fields',
                desc: 'Deploy automated estimate follow-ups, contractor pipelines, and address tracking.',
                checkboxes: [
                    {
                        id: 'wiz-auto-sms',
                        label: '⚡ Instant SMS with Estimator Dispatch & Photo Upload Link',
                        desc: 'Sends instant SMS confirmation asking homeowner for project photos',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-pipeline',
                        label: '📊 Contractor Jobs Pipeline (Quote ➔ Job Won)',
                        desc: 'Stages: Quote Requested ➔ Site Visit Set ➔ Quote Sent ➔ Deposit Paid ➔ Completed',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-tag',
                        label: '🏷️ Property Custom Fields (Address, Square Footage, Urgency)',
                        desc: 'Captures `service_address`, `square_footage`, `property_type`, `timeline`',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-reminders',
                        label: '⏰ 3-Day Automated Estimate Follow-Up & Review Request',
                        desc: 'Follows up on pending quotes and triggers 5-star Google review request on job completion',
                        checked: true
                    }
                ]
            },
            step5: {
                title: 'Step 5: Contractor Brand Customization',
                desc: 'Personalize with your company details or use the AI-tailored home service defaults.',
                brandNamePlaceholder: 'e.g. Apex Home & Roofing Solutions',
                taglinePlaceholder: 'e.g. Licensed, Insured & Trusted Local Experts — Free Estimates',
                defaultBrandName: 'Apex Home Solutions',
                defaultTagline: 'Top-Rated Local Home Services — Free 60-Second Estimate',
                defaultColor: '#2563eb',
                colorPresets: ['#2563eb', '#0284c7', '#16a34a', '#d97706', '#dc2626', '#475569']
            }
        },
        'b2b-agency': {
            key: 'b2b-agency',
            name: 'B2B Agency & Consulting',
            icon: '💼',
            matchKeywords: ['agency', 'b2b', 'consulting', 'consultant', 'marketing', 'saas', 'software', 'lead generation', 'strategy call', 'client acquisition'],
            step2_funnel: {
                title: 'Step 2: Choose your B2B Multi-Step Funnel Flow',
                desc: 'Select the high-converting client acquisition funnel structure.',
                aiRecIdx: 0,
                aiRecText: 'AI Recommends: VSL & High-Ticket Application Funnel qualifies prospects and closes $5k-$20k retainers.',
                options: [
                    {
                        icon: '🎬',
                        title: 'VSL & High-Ticket Application Funnel',
                        desc: 'Step 1: Case Study VSL ➔ Step 2: 7-Question Revenue Audit ➔ Step 3: Discovery Call Calendar ➔ Step 4: Pre-Call Briefing ➔ Step 5: Retainer Won',
                        value: 'VSL & High-Ticket Application Funnel (Case Study VSL ➔ Qualification Survey ➔ Calendar Booking ➔ Retainer Won)'
                    },
                    {
                        icon: '🎁',
                        title: 'Free Growth Audit & Lead Magnet Funnel',
                        desc: 'Step 1: Opt-in for Custom Growth Audit ➔ Step 2: Instant Loom Video Audit Landing ➔ Step 3: Strategy Call Booking ➔ Step 4: Thank You',
                        value: 'Free Growth Audit Funnel (Opt-in ➔ Video Audit ➔ Strategy Calendar ➔ Confirmation)'
                    },
                    {
                        icon: '💻',
                        title: 'SaaS Free Trial & Interactive Demo Funnel',
                        desc: 'Step 1: Interactive Product Tour ➔ Step 2: 14-Day Free Trial Account Setup ➔ Step 3: Onboarding Sequence ➔ Step 4: Annual Plan Upgrade',
                        value: 'SaaS Interactive Demo Funnel (Product Tour ➔ Trial Setup ➔ Onboarding Flow ➔ Paid Upgrade)'
                    },
                    {
                        icon: '🚀',
                        title: 'Mini-Workshop / Masterclass Funnel',
                        desc: 'Step 1: $27 Workshop Ticket Squeeze ➔ Step 2: 1-Click Agency SOP Bundle Upsell ($97) ➔ Step 3: Live Zoom Room ➔ Step 4: Retainer Pitch',
                        value: 'Mini-Workshop Funnel ($27 Ticket ➔ $97 SOP Upsell ➔ Workshop Room ➔ Retainer Pitch)'
                    }
                ]
            },
            step2_landing: {
                title: 'Step 2: What is your B2B Landing Page Conversion Goal?',
                desc: 'Select the primary CTA for your agency or consulting firm.',
                aiRecIdx: 0,
                aiRecText: 'AI Recommends: 30-Min Strategy Call with qualifying questionnaire converts best for high-ticket B2B.',
                options: [
                    {
                        icon: '📅',
                        title: 'Free 30-Min Growth Strategy Audit',
                        desc: 'Direct calendar booking with embedded 4-question qualification survey',
                        value: 'Free 30-Min Growth Strategy Audit (GHL Embedded Calendar + Survey)'
                    },
                    {
                        icon: '🎁',
                        title: 'High-Value Lead Magnet / PDF Case Study',
                        desc: 'Low-friction opt-in delivering proprietary playbook or industry benchmark study',
                        value: 'High-Value Lead Magnet / Proprietary Playbook Download (Instant SMS/Email)'
                    },
                    {
                        icon: '💻',
                        title: 'Live Interactive SaaS Demo Booking',
                        desc: 'Tailored demo calendar booking with team size & current tech stack capture',
                        value: 'Live Interactive SaaS Demo Booking (GHL Calendar + Tech Stack Fields)'
                    },
                    {
                        icon: '🚀',
                        title: 'Full Retainer Proposal Request',
                        desc: 'Multi-step qualification form capturing monthly ad spend & revenue goals',
                        value: 'Full Retainer Proposal Request (Multi-Step Revenue Qualification Form)'
                    }
                ]
            },
            step3: {
                title: 'Step 3: Choose your B2B Agency Aesthetic',
                desc: 'Select an enterprise-grade visual theme that commands $5k-$20k retainer fees.',
                aiRecIdx: 0,
                aiRecText: 'AI Recommends: Tech-Forward Dark Glassmorphism positions your firm as elite and modern.',
                options: [
                    {
                        icon: '🌙',
                        title: 'Tech-Forward Dark Glassmorphism',
                        desc: 'Deep indigo/black background, frosted glass panels, glowing purple gradients',
                        value: 'Tech-Forward Dark Glassmorphism (Deep Indigo & Violet Glow Gradients)'
                    },
                    {
                        icon: '💼',
                        title: 'Corporate Enterprise Slate & Platinum',
                        desc: 'Clean corporate light/slate, serif accents, client logo wall & ROI stat counters',
                        value: 'Corporate Enterprise Slate (Monochrome, Client Proof Grid & Crisp Typography)'
                    },
                    {
                        icon: '⚡',
                        title: 'High-Impact Metric & Case Study Driven',
                        desc: 'Bold headline typography, highlighted revenue metrics, video testimonial embeds',
                        value: 'High-Impact Metric Driven (Bold Revenue Proof, Video Testimonials)'
                    },
                    {
                        icon: '💎',
                        title: 'Silicon Valley Minimalist',
                        desc: 'Airy whitespace, elegant micro-animations, ultra-clean product mockup frames',
                        value: 'Silicon Valley Minimalist (Clean Whitespace, Elegant Micro-Interactions)'
                    }
                ]
            },
            step4_funnel: {
                title: 'Step 4: B2B Funnel Automations & Application Triage',
                desc: 'Deploy deal pipelines, qualification triggers, and pre-call homework sequences.',
                checkboxes: [
                    {
                        id: 'wiz-auto-sms',
                        label: '⚡ Instant Strategy Session SMS + Pre-Call Case Study Dossier',
                        desc: 'Dispatches Google Calendar invite & executive breakdown to maximize show-up rates',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-pipeline',
                        label: '📊 High-Ticket B2B Funnel Pipeline (Opt-in ➔ Audit ➔ Proposal ➔ Closed)',
                        desc: 'Stages: Inbound Lead ➔ Discovery Set ➔ Audit Presented ➔ Proposal Sent ➔ Won',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-tag',
                        label: '🏷️ Application Drop-off Recovery (T+15m Automated Nudge)',
                        desc: 'Sends instant follow-up to leads who started the qualification survey but did not finish',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-reminders',
                        label: '⏰ 24h & 1h Pre-Call SMS Reminders + No-Show Auto-Reschedule',
                        desc: 'Automated multi-channel reminders ensuring 85%+ show-up rates for strategy calls',
                        checked: true
                    }
                ]
            },
            step4_landing: {
                title: 'Step 4: B2B Pipeline, Intake Survey & Workflow Triggers',
                desc: 'Deploy GoHighLevel deal pipelines, calendar booking automations, and CRM fields.',
                checkboxes: [
                    {
                        id: 'wiz-auto-sms',
                        label: '⚡ Instant Strategy Session Confirmation SMS + Pre-Call Prep Email',
                        desc: 'Dispatches Google Calendar invite & case study link to maximize show-up rates',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-pipeline',
                        label: '📊 B2B Deal Pipeline (Discovery ➔ Audit ➔ Contract Signed)',
                        desc: 'Stages: Inbound Lead ➔ Discovery Set ➔ Audit Presented ➔ Proposal Sent ➔ Won',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-tag',
                        label: '🏷️ B2B Qualification Fields (Revenue, Ad Spend, Team Size)',
                        desc: 'Captures `monthly_revenue`, `current_ad_spend`, `team_size`, `primary_bottleneck`',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-reminders',
                        label: '⏰ 24h & 1h Pre-Call SMS Reminders + No-Show Auto-Reschedule',
                        desc: 'Automated multi-channel reminders ensuring 85%+ show-up rates for strategy calls',
                        checked: true
                    }
                ]
            },
            step5: {
                title: 'Step 5: Agency Brand Customization',
                desc: 'Personalize with your agency details or use the AI-tailored B2B defaults.',
                brandNamePlaceholder: 'e.g. ScalePoint Growth Partners',
                taglinePlaceholder: 'e.g. We Scale B2B Companies from $1M to $10M ARR',
                defaultBrandName: 'ScalePoint Agency',
                defaultTagline: 'Predictable Pipeline & Revenue Growth for Modern B2B Brands',
                defaultColor: '#6366f1',
                colorPresets: ['#6366f1', '#0ea5e9', '#8b5cf6', '#3b82f6', '#10b981', '#0f172a']
            }
        },
        'coaching': {
            key: 'coaching',
            name: 'Coaching & Digital Product',
            icon: '🎓',
            matchKeywords: ['coach', 'coaching', 'course', 'masterclass', 'webinar', 'vsl', 'infoproduct', 'consultant', 'mentor', 'mentorship'],
            step2_funnel: {
                title: 'Step 2: Choose your Coaching Multi-Step Funnel Flow',
                desc: 'Select the high-converting conversion funnel structure for your program.',
                aiRecIdx: 0,
                aiRecText: 'AI Recommends: 2-Step VSL Funnel with Application Booking yields the highest ROI for $3k-$10k coaching.',
                options: [
                    {
                        icon: '🎬',
                        title: '2-Step VSL (Video Sales Letter) ➔ Application Funnel',
                        desc: 'Step 1: 15-Min Breakthrough VSL ➔ Step 2: 8-Question Application ➔ Step 3: Strategy Calendar Booking ➔ Step 4: Confirmation',
                        value: '2-Step VSL Funnel (Breakthrough VSL ➔ Application Form ➔ Strategy Calendar ➔ Confirmation)'
                    },
                    {
                        icon: '🎟️',
                        title: 'Automated Masterclass / Webinar Funnel',
                        desc: 'Step 1: Registration Page ➔ Step 2: Dynamic Countdown Room ➔ Step 3: Broadcast/Replay Page ➔ Step 4: 2-Step Checkout ➔ Step 5: Portal Access',
                        value: 'Automated Masterclass Funnel (Registration ➔ Countdown Room ➔ Replay Room ➔ Checkout ➔ Member Portal)'
                    },
                    {
                        icon: '🛒',
                        title: 'Free Book / Tripwire Order Form Funnel',
                        desc: 'Step 1: Free Book (+S&H $7.95) 2-Step Order Form ➔ Step 2: Audio Masterclass Upsell ($37) ➔ Step 3: Mastermind OTO ($97/mo) ➔ Step 4: Receipt',
                        value: 'Tripwire Order Form Funnel (Free Book S&H ➔ $37 Audio Upsell ➔ $97/mo Mastermind OTO ➔ Receipt)'
                    },
                    {
                        icon: '🏆',
                        title: '5-Day Live Challenge Funnel',
                        desc: 'Step 1: Free Challenge Opt-in ➔ Step 2: VIP WhatsApp/SMS Group ➔ Step 3: Daily Training Room ➔ Step 4: VIP Pass Upsell ➔ Step 5: Pitch Day',
                        value: '5-Day Live Challenge Funnel (Opt-in ➔ VIP Group ➔ Challenge Room ➔ VIP Pass Upsell ➔ Pitch Day)'
                    }
                ]
            },
            step2_landing: {
                title: 'Step 2: What is your Coaching Landing Page Offer?',
                desc: 'Select the primary conversion hook for your coaching program.',
                aiRecIdx: 0,
                aiRecText: 'AI Recommends: 2-Step VSL Funnel with Application Booking yields the highest ROI for $3k-$10k coaching.',
                options: [
                    {
                        icon: '🎬',
                        title: '2-Step VSL (Video Sales Letter) ➔ Application',
                        desc: 'Step 1: Watch 15-min masterclass video ➔ Step 2: Fill out breakthrough application',
                        value: '2-Step VSL Funnel (Video Sales Letter ➔ Application Booking Form)'
                    },
                    {
                        icon: '🎟️',
                        title: 'Live Workshop / Webinar Registration',
                        desc: 'Countdown timer registration page with SMS seat reservation & calendar sync',
                        value: 'Live Workshop / Webinar Registration (Countdown Timer & SMS Calendar Sync)'
                    },
                    {
                        icon: '🛒',
                        title: 'Low-Ticket Tripwire ($27-$97) with Order Bump',
                        desc: 'Direct checkout with 1-click order bump & high-ticket VSL upsell sequence',
                        value: 'Low-Ticket Tripwire Offer (Order Bump & 1-Click Upsell Flow)'
                    },
                    {
                        icon: '📱',
                        title: '1-on-1 Breakthrough Mentorship Call',
                        desc: 'High-ticket application filter: Income goals, commitment level & direct calendar',
                        value: '1-on-1 Breakthrough Mentorship Call (Income Qualification & Calendar)'
                    }
                ]
            },
            step3: {
                title: 'Step 3: Choose your Authority Visual Theme',
                desc: 'Select an aesthetic designed to establish personal authority and elite positioning.',
                aiRecIdx: 0,
                aiRecText: 'AI Recommends: Luxury Authority Slate theme with emerald/gold accents justifies premium pricing.',
                options: [
                    {
                        icon: '💎',
                        title: 'Luxury Authority Slate & Emerald',
                        desc: 'Rich matte charcoal, subtle emerald/gold accents, elegant serif typography, founder hero',
                        value: 'Luxury Authority Slate (Charcoal, Emerald/Gold & Serif Headlines)'
                    },
                    {
                        icon: '⚡',
                        title: 'High-Converting Direct Response',
                        desc: 'Urgency countdown bar, vibrant CTA buttons, scarcity badges, extensive proof gallery',
                        value: 'High-Converting Direct Response (Sticky Countdown Bar, Scarcity Tags)'
                    },
                    {
                        icon: '🌙',
                        title: 'Modern Creator Dark Aesthetic',
                        desc: 'Podcast/YouTube aesthetic, dark background, glowing video player frame, student reviews',
                        value: 'Modern Creator Dark (Dark Mode, Glowing Media Player, Student Wall)'
                    },
                    {
                        icon: '☀️',
                        title: 'Clean Academic & Workshop Light',
                        desc: 'Crisp whites, educational syllabus breakdown cards, structured module preview',
                        value: 'Clean Academic Light (Structured Syllabus Grid, Clean White & Blue)'
                    }
                ]
            },
            step4_funnel: {
                title: 'Step 4: Coaching Funnel Automations, Cart Recovery & Member Delivery',
                desc: 'Deploy course delivery triggers, student qualification fields, and replay sequences.',
                checkboxes: [
                    {
                        id: 'wiz-auto-sms',
                        label: '⚡ Instant VSL / Webinar Access SMS with Magic Video Link',
                        desc: 'Sends magic link to watch training immediately + SMS workbook download',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-pipeline',
                        label: '📊 Coaching Enrollment Pipeline (Application ➔ Enrolled)',
                        desc: 'Stages: App Submitted ➔ Qualified ➔ Strategy Call Held ➔ Offer Made ➔ Enrolled Won',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-tag',
                        label: '🛒 2-Step Order Form Cart Abandonment Sequence (T+15m, 4h, 24h)',
                        desc: 'Automated SMS/Email sequence recovering uncompleted tripwire checkouts',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-reminders',
                        label: '⏰ 24-Hour Evergreen Replay & Urgency Follow-up Cadence',
                        desc: 'Automated 4-part email/SMS series closing enrollment before timer expires',
                        checked: true
                    }
                ]
            },
            step4_landing: {
                title: 'Step 4: Coaching Pipeline, Portal Access & Nurture Workflows',
                desc: 'Deploy course delivery triggers, student qualification fields, and replay sequences.',
                checkboxes: [
                    {
                        id: 'wiz-auto-sms',
                        label: '⚡ Instant VSL / Webinar Access SMS with Personal Video Link',
                        desc: 'Sends magic link to watch training immediately + SMS workbook download',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-pipeline',
                        label: '📊 Coaching Enrollment Pipeline (Application ➔ Enrolled)',
                        desc: 'Stages: App Submitted ➔ Qualified ➔ Strategy Call Held ➔ Offer Made ➔ Enrolled Won',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-tag',
                        label: '🏷️ Student Intake Fields (Annual Target, Roadblocks, Budget)',
                        desc: 'Captures `annual_income_goal`, `biggest_obstacle`, `investment_readiness`',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-reminders',
                        label: '⏰ 24-Hour Evergreen Replay & Urgency Follow-up Cadence',
                        desc: 'Automated 4-part email/SMS series closing enrollment before timer expires',
                        checked: true
                    }
                ]
            },
            step5: {
                title: 'Step 5: Coaching Brand Customization',
                desc: 'Personalize with your brand details or use the AI-tailored coaching defaults.',
                brandNamePlaceholder: 'e.g. Mastermind Coaching Academy',
                taglinePlaceholder: 'e.g. Master High-Ticket Client Acquisition in 60 Days',
                defaultBrandName: 'Mastermind Coaching Academy',
                defaultTagline: 'Scale Your Expertise into a 7-Figure Online Coaching Business',
                defaultColor: '#059669',
                colorPresets: ['#059669', '#d97706', '#8b5cf6', '#2563eb', '#dc2626', '#0f172a']
            }
        },
        'real-estate': {
            key: 'real-estate',
            name: 'Real Estate & Property',
            icon: '🏠',
            matchKeywords: ['real estate', 'property', 'realtor', 'home buyer', 'home seller', 'mortgage', 'open house', 'listing', 'luxury estate', 'foreclosure'],
            step2_funnel: {
                title: 'Step 2: Choose your Real Estate Multi-Step Funnel Flow',
                desc: 'Select the high-converting lead funnel flow for buyers, sellers, or investors.',
                aiRecIdx: 0,
                aiRecText: 'AI Recommends: VIP Property Tour & Showing Funnel converts 4.1x better than standard forms.',
                options: [
                    {
                        icon: '🏡',
                        title: 'VIP Luxury Property Tour & Showing Funnel',
                        desc: 'Step 1: Video Walkthrough Squeeze ➔ Step 2: Private Showing Booking Calendar ➔ Step 3: Pre-Approval Verification ➔ Step 4: Tour Confirmed',
                        value: 'Luxury Property Tour Funnel (Walkthrough Squeeze ➔ Showing Calendar ➔ Pre-Approval ➔ Tour Confirmed)'
                    },
                    {
                        icon: '📑',
                        title: '2-Step Instant Home Valuation & CMA Funnel',
                        desc: 'Step 1: Property Address Capture ➔ Step 2: Condition & Beds/Baths Form ➔ Step 3: Automated SMS CMA Report ➔ Step 4: Listing Consultation Booking',
                        value: 'Home Valuation Funnel (Address Capture ➔ Condition Specs ➔ Instant CMA ➔ Listing Consultation)'
                    },
                    {
                        icon: '🔑',
                        title: 'Off-Market & Foreclosure Deal List Funnel',
                        desc: 'Step 1: Exclusive Deals Squeeze ➔ Step 2: Budget & Neighborhood Filter ➔ Step 3: VIP SMS List Delivery ➔ Step 4: Buyer Consultation Call',
                        value: 'Off-Market Deal List Funnel (Exclusive Squeeze ➔ Filter Criteria ➔ SMS Delivery ➔ Buyer Consultation)'
                    },
                    {
                        icon: '🎓',
                        title: 'First-Time Homebuyer Masterclass Funnel',
                        desc: 'Step 1: Free Buyer Guide Squeeze ➔ Step 2: 12-Min Video Class ➔ Step 3: Mortgage Pre-Approval Application ➔ Step 4: Buyer Won',
                        value: 'First-Time Buyer Funnel (Guide Squeeze ➔ Video Class ➔ Mortgage App ➔ Buyer Retained)'
                    }
                ]
            },
            step2_landing: {
                title: 'Step 2: What is your Real Estate Lead Offer?',
                desc: 'Select the high-converting hook for buyers, sellers, or investors.',
                aiRecIdx: 0,
                aiRecText: 'AI Recommends: VIP Property Tour / Open House Booking converts 4.1x better than generic contact forms.',
                options: [
                    {
                        icon: '🏡',
                        title: 'VIP Private Property Tour Booking',
                        desc: 'Interactive calendar to schedule an in-person or virtual luxury walkthrough',
                        value: 'VIP Private Property Tour Booking (Embedded GHL Tour Calendar)'
                    },
                    {
                        icon: '📑',
                        title: 'Instant Free Home Valuation (CMA Report)',
                        desc: 'Capture address & property specs to generate a Comparative Market Analysis',
                        value: 'Instant Free Home Valuation & CMA Report (Address & Beds/Baths Fields)'
                    },
                    {
                        icon: '🔑',
                        title: 'Exclusive Off-Market & Foreclosure List',
                        desc: 'Instant digital access to unlisted properties and price-reduced neighborhood deals',
                        value: 'Exclusive Off-Market & Foreclosure Deal List (SMS Digital Access)'
                    },
                    {
                        icon: '📞',
                        title: '1-on-1 Buyer / Relocation Consultation',
                        desc: 'Schedule a discovery call with top local neighborhood specialists',
                        value: '1-on-1 Buyer / Relocation Strategy Consultation (GHL Calendar)'
                    }
                ]
            },
            step3: {
                title: 'Step 3: Choose your Real Estate Visual Theme',
                desc: 'Select an aesthetic that showcases high-end properties and local neighborhood prestige.',
                aiRecIdx: 0,
                aiRecText: 'AI Recommends: Luxury Architectural Slate with gold accents elevates property perceived value.',
                options: [
                    {
                        icon: '💎',
                        title: 'Luxury Architectural Slate & Gold',
                        desc: 'High-res photography showcase, subtle gold trim, elegant editorial font styling',
                        value: 'Luxury Architectural Slate (Charcoal, Gold Highlights & High-Res Gallery)'
                    },
                    {
                        icon: '☀️',
                        title: 'Clean Suburban Bright & Inviting',
                        desc: 'Warm welcoming white & navy palette, neighborhood guide badges, family-first appeal',
                        value: 'Clean Suburban Bright (Warm Whites, Coastal Navy & Neighborhood Map)'
                    },
                    {
                        icon: '🌙',
                        title: 'Modern Penthouse Dark Mode',
                        desc: 'Sleek dark theme with floorplan toggle, 3D tour embeds, luxury black marble feel',
                        value: 'Modern Penthouse Dark (Dark Mode, 3D Virtual Tour Embeds & Floorplans)'
                    },
                    {
                        icon: '⚡',
                        title: 'Fast Cash Buyer Direct Response',
                        desc: 'High-contrast "We Buy Houses for Cash As-Is" direct response with fast-cash form',
                        value: 'Fast Cash Buyer Direct Response (High Contrast Amber/Green Cash Offer Form)'
                    }
                ]
            },
            step4_funnel: {
                title: 'Step 4: Real Estate Funnel Automations & Tour Follow-Up',
                desc: 'Deploy property pipelines, automated listing alerts, and mortgage qualification fields.',
                checkboxes: [
                    {
                        id: 'wiz-auto-sms',
                        label: '⚡ Instant Property Spec Sheet & Virtual Tour Video SMS',
                        desc: 'Sends instant text with property brochure PDF & agent digital business card',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-pipeline',
                        label: '📊 Real Estate Funnel Pipeline (Lead ➔ Tour ➔ Offer ➔ Escrow)',
                        desc: 'Stages: Inbound Lead ➔ Tour Scheduled ➔ Tour Completed ➔ Offer Made ➔ Closed Escrow',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-tag',
                        label: '🏷️ Incomplete Valuation Recovery Cadence (T+15m SMS)',
                        desc: 'Nudges sellers who entered their address on Step 1 but dropped before submitting specs',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-reminders',
                        label: '⏰ Automated Price Drop & New Neighborhood Listing Alerts',
                        desc: 'Weekly automated SMS/email alerts keeping buyers engaged until they transact',
                        checked: true
                    }
                ]
            },
            step4_landing: {
                title: 'Step 4: Real Estate CRM Pipeline & Buyer/Seller Taxonomy',
                desc: 'Deploy property pipelines, automated listing alerts, and mortgage qualification fields.',
                checkboxes: [
                    {
                        id: 'wiz-auto-sms',
                        label: '⚡ Instant Property Spec Sheet & Virtual Tour Video SMS',
                        desc: 'Sends instant text with property brochure PDF & agent digital business card',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-pipeline',
                        label: '📊 Real Estate Pipeline (Lead ➔ Tour ➔ Offer ➔ Escrow)',
                        desc: 'Stages: Inbound Lead ➔ Tour Scheduled ➔ Tour Completed ➔ Offer Made ➔ Closed Escrow',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-tag',
                        label: '🏷️ Buyer/Seller Custom Fields (Pre-Approval, Budget, Beds)',
                        desc: 'Captures `buyer_budget`, `pre_approval_status`, `desired_bedrooms`, `move_in_timeline`',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-reminders',
                        label: '⏰ Automated Price Drop & New Neighborhood Listing Alerts',
                        desc: 'Weekly automated SMS/email alerts keeping buyers engaged until they transact',
                        checked: true
                    }
                ]
            },
            step5: {
                title: 'Step 5: Real Estate Brand Customization',
                desc: 'Personalize with your agency details or use the AI-tailored real estate defaults.',
                brandNamePlaceholder: 'e.g. Apex Luxury Real Estate Group',
                taglinePlaceholder: 'e.g. Find Your Dream Luxury Home in Prime Neighborhoods',
                defaultBrandName: 'Apex Real Estate Group',
                defaultTagline: 'Exclusive Luxury Homes & Off-Market Properties',
                defaultColor: '#0284c7',
                colorPresets: ['#0284c7', '#0f172a', '#d97706', '#059669', '#3b82f6', '#475569']
            }
        },
        'ecommerce': {
            key: 'ecommerce',
            name: 'E-Commerce & DTC',
            icon: '🛍️',
            matchKeywords: ['ecommerce', 'e-commerce', 'dtc', 'product launch', 'shopify', 'store', 'shop', 'flash sale', 'cart', 'retail'],
            step2_funnel: {
                title: 'Step 2: Choose your E-Commerce Multi-Step Funnel Flow',
                desc: 'Select the high-converting product sales funnel progression with order bumps & 1-click upsells.',
                aiRecIdx: 0,
                aiRecText: 'AI Recommends: 2-Step Order Form & 1-Click Upsell Funnel produces the highest Average Order Value (AOV).',
                options: [
                    {
                        icon: '🛒',
                        title: '2-Step Order Form & 1-Click Upsell Funnel',
                        desc: 'Step 1: Product Showcase Lander ➔ Step 2: 2-Step Checkout (with Order Bump) ➔ Step 3: 1-Click Post-Purchase Upsell (OTO 1) ➔ Step 4: Downsell ➔ Step 5: Receipt',
                        value: '2-Step Order Form & Upsell Funnel (Lander ➔ 2-Step Order Bump ➔ 1-Click Upsell ➔ Downsell ➔ Receipt)'
                    },
                    {
                        icon: '📦',
                        title: 'Free-Plus-Shipping Product Launch Funnel',
                        desc: 'Step 1: Hero Unboxing Video ➔ Step 2: Claim Free Sample ($6.95 S&H) ➔ Step 3: 3-Pack Bundle Upsell ($29) ➔ Step 4: VIP Auto-Refill Subscription ➔ Step 5: Thank You',
                        value: 'Free + Shipping Launch Funnel (Unboxing Video ➔ Free Sample Checkout ➔ Bundle Upsell ➔ VIP Subscription)'
                    },
                    {
                        icon: '✨',
                        title: 'Interactive Recommendation Quiz Funnel',
                        desc: 'Step 1: 5-Question Lifestyle/Routine Quiz ➔ Step 2: Personalized Regimen Results Page ➔ Step 3: 1-Click Custom Bundle Checkout ➔ Step 4: VIP Club Upsell',
                        value: 'Interactive Quiz Funnel (5-Question Quiz ➔ Custom Routine Results ➔ Bundle Checkout ➔ VIP Club)'
                    },
                    {
                        icon: '🔥',
                        title: 'VIP Flash Sale & Early Access Vault Funnel',
                        desc: 'Step 1: Secret VIP Access Squeeze ➔ Step 2: 24h Countdown Vault Page ➔ Step 3: Fast-Checkout Order Form ➔ Step 4: Mystery Gift Upsell',
                        value: 'VIP Flash Sale Funnel (VIP Pass Squeeze ➔ Countdown Vault ➔ Fast Checkout ➔ Mystery Upsell)'
                    }
                ]
            },
            step2_landing: {
                title: 'Step 2: What is your E-Commerce Conversion Goal?',
                desc: 'Select the primary purchasing or discount capture mechanism for your store.',
                aiRecIdx: 0,
                aiRecText: 'AI Recommends: 15% Off First Order SMS & Email Capture drives 2.8x higher immediate checkout.',
                options: [
                    {
                        icon: '🎁',
                        title: '15% Off VIP Welcome Coupon & SMS Club',
                        desc: 'High-converting discount unlock form capturing phone & email before purchase',
                        value: '15% Off VIP Welcome Coupon (Instant SMS Discount Code Delivery)'
                    },
                    {
                        icon: '🛒',
                        title: 'Single-Product Hero Showcase Page',
                        desc: 'High-converting direct-to-checkout landing page with quantity bundles & sticky Buy bar',
                        value: 'Single-Product Hero Showcase (Bundle Selection & 1-Click Fast Checkout)'
                    },
                    {
                        icon: '🛍️',
                        title: 'VIP Product Drop / Pre-Order Waitlist',
                        desc: 'Build massive anticipation with countdown timer & VIP early-bird SMS reservation',
                        value: 'VIP Product Drop Waitlist (Countdown Timer & Early Access VIP List)'
                    },
                    {
                        icon: '📦',
                        title: 'Free Sample / "Free + Shipping" Page',
                        desc: 'Low-barrier trial offer capturing customer info with 1-click upsell sequence',
                        value: 'Free + Shipping Introductory Offer (2-Step Checkout with Post-Purchase Upsell)'
                    }
                ]
            },
            step3: {
                title: 'Step 3: Choose your DTC Brand Aesthetic',
                desc: 'Select an aesthetic tailored to your product category and lifestyle appeal.',
                aiRecIdx: 0,
                aiRecText: 'AI Recommends: Bold Flash Sale Direct Response drives highest impulse purchasing.',
                options: [
                    {
                        icon: '⚡',
                        title: 'Bold High-Conversion Flash Sale',
                        desc: 'High contrast, live inventory stock counters, sticky Add to Cart bar, trust guarantee badges',
                        value: 'Bold High-Conversion Flash Sale (Sticky Cart Bar, Inventory Countdowns)'
                    },
                    {
                        icon: '🌸',
                        title: 'Clean Beauty & Lifestyle Aesthetic',
                        desc: 'Soft pastel tones, Instagram UGC photo grid, clean skincare/fashion typography',
                        value: 'Clean Beauty & Lifestyle (Pastel Tones, UGC Photo Grid & Clean Sans)'
                    },
                    {
                        icon: '🌙',
                        title: 'Dark Cyberpunk / Tech Gadget DTC',
                        desc: 'RGB neon border accents, dark sleek background, technical feature breakdown cards',
                        value: 'Dark Cyberpunk Tech (Matte Black, RGB Neon Glow & Spec Cards)'
                    },
                    {
                        icon: '🌿',
                        title: 'Organic & Sustainable Earth Tones',
                        desc: 'Natural warm clay & forest green, clean recycled badges, ingredient transparency cards',
                        value: 'Organic & Sustainable (Earth Tones, Eco Badges & Ingredient Cards)'
                    }
                ]
            },
            step4_funnel: {
                title: 'Step 4: E-Com Funnel Automations, Abandoned Cart & Upsell Triggers',
                desc: 'Deploy GoHighLevel 2-step cart recovery workflows, 1-click upsell fulfillments, and purchase triggers.',
                checkboxes: [
                    {
                        id: 'wiz-auto-sms',
                        label: '⚡ 3-Touch Abandoned Cart Recovery Sequence (T+15m, 4h, 24h)',
                        desc: 'Recovers up to 28% of abandoned checkouts with dynamic urgency discount incentives',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-pipeline',
                        label: '📊 E-Com Funnel Pipeline (Step 1 Cart ➔ Checkout ➔ Upsell Taken ➔ VIP)',
                        desc: 'Stages: Cart Started ➔ Order Complete ➔ Upsell Taken ➔ Shipped ➔ VIP Repeat Buyer',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-tag',
                        label: '🏷️ 1-Click Upsell (OTO) Trigger & Fulfillment Workflow',
                        desc: 'Instantly processes Stripe one-click charge and updates warehouse shipment queue',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-reminders',
                        label: '⏰ VIP Post-Purchase Review & Referral Automation',
                        desc: 'Automated SMS dispatched 7 days after delivery asking for photo review and referral bonus',
                        checked: true
                    }
                ]
            },
            step4_landing: {
                title: 'Step 4: E-Commerce Automations & Abandoned Cart Recovery',
                desc: 'Deploy GoHighLevel cart recovery workflows, VIP tags, and purchase triggers.',
                checkboxes: [
                    {
                        id: 'wiz-auto-sms',
                        label: '⚡ Instant VIP Discount Code SMS (Dispatched in < 30 seconds)',
                        desc: 'Sends unique coupon code with 1-click cart autofill link via SMS',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-pipeline',
                        label: '📊 E-Com Customer Pipeline (Cart ➔ Purchased ➔ VIP)',
                        desc: 'Stages: Cart Started ➔ Checkout Complete ➔ Shipped ➔ VIP Repeat Buyer',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-tag',
                        label: '🏷️ Customer Preference Fields (Category Interest, Skin/Size)',
                        desc: 'Captures `product_interest`, `birthday_month`, `size_preference`, `vip_tier`',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-reminders',
                        label: '⏰ 3-Touch Abandoned Cart Recovery Sequence (T+15m, 4h, 24h)',
                        desc: 'Recovers up to 28% of abandoned checkouts with dynamic urgency discount incentives',
                        checked: true
                    }
                ]
            },
            step5: {
                title: 'Step 5: DTC Brand Customization',
                desc: 'Personalize with your store details or use the AI-tailored e-commerce defaults.',
                brandNamePlaceholder: 'e.g. Lumina Luxe Essentials',
                taglinePlaceholder: 'e.g. Premium Daily Essentials Engineered for Modern Living',
                defaultBrandName: 'Lumina Essentials',
                defaultTagline: 'Engineered for Performance & Everyday Luxury',
                defaultColor: '#ec4899',
                colorPresets: ['#ec4899', '#8b5cf6', '#0ea5e9', '#10b981', '#f59e0b', '#0f172a']
            }
        },
        'restaurant': {
            key: 'restaurant',
            name: 'Restaurant & Hospitality',
            icon: '🍽️',
            matchKeywords: ['restaurant', 'cafe', 'bistro', 'bar', 'hospitality', 'food', 'dining', 'catering', 'bakery', 'pub', 'reservation'],
            step2_funnel: {
                title: 'Step 2: Choose your Restaurant Multi-Step Funnel Flow',
                desc: 'Select the high-converting dining or event reservation progression.',
                aiRecIdx: 0,
                aiRecText: 'AI Recommends: VIP Birthday & Celebration Club Funnel drives predictable weekly covers.',
                options: [
                    {
                        icon: '🎂',
                        title: 'VIP Birthday & Celebration Club Funnel',
                        desc: 'Step 1: Free Birthday Entrée Squeeze ➔ Step 2: Instant SMS Voucher Wallet Card ➔ Step 3: Table Reservation Calendar ➔ Step 4: Birthday Confirmed',
                        value: 'Birthday Club Funnel (Birthday Squeeze ➔ SMS Wallet Voucher ➔ Reservation Calendar ➔ Confirmed)'
                    },
                    {
                        icon: '🥂',
                        title: 'Private Dining & Event Catering Funnel',
                        desc: 'Step 1: Event Space Showcase Lander ➔ Step 2: Guest Count & Menu Selector ➔ Step 3: Event Coordinator Calendar Booking ➔ Step 4: Proposal Won',
                        value: 'Private Event Catering Funnel (Event Showcase ➔ Menu Selector ➔ Coordinator Calendar ➔ Deposit Won)'
                    },
                    {
                        icon: '🍷',
                        title: 'Chef Tasting Night & Ticketed Dinner Funnel',
                        desc: 'Step 1: Exclusive Tasting Menu Lander ➔ Step 2: Seat Ticket Checkout ➔ Step 3: 1-Click Wine Pairing Upsell ($45) ➔ Step 4: Digital Pass Receipt',
                        value: 'Tasting Night Funnel (Tasting Lander ➔ Seat Checkout ➔ Wine Pairing Upsell ➔ Ticket Pass)'
                    },
                    {
                        icon: '📱',
                        title: 'Online Takeout & Loyalty App Funnel',
                        desc: 'Step 1: $10 Off First Order Squeeze ➔ Step 2: Online Menu Selector ➔ Step 3: Direct Pickup/Delivery Checkout ➔ Step 4: 7-Day Reorder Automation',
                        value: 'Takeout Loyalty Funnel ($10 Squeeze ➔ Menu Selector ➔ Takeout Checkout ➔ Reorder Automation)'
                    }
                ]
            },
            step2_landing: {
                title: 'Step 2: What is your Restaurant Conversion Offer?',
                desc: 'Select the primary reservation or dining incentive hook.',
                aiRecIdx: 0,
                aiRecText: 'AI Recommends: VIP Table Reservation with Instant Confirmation produces the highest guest booking rate.',
                options: [
                    {
                        icon: '🍽️',
                        title: 'Online VIP Table Reservation Booking',
                        desc: 'Select party size, date, time slot & seating preference with instant SMS confirmation',
                        value: 'Online VIP Table Reservation Booking (Party Size, Time & GHL Calendar)'
                    },
                    {
                        icon: '🎟️',
                        title: '$15 Off Dinner / Free Appetizer Voucher',
                        desc: 'High-converting dine-in voucher claimed via SMS & delivered to digital wallet',
                        value: '$15 Off Dinner / Free Appetizer Voucher (Instant SMS Wallet Pass)'
                    },
                    {
                        icon: '🎂',
                        title: 'Birthday Club & VIP Diners Loyalty Signup',
                        desc: 'Capture birth month and anniversary to automate recurring celebration dinner bookings',
                        value: 'Birthday Club & VIP Loyalty Club (Automated Birthday Gift Offer)'
                    },
                    {
                        icon: '🥂',
                        title: 'Private Event & Catering Quote Request',
                        desc: 'Multi-step event inquiry for weddings, corporate banquets & private room buyouts',
                        value: 'Private Event & Catering Quote Request (Guest Count & Menu Options)'
                    }
                ]
            },
            step3: {
                title: 'Step 3: Choose your Culinary Visual Theme',
                desc: 'Select an aesthetic that captures your restaurant atmosphere and showcases your cuisine.',
                aiRecIdx: 0,
                aiRecText: 'AI Recommends: Warm Culinary Elegance with deep wine/charcoal accents elevates average check size.',
                options: [
                    {
                        icon: '🍷',
                        title: 'Warm Culinary Elegance (Fine Dining)',
                        desc: 'Deep burgundy & warm charcoal, gold typography, mouthwatering dish highlights',
                        value: 'Warm Culinary Elegance (Deep Burgundy, Gold & High-End Menu Layout)'
                    },
                    {
                        icon: '🌿',
                        title: 'Modern Fresh Bistro & Farm-to-Table',
                        desc: 'Botanical green accents, clean chalkboard styling, fresh ingredient gallery',
                        value: 'Modern Fresh Bistro (Botanical Green, Chalkboard & Farm-to-Table Cards)'
                    },
                    {
                        icon: '🌙',
                        title: 'Trendy Nightlife, Lounge & Cocktail Bar',
                        desc: 'Moody dark ambiance, glowing neon drink menu highlights, DJ/event calendar',
                        value: 'Trendy Nightlife Lounge (Moody Dark, Neon Cocktail Highlights & Events)'
                    },
                    {
                        icon: '☀️',
                        title: 'Vibrant Family Pizzeria & Casual Diner',
                        desc: 'Warm red & gold accents, kid-friendly specials, simple 1-touch table booking',
                        value: 'Vibrant Family Diner (Warm Crimson & Gold, Casual Menu Grid)'
                    }
                ]
            },
            step4_funnel: {
                title: 'Step 4: Hospitality Funnel Automations & Table Recovery',
                desc: 'Deploy table management pipelines, SMS reminders, and VIP review automations.',
                checkboxes: [
                    {
                        id: 'wiz-auto-sms',
                        label: '⚡ Instant Reservation Confirmation SMS + Digital Table Wallet Pass',
                        desc: 'Dispatches instant text confirmation with directions, parking info & table status',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-pipeline',
                        label: '📊 Dining Funnel Pipeline (Requested ➔ Confirmed ➔ Dined ➔ VIP Regular)',
                        desc: 'Stages: Reservation Inbound ➔ Confirmed ➔ Checked In ➔ Dined ➔ VIP Regular',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-tag',
                        label: '🏷️ Drop-Off Reservation Recovery (T+15m Automated Nudge)',
                        desc: 'Sends SMS to guests who started picking date/party size but did not finalize booking',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-reminders',
                        label: '⏰ 2-Hour Pre-Dining SMS Reminder + Next-Day Google Review Ask',
                        desc: 'Reduces table no-shows to under 4% and automates 5-star Google review collection',
                        checked: true
                    }
                ]
            },
            step4_landing: {
                title: 'Step 4: Dining Automations, Reservation Pipeline & Guest Tags',
                desc: 'Deploy GoHighLevel table management, SMS reminders, and review automations.',
                checkboxes: [
                    {
                        id: 'wiz-auto-sms',
                        label: '⚡ Instant Reservation Confirmation SMS + Digital Table Pass',
                        desc: 'Dispatches instant text confirmation with directions, parking info & table status',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-pipeline',
                        label: '📊 Dining Reservations Pipeline (Requested ➔ Dined)',
                        desc: 'Stages: Reservation Inbound ➔ Confirmed ➔ Checked In ➔ Dined ➔ VIP Regular',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-tag',
                        label: '🏷️ Guest Custom Fields (Party Size, Dietary Needs, Occasion)',
                        desc: 'Captures `party_size`, `dietary_restrictions`, `celebration_type`, `birthday_date`',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-reminders',
                        label: '⏰ 2-Hour Pre-Dining SMS Reminder + Next-Day Google Review Ask',
                        desc: 'Reduces table no-shows to under 4% and automates 5-star Google review collection',
                        checked: true
                    }
                ]
            },
            step5: {
                title: 'Step 5: Restaurant Brand Customization',
                desc: 'Personalize with your restaurant details or use the AI-tailored culinary defaults.',
                brandNamePlaceholder: 'e.g. Bella Vista Italian Ristorante',
                taglinePlaceholder: 'e.g. Authentic Wood-Fired Cuisine & Handcrafted Cocktails',
                defaultBrandName: 'Bella Vista Ristorante',
                defaultTagline: 'Authentic Wood-Fired Italian Dining in the Heart of the City',
                defaultColor: '#dc2626',
                colorPresets: ['#dc2626', '#b91c1c', '#d97706', '#059669', '#8b5cf6', '#0f172a']
            }
        },
        'healthcare': {
            key: 'healthcare',
            name: 'Healthcare & Legal',
            icon: '⚕️',
            matchKeywords: ['healthcare', 'doctor', 'clinic', 'dental', 'dentist', 'legal', 'lawyer', 'attorney', 'chiropractic', 'therapy', 'medical', 'medspa'],
            step2_funnel: {
                title: 'Step 2: Choose your Healthcare/Legal Multi-Step Funnel Flow',
                desc: 'Select the high-converting patient or client intake funnel progression.',
                aiRecIdx: 0,
                aiRecText: 'AI Recommends: HIPAA Secure Intake & Specialist Booking Funnel produces maximum show-ups.',
                options: [
                    {
                        icon: '⚕️',
                        title: 'HIPAA Secure Patient Intake & Specialist Booking Funnel',
                        desc: 'Step 1: Confidential Evaluation Lander ➔ Step 2: Encrypted Medical History & Insurance Form ➔ Step 3: Priority Appointment Calendar ➔ Step 4: Confirmation',
                        value: 'HIPAA Secure Intake Funnel (Confidential Lander ➔ Medical History Form ➔ Appointment Calendar ➔ Intake Confirmed)'
                    },
                    {
                        icon: '⚖️',
                        title: 'Personal Injury & Case Evaluation Funnel',
                        desc: 'Step 1: Accident Case Triage Squeeze ➔ Step 2: Settlement Value Estimator ➔ Step 3: 24/7 Legal Hotline Callback Booking ➔ Step 4: Digital Retainer Agreement',
                        value: 'Personal Injury Case Funnel (Accident Triage ➔ Settlement Estimator ➔ Attorney Callback ➔ Retainer Agreement)'
                    },
                    {
                        icon: '🦷',
                        title: '$49 New Patient Exam & Scan Funnel',
                        desc: 'Step 1: Claim $49 Exam Voucher ➔ Step 2: 2-Step Registration ➔ Step 3: In-Office Scan Calendar Booking ➔ Step 4: SMS Voucher Pass',
                        value: '$49 New Patient Exam Funnel (Claim Voucher ➔ 2-Step Registration ➔ Scan Calendar ➔ SMS Pass Delivery)'
                    },
                    {
                        icon: '📞',
                        title: '24/7 Priority Callback & Telehealth Triage Funnel',
                        desc: 'Step 1: Rapid Symptom Triage ➔ Step 2: 60s On-Call Nurse/Attorney Auto-Dial ➔ Step 3: Video Room Link Delivery ➔ Step 4: Care Plan Won',
                        value: 'Priority Telehealth Funnel (Symptom Triage ➔ Auto-Dial ➔ Video Room Link ➔ Care Plan Won)'
                    }
                ]
            },
            step2_landing: {
                title: 'Step 2: What is your Practice Conversion Goal?',
                desc: 'Select the consultation or patient intake pathway.',
                aiRecIdx: 0,
                aiRecText: 'AI Recommends: New Patient / Client Intake Booking with HIPAA notice produces maximum show-ups.',
                options: [
                    {
                        icon: '⚕️',
                        title: 'New Patient / Client Intake Booking',
                        desc: 'Interactive calendar to choose provider, service type & insurance provider',
                        value: 'New Patient / Client Intake Booking (Provider Selection & GHL Calendar)'
                    },
                    {
                        icon: '🦷',
                        title: '$49 New Patient Exam & Consultation Special',
                        desc: 'Promotional voucher capturing lead contact details with instant SMS confirmation',
                        value: '$49 New Patient Exam & Consultation Special (SMS Voucher Claim)'
                    },
                    {
                        icon: '⚖️',
                        title: 'Free Confidential Legal Case Evaluation',
                        desc: 'Secure 4-question intake capturing case timeline, damages & contact info',
                        value: 'Free Confidential Legal Case Evaluation (Case Details & Scope Form)'
                    },
                    {
                        icon: '📞',
                        title: '24/7 Priority Callback & Telehealth Line',
                        desc: 'Rapid intake routing for immediate nurse triage or attorney consultation',
                        value: '24/7 Priority Callback & Telehealth Triage (Rapid Phone & SMS Routing)'
                    }
                ]
            },
            step3: {
                title: 'Step 3: Choose your Professional Practice Theme',
                desc: 'Select an aesthetic that conveys clinical excellence, confidentiality, and utmost trust.',
                aiRecIdx: 0,
                aiRecText: 'AI Recommends: Clinical Serenity Light with medical cyan builds instant patient trust.',
                options: [
                    {
                        icon: '☀️',
                        title: 'Clinical Serenity Light (Medical Cyan & Slate)',
                        desc: 'Calming blue/cyan palette, HIPAA compliance badges, doctor credentials showcase',
                        value: 'Clinical Serenity Light (Medical Cyan, Slate & HIPAA Badges)'
                    },
                    {
                        icon: '⚖️',
                        title: 'Prestigious Legal Firm (Navy & Gold)',
                        desc: 'Deep authoritative navy blue, serif typography, scale of justice badge, courtroom verdicts',
                        value: 'Prestigious Legal Firm (Deep Navy, Gold Accents & Verdict Proof)'
                    },
                    {
                        icon: '🌿',
                        title: 'Holistic Wellness & MedSpa Serenity',
                        desc: 'Soft lavender & eucalyptus tones, treatment menu cards, ambient soothing aesthetics',
                        value: 'Holistic Wellness & MedSpa (Soft Lavender, Eucalyptus & Treatment Cards)'
                    },
                    {
                        icon: '⚡',
                        title: 'Urgent Care Fast-Track & Walk-In',
                        desc: 'Live wait-time counter badge, high-visibility check-in banner, instant map directions',
                        value: 'Urgent Care Fast-Track (Live Wait-Time Badge & Fast Check-In Banner)'
                    }
                ]
            },
            step4_funnel: {
                title: 'Step 4: Healthcare/Legal Funnel Automations & HIPAA Workflows',
                desc: 'Deploy compliant appointment workflows, case qualification, and automated reminders.',
                checkboxes: [
                    {
                        id: 'wiz-auto-sms',
                        label: '⚡ HIPAA/Confidential SMS Confirmation + Online Medical History Link',
                        desc: 'Dispatches secure pre-visit intake link to collect insurance & history before arrival',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-pipeline',
                        label: '📊 Patient/Case Intake Funnel Pipeline (Intake ➔ Treatment Won)',
                        desc: 'Stages: Step 1 Inquiry ➔ Medical Review ➔ Consultation Held ➔ Treatment Won',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-tag',
                        label: '🏷️ Incomplete Medical Form Recovery Cadence (T+15m SMS)',
                        desc: 'Sends automated SMS reminder to patients who initiated intake but stopped before HIPAA sign-off',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-reminders',
                        label: '⏰ 24h & 2h Appointment Reminder Cadence + Reschedule Link',
                        desc: 'Automated 2-way SMS reminder reducing clinic no-shows to under 5%',
                        checked: true
                    }
                ]
            },
            step4_landing: {
                title: 'Step 4: Healthcare/Legal Pipelines, Intake Fields & HIPAA Triggers',
                desc: 'Deploy compliant appointment workflows, case qualification, and automated reminders.',
                checkboxes: [
                    {
                        id: 'wiz-auto-sms',
                        label: '⚡ HIPAA/Confidential SMS Confirmation + Online Medical History Link',
                        desc: 'Dispatches secure pre-visit intake link to collect insurance & history before arrival',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-pipeline',
                        label: '📊 Patient/Case Intake Pipeline (Intake ➔ Treatment Won)',
                        desc: 'Stages: Intake Submitted ➔ Consultation Held ➔ Treatment/Retainer Accepted ➔ Active',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-tag',
                        label: '🏷️ Practice Custom Fields (Insurance, Symptoms, Case Details)',
                        desc: 'Captures `insurance_carrier`, `primary_symptoms`, `preferred_provider`, `intake_notes`',
                        checked: true
                    },
                    {
                        id: 'wiz-auto-reminders',
                        label: '⏰ 24h & 2h Appointment Reminder Cadence + Reschedule Link',
                        desc: 'Automated 2-way SMS reminder reducing clinic no-shows to under 5%',
                        checked: true
                    }
                ]
            },
            step5: {
                title: 'Step 5: Practice Brand Customization',
                desc: 'Personalize with your practice details or use the AI-tailored healthcare defaults.',
                brandNamePlaceholder: 'e.g. Apex Health & Wellness Clinic',
                taglinePlaceholder: 'e.g. Compassionate, State-of-the-Art Medical Care for Your Family',
                defaultBrandName: 'Apex Medical Group',
                defaultTagline: 'Compassionate Medical & Specialty Care You Can Trust',
                defaultColor: '#0284c7',
                colorPresets: ['#0284c7', '#0891b2', '#059669', '#1e293b', '#7c3aed', '#dc2626']
            }
        }
    };

    function resolveNicheKey(inputString) {
        if (!inputString) return 'fitness';
        const str = inputString.toLowerCase();
        for (const [key, cfg] of Object.entries(NICHE_CONFIGURATIONS)) {
            if (str.includes(key) || str.includes(cfg.name.toLowerCase())) return key;
            if (cfg.matchKeywords && cfg.matchKeywords.some(kw => str.includes(kw))) {
                return key;
            }
        }
        return 'fitness';
    }

    function applyNicheConfiguration(nicheKey) {
        const config = NICHE_CONFIGURATIONS[nicheKey] || NICHE_CONFIGURATIONS['fitness'];
        currentNicheKey = config.key;

        const isFunnel = (currentWizardMode === 'funnel');

        // Dynamic Header titles & badges
        const wizardTitleText = document.getElementById('wizard-title-text');
        const wizardSubtitleText = document.getElementById('wizard-subtitle-text');
        const wizardBrandIcon = document.getElementById('wizard-brand-icon');

        if (wizardTitleText) {
            wizardTitleText.textContent = isFunnel ? 'Smart Multi-Step Funnel & CRM Wizard' : 'Smart Landing Page & CRM Wizard';
        }
        if (wizardSubtitleText) {
            wizardSubtitleText.textContent = isFunnel ? 'Configure your high-converting multi-step funnel, pipeline & automations in 6 quick steps' : 'Configure your landing page, pipeline & CRM automations in 6 quick steps';
        }
        if (wizardBrandIcon) {
            wizardBrandIcon.textContent = isFunnel ? '🌪️' : '🚀';
        }

        // Dynamic Step 2 Progress Node Label
        const step2NodeLabel = document.querySelector('.wizard-step-node[data-step="2"] .step-label');
        if (step2NodeLabel) {
            step2NodeLabel.textContent = isFunnel ? 'Funnel Flow' : 'Goal / CTA';
        }

        // 1. Update Step 2 (Funnel vs Landing Options)
        const step2Config = isFunnel ? (config.step2_funnel || config.step2_landing) : (config.step2_landing || config.step2_funnel);
        const step2Title = document.getElementById('step-2-title');
        const step2Desc = document.getElementById('step-2-desc');
        const step2Grid = document.getElementById('step-2-options-grid');
        const aiBox2 = document.getElementById('ai-suggest-step2');
        const aiText2 = document.getElementById('ai-suggest-text-2');

        if (step2Title) step2Title.textContent = step2Config.title;
        if (step2Desc) step2Desc.textContent = step2Config.desc;
        if (aiBox2 && aiText2) {
            aiText2.textContent = step2Config.aiRecText;
            aiBox2.classList.remove('hidden');
        }

        if (step2Grid) {
            step2Grid.innerHTML = step2Config.options.map((opt, idx) => {
                const isRec = idx === step2Config.aiRecIdx;
                const isSelected = isRec;
                return `
                    <div class="wizard-option-card ${isSelected ? 'selected' : ''}" data-value="${escapeHtml(opt.value)}" ${isRec ? 'data-ai-rec="true"' : ''}>
                        <div class="card-icon">${opt.icon}</div>
                        <div class="card-content">
                            <h5>${escapeHtml(opt.title)}</h5>
                            <p>${escapeHtml(opt.desc)}</p>
                        </div>
                        ${isRec ? '<span class="ai-rec-badge" title="AI Recommended for maximum conversion">💡 AI Pick</span>' : ''}
                        <span class="card-check">✓</span>
                    </div>
                `;
            }).join('');
        }

        // 2. Update Step 3 (Visual Theme)
        const step3Title = document.getElementById('step-3-title');
        const step3Desc = document.getElementById('step-3-desc');
        const step3Grid = document.getElementById('step-3-options-grid');
        const aiBox3 = document.getElementById('ai-suggest-step3');
        const aiText3 = document.getElementById('ai-suggest-text-3');

        if (step3Title) step3Title.textContent = config.step3.title;
        if (step3Desc) step3Desc.textContent = config.step3.desc;
        if (aiBox3 && aiText3) {
            aiText3.textContent = config.step3.aiRecText;
            aiBox3.classList.remove('hidden');
        }

        if (step3Grid) {
            step3Grid.innerHTML = config.step3.options.map((opt, idx) => {
                const isRec = idx === config.step3.aiRecIdx;
                return `
                    <div class="wizard-option-card ${idx === 0 ? 'selected' : ''}" data-value="${escapeHtml(opt.value)}" ${isRec ? 'data-ai-rec="true"' : ''}>
                        <div class="card-icon">${opt.icon}</div>
                        <div class="card-content">
                            <h5>${escapeHtml(opt.title)}</h5>
                            <p>${escapeHtml(opt.desc)}</p>
                        </div>
                        ${isRec ? '<span class="ai-rec-badge" title="AI Recommended theme">💡 AI Pick</span>' : ''}
                        <span class="card-check">✓</span>
                    </div>
                `;
            }).join('');
        }

        // 3. Update Step 4 (Automations & Recovery)
        const step4Config = isFunnel ? (config.step4_funnel || config.step4_landing) : (config.step4_landing || config.step4_funnel);
        const step4Title = document.getElementById('step-4-title');
        const step4Desc = document.getElementById('step-4-desc');
        const step4List = document.getElementById('step-4-checkboxes-list');

        if (step4Title) step4Title.textContent = step4Config.title;
        if (step4Desc) step4Desc.textContent = step4Config.desc;

        if (step4List) {
            step4List.innerHTML = step4Config.checkboxes.map(cb => `
                <label class="wizard-checkbox-card">
                    <input type="checkbox" id="${escapeHtml(cb.id)}" ${cb.checked ? 'checked' : ''}>
                    <div class="cb-content">
                        <strong>${escapeHtml(cb.label)}</strong>
                        <span>${escapeHtml(cb.desc)}</span>
                    </div>
                </label>
            `).join('');
        }

        // 4. Update Step 5 (Brand Defaults & Placeholders)
        const step5Title = document.getElementById('step-5-title');
        const step5Desc = document.getElementById('step-5-desc');
        const brandNameInput = document.getElementById('wiz-brand-name');
        const brandTaglineInput = document.getElementById('wiz-brand-tagline');
        const brandColorInput = document.getElementById('wiz-brand-color');
        const brandColorHex = document.getElementById('brand-color-hex');
        const presetsContainer = document.getElementById('wiz-color-presets');

        if (step5Title) step5Title.textContent = config.step5.title;
        if (step5Desc) step5Desc.textContent = config.step5.desc;

        if (brandNameInput) {
            brandNameInput.placeholder = config.step5.brandNamePlaceholder;
            if (!brandNameInput.value.trim() || Object.values(NICHE_CONFIGURATIONS).some(c => c.step5.defaultBrandName === brandNameInput.value.trim())) {
                brandNameInput.value = config.step5.defaultBrandName;
            }
        }

        if (brandTaglineInput) {
            brandTaglineInput.placeholder = config.step5.taglinePlaceholder;
            if (!brandTaglineInput.value.trim() || Object.values(NICHE_CONFIGURATIONS).some(c => c.step5.defaultTagline === brandTaglineInput.value.trim())) {
                brandTaglineInput.value = config.step5.defaultTagline;
            }
        }

        if (brandColorInput && brandColorHex) {
            brandColorInput.value = config.step5.defaultColor;
            brandColorHex.textContent = config.step5.defaultColor;
        }

        if (presetsContainer && config.step5.colorPresets) {
            presetsContainer.innerHTML = config.step5.colorPresets.map((color, idx) => `
                <button type="button" class="color-preset-btn ${idx === 0 ? 'active' : ''}" data-color="${color}" style="background:${color}" title="${color}"></button>
            `).join('');
            bindColorPresetEvents();
        }

        // Re-bind option card selection events
        bindOptionCardEvents();
    }

    function bindOptionCardEvents() {
        document.querySelectorAll('.wizard-options-grid .wizard-option-card').forEach(card => {
            card.onclick = () => {
                const grid = card.closest('.wizard-options-grid');
                if (grid) {
                    grid.querySelectorAll('.wizard-option-card').forEach(c => c.classList.remove('selected'));
                    card.classList.add('selected');
                    hideValidation();

                    // If user changed Step 1 (Industry), immediately apply the new niche configuration
                    if (grid.getAttribute('data-group') === 'niche') {
                        const val = card.getAttribute('data-value') || '';
                        const resolvedKey = resolveNicheKey(val);
                        applyNicheConfiguration(resolvedKey);
                    }
                }
            };
        });
    }

    function bindColorPresetEvents() {
        const brandColorInput = document.getElementById('wiz-brand-color');
        const brandColorHex = document.getElementById('brand-color-hex');

        document.querySelectorAll('.color-preset-btn').forEach(btn => {
            btn.onclick = () => {
                const color = btn.getAttribute('data-color');
                if (brandColorInput) brandColorInput.value = color;
                if (brandColorHex) brandColorHex.textContent = color;
                document.querySelectorAll('.color-preset-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            };
        });
    }

    // Color picker input listener
    const brandColorInput = document.getElementById('wiz-brand-color');
    const brandColorHex = document.getElementById('brand-color-hex');
    if (brandColorInput) {
        brandColorInput.addEventListener('input', () => {
            if (brandColorHex) brandColorHex.textContent = brandColorInput.value;
            document.querySelectorAll('.color-preset-btn').forEach(b => b.classList.remove('active'));
        });
    }

    const headerWizardLauncherBtn = document.getElementById('header-wizard-launcher-btn');
    const sidebarWizardBtn = document.getElementById('sidebar-wizard-btn');

    if (openWizardChipBtn) openWizardChipBtn.addEventListener('click', () => openWizardModal('', 'funnel'));
    if (headerWizardLauncherBtn) headerWizardLauncherBtn.addEventListener('click', () => openWizardModal('', 'funnel'));
    if (sidebarWizardBtn) sidebarWizardBtn.addEventListener('click', () => openWizardModal('', 'funnel'));
    if (closeWizardModalBtn) closeWizardModalBtn.addEventListener('click', closeWizardModal);
    if (cancelWizardModalBtn) cancelWizardModalBtn.addEventListener('click', closeWizardModal);

    // Global Keyboard Shortcut: Ctrl + K (or Cmd + K) for New Chat
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            createNewThread(true);
        }
    });

    function openWizardModal(promptContext = '', defaultMode = '') {
        currentWizardStep = 1;
        hideValidation();

        const lower = (promptContext || '').toLowerCase();
        if (defaultMode) {
            currentWizardMode = defaultMode;
        } else if (lower.includes('funnel') || lower.includes('vsl') || lower.includes('tripwire') || lower.includes('webinar') || lower.includes('challenge')) {
            currentWizardMode = 'funnel';
        } else if (lower.includes('landing') || lower.includes('website') || lower.includes('one pager') || lower.includes('lead page')) {
            currentWizardMode = 'landing_page';
        } else {
            currentWizardMode = 'funnel'; // Default to funnel
        }

        // Update toggle pill buttons in modal header
        const btnFunnel = document.getElementById('btn-mode-funnel');
        const btnLanding = document.getElementById('btn-mode-landing');
        if (btnFunnel && btnLanding) {
            btnFunnel.classList.toggle('active', currentWizardMode === 'funnel');
            btnLanding.classList.toggle('active', currentWizardMode === 'landing_page');
        }

        // Detect niche from prompt context if provided
        const detectedNicheKey = resolveNicheKey(promptContext);
        currentNicheKey = detectedNicheKey;

        // Highlight matching Step 1 card
        const nicheCards = document.querySelectorAll('#wizard-step-1 .wizard-option-card');
        nicheCards.forEach(c => {
            c.classList.remove('selected');
            const val = c.getAttribute('data-value') || '';
            if (resolveNicheKey(val) === detectedNicheKey) {
                c.classList.add('selected');
            }
        });

        // If none selected, default to first card
        if (!document.querySelector('#wizard-step-1 .wizard-option-card.selected') && nicheCards[0]) {
            nicheCards[0].classList.add('selected');
        }

        // Apply dynamic questions and options for this niche across steps 2-5
        applyNicheConfiguration(detectedNicheKey);

        renderWizardStep(1, 'none');
        if (wizardModal) wizardModal.classList.remove('hidden');
    }

    function closeWizardModal() {
        if (wizardModal) wizardModal.classList.add('hidden');
    }

    function hideValidation() {
        if (wizardValidationBar) wizardValidationBar.classList.add('hidden');
    }

    function showValidation(msg) {
        if (wizardValidationText) wizardValidationText.textContent = msg;
        if (wizardValidationBar) {
            wizardValidationBar.classList.remove('hidden');
            wizardValidationBar.style.animation = 'none';
            void wizardValidationBar.offsetHeight;
            wizardValidationBar.style.animation = '';
        }
    }

    function populateSummaryCard() {
        const card = document.getElementById('wizard-summary-card');
        if (!card) return;

        const isFunnel = (currentWizardMode === 'funnel');
        const s1 = document.querySelector('#wizard-step-1 .wizard-option-card.selected');
        const s2 = document.querySelector('#wizard-step-2 .wizard-option-card.selected');
        const s3 = document.querySelector('#wizard-step-3 .wizard-option-card.selected');

        const niche = s1 ? (s1.querySelector('h5')?.textContent || s1.getAttribute('data-value')) : 'Not selected';
        const objective = s2 ? (s2.querySelector('h5')?.textContent || s2.getAttribute('data-value')) : 'Not selected';
        const style = s3 ? (s3.querySelector('h5')?.textContent || s3.getAttribute('data-value')) : 'Not selected';

        const automations = [];
        document.querySelectorAll('#step-4-checkboxes-list input[type="checkbox"]:checked').forEach(cb => {
            const labelEl = cb.closest('.wizard-checkbox-card')?.querySelector('strong');
            if (labelEl) automations.push(labelEl.textContent.trim());
        });

        const brandName = document.getElementById('wiz-brand-name')?.value.trim() || 'AI Generated';
        const brandTagline = document.getElementById('wiz-brand-tagline')?.value.trim() || 'AI Generated';
        const brandColor = document.getElementById('wiz-brand-color')?.value || '#10b981';
        const brandLogo = document.getElementById('wiz-brand-logo')?.value.trim() || 'None';

        card.innerHTML = `
            <div class="summary-section">
                <span class="summary-icon">${isFunnel ? '🌪️' : '📄'}</span>
                <div class="summary-content">
                    <div class="summary-label">Asset Type</div>
                    <div class="summary-value">${isFunnel ? 'Multi-Step High-Converting Funnel' : 'Single High-Converting Landing Page'}</div>
                </div>
            </div>
            <div class="summary-section">
                <span class="summary-icon">🏢</span>
                <div class="summary-content">
                    <div class="summary-label">Industry / Niche</div>
                    <div class="summary-value">${escapeHtml(niche)}</div>
                </div>
            </div>
            <div class="summary-section">
                <span class="summary-icon">🎯</span>
                <div class="summary-content">
                    <div class="summary-label">${isFunnel ? 'Multi-Step Funnel Flow' : 'Primary Conversion Goal / CTA'}</div>
                    <div class="summary-value">${escapeHtml(objective)}</div>
                </div>
            </div>
            <div class="summary-section">
                <span class="summary-icon">🎨</span>
                <div class="summary-content">
                    <div class="summary-label">Design Theme</div>
                    <div class="summary-value">${escapeHtml(style)}</div>
                </div>
            </div>
            <div class="summary-section">
                <span class="summary-icon">⚙️</span>
                <div class="summary-content">
                    <div class="summary-label">Connected Automations & Custom Fields</div>
                    <div class="summary-value">${automations.length > 0 ? automations.map(a => `<span class="summary-tag">${escapeHtml(a)}</span>`).join('') : 'None selected'}</div>
                </div>
            </div>
            <div class="summary-section">
                <span class="summary-icon">✏️</span>
                <div class="summary-content">
                    <div class="summary-label">Brand Identity</div>
                    <div class="summary-value">
                        <strong>${escapeHtml(brandName)}</strong> — "${escapeHtml(brandTagline)}"<br>
                        <span class="summary-color-swatch" style="background:${brandColor}"></span>${brandColor} &nbsp;|&nbsp; Logo: ${brandLogo === 'None' ? 'AI Generated' : '✓ Custom'}
                    </div>
                </div>
            </div>
        `;
    }

    function renderWizardStep(step, direction) {
        currentWizardStep = step;
        hideValidation();

        // Slide animation
        for (let i = 1; i <= TOTAL_WIZARD_STEPS; i++) {
            const panel = document.getElementById(`wizard-step-${i}`);
            if (!panel) continue;

            if (i === step) {
                panel.classList.add('active');
                panel.classList.remove('slide-out-left', 'slide-out-right', 'slide-in-left', 'slide-in-right');
                if (direction === 'forward') panel.classList.add('slide-in-right');
                else if (direction === 'backward') panel.classList.add('slide-in-left');
            } else {
                panel.classList.remove('active', 'slide-in-right', 'slide-in-left');
            }
        }

        // Node indicators
        document.querySelectorAll('.wizard-step-node').forEach(node => {
            const nodeStep = parseInt(node.getAttribute('data-step') || '1');
            node.classList.remove('active', 'completed');
            const numSpan = node.querySelector('.step-num');
            if (nodeStep < step) {
                node.classList.add('completed');
                if (numSpan) numSpan.textContent = '✓';
            } else if (nodeStep === step) {
                node.classList.add('active');
                if (numSpan) numSpan.textContent = String(nodeStep);
            } else {
                if (numSpan) numSpan.textContent = String(nodeStep);
            }
        });

        // Connector lines
        document.querySelectorAll('.wizard-step-connector').forEach((conn, idx) => {
            if (idx + 1 < step) conn.classList.add('completed');
            else conn.classList.remove('completed');
        });

        // Navigation button labels
        if (wizardBackBtn) wizardBackBtn.disabled = (step === 1);
        if (wizardNextBtn) {
            const isFunnel = (currentWizardMode === 'funnel');
            wizardNextBtn.textContent = (step === TOTAL_WIZARD_STEPS) ? (isFunnel ? '🚀 Generate Funnel Bundle' : '🚀 Generate Landing Page') : 'Next Step →';
        }

        // Summary on step 6
        if (step === 6) populateSummaryCard();
    }

    function validateCurrentStep() {
        if (currentWizardStep >= 1 && currentWizardStep <= 3) {
            const panel = document.getElementById(`wizard-step-${currentWizardStep}`);
            if (panel) {
                const selected = panel.querySelector('.wizard-option-card.selected');
                if (!selected) {
                    showValidation('Please select an option before proceeding to the next step.');
                    return false;
                }
            }
        }
        if (currentWizardStep === 4) {
            const anyChecked = document.querySelector('#step-4-checkboxes-list input[type="checkbox"]:checked');
            if (!anyChecked) {
                showValidation('Please select at least one automation workflow.');
                return false;
            }
        }
        return true;
    }

    if (wizardBackBtn) {
        wizardBackBtn.addEventListener('click', () => {
            if (currentWizardStep > 1) {
                renderWizardStep(currentWizardStep - 1, 'backward');
            }
        });
    }

    if (wizardNextBtn) {
        wizardNextBtn.addEventListener('click', () => {
            if (currentWizardStep < TOTAL_WIZARD_STEPS) {
                if (!validateCurrentStep()) return;
                renderWizardStep(currentWizardStep + 1, 'forward');
            } else {
                submitWizardBuild();
            }
        });
    }

    if (wizardQuickBtn) {
        wizardQuickBtn.addEventListener('click', () => {
            // Pick AI Recommended options for current niche
            const config = NICHE_CONFIGURATIONS[currentNicheKey] || NICHE_CONFIGURATIONS['fitness'];
            const isFunnel = (currentWizardMode === 'funnel');
            const step2Cfg = isFunnel ? config.step2_funnel : config.step2_landing;

            // Step 2 & 3: select AI recommended cards
            const s2Cards = document.querySelectorAll('#step-2-options-grid .wizard-option-card');
            s2Cards.forEach((c, idx) => {
                c.classList.toggle('selected', idx === (step2Cfg ? step2Cfg.aiRecIdx : 0));
            });

            const s3Cards = document.querySelectorAll('#step-3-options-grid .wizard-option-card');
            s3Cards.forEach((c, idx) => {
                c.classList.toggle('selected', idx === (config.step3 ? config.step3.aiRecIdx : 0));
            });

            // Step 4: check all automations
            document.querySelectorAll('#step-4-checkboxes-list input[type="checkbox"]').forEach(cb => cb.checked = true);

            // Step 5: fill niche brand defaults
            const nameInput = document.getElementById('wiz-brand-name');
            if (nameInput) nameInput.value = config.step5.defaultBrandName;
            const tagInput = document.getElementById('wiz-brand-tagline');
            if (tagInput) tagInput.value = config.step5.defaultTagline;
            const colorInput = document.getElementById('wiz-brand-color');
            if (colorInput) colorInput.value = config.step5.defaultColor;

            submitWizardBuild();
        });
    }

    function submitWizardBuild() {
        const isFunnel = (currentWizardMode === 'funnel');
        const step1Selected = document.querySelector('#wizard-step-1 .wizard-option-card.selected');
        const step2Selected = document.querySelector('#wizard-step-2 .wizard-option-card.selected');
        const step3Selected = document.querySelector('#wizard-step-3 .wizard-option-card.selected');

        const rawNiche = step1Selected ? (step1Selected.querySelector('h5')?.textContent || step1Selected.getAttribute('data-value')) : 'Fitness & Gym Studio';
        const rawObjective = step2Selected ? (step2Selected.querySelector('h5')?.textContent || step2Selected.getAttribute('data-value')) : (isFunnel ? 'VSL & 1-on-1 Assessment Funnel' : '7-Day Free VIP Pass');
        const rawStyle = step3Selected ? (step3Selected.querySelector('h5')?.textContent || step3Selected.getAttribute('data-value')) : 'Modern Dark Glassmorphism';

        const cleanNiche = rawNiche.split('(')[0].trim();
        const cleanObjective = rawObjective.split('(')[0].trim();
        const cleanStyle = rawStyle.split('(')[0].trim();

        const automations = [];
        document.querySelectorAll('#step-4-checkboxes-list input[type="checkbox"]:checked').forEach(cb => {
            const title = cb.closest('.wizard-checkbox-card')?.querySelector('strong')?.textContent.trim();
            if (title) automations.push(title);
        });

        // Brand customization fields
        const config = NICHE_CONFIGURATIONS[currentNicheKey] || NICHE_CONFIGURATIONS['fitness'];
        const brandName = document.getElementById('wiz-brand-name')?.value.trim() || config.step5.defaultBrandName;
        const brandTagline = document.getElementById('wiz-brand-tagline')?.value.trim() || config.step5.defaultTagline;
        const brandColor = document.getElementById('wiz-brand-color')?.value || config.step5.defaultColor;
        const brandLogo = document.getElementById('wiz-brand-logo')?.value.trim() || '';

        closeWizardModal();

        let brandSection = `\n\nBrand Customization:`;
        brandSection += `\n- Business Name: ${brandName}`;
        brandSection += `\n- Hero Tagline: ${brandTagline}`;
        brandSection += `\n- Primary Brand Color: ${brandColor}`;
        if (brandLogo) brandSection += `\n- Logo URL: ${brandLogo}`;

        const compiledPrompt = isFunnel ? 
`Build a complete GoHighLevel Multi-Step High-Converting Funnel and CRM Architecture for a ${cleanNiche} business.

Configuration:
- Asset Type: Multi-Step Conversion Funnel (Opt-in ➔ VSL ➔ Booking/Checkout ➔ Upsell ➔ Thank You)
- Target Industry: ${cleanNiche}
- Funnel Flow Structure: ${cleanObjective}
- Visual Design Aesthetic: ${cleanStyle}
- Connected Automations & Drop-off Recovery: ${automations.join(', ')}${brandSection}

Please provide the complete multi-step funnel architecture, step-by-step URLs/pages, production-ready responsive HTML/CSS code for each step, HighLevel Pipeline stages taxonomy, Contact Custom Fields & Tags schema, and 2-step abandoned cart / drop-off Workflow automations.`
:
`Build a complete GoHighLevel High-Converting Landing Page and CRM Architecture for a ${cleanNiche} business.

Configuration:
- Asset Type: Single High-Converting Landing Page
- Target Industry: ${cleanNiche}
- Primary Conversion Goal / CTA: ${cleanObjective}
- Visual Design Aesthetic: ${cleanStyle}
- Connected Automations: ${automations.join(', ')}${brandSection}

Please provide the production-ready responsive HTML/CSS landing page code, HighLevel Pipeline stages taxonomy, Contact Custom Fields & Tags schema, and step-by-step Workflow automation configuration.`;

        if (userInput) {
            userInput.value = compiledPrompt;
            userInput.style.height = 'auto';
            if (sendBtn) sendBtn.disabled = false;
            handleSendPrompt();
        }
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
        if (sidebarOverlay) sidebarOverlay.classList.add('active');
        localStorage.setItem('sidebar_closed', 'false');
    }

    function closeSidebar() {
        sidebar.classList.add('closed');
        if (sidebarOverlay) sidebarOverlay.classList.remove('active');
        localStorage.setItem('sidebar_closed', 'true');
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
    // CHAT EXECUTION & PROMPT QUEUE ENGINE
    // ==========================================

    if (userInput) {
        userInput.addEventListener('input', () => {
            userInput.style.height = 'auto';
            userInput.style.height = Math.min(userInput.scrollHeight, 180) + 'px';
            if (!isGenerating) {
                updateSendButtonState();
            }
        });

        userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && isGenerating) {
                e.preventDefault();
                abortCurrentGeneration();
            } else if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (isGenerating) {
                    abortCurrentGeneration();
                } else if (userInput.value.trim().length > 0 || (typeof pendingAttachments !== 'undefined' && pendingAttachments.length > 0)) {
                    handleSendPrompt();
                }
            }
        });
    }

    if (sendBtn) {
        sendBtn.addEventListener('click', () => {
            if (isGenerating) {
                abortCurrentGeneration();
            } else {
                handleSendPrompt();
            }
        });
    }

    cardItems.forEach(card => {
        card.addEventListener('click', () => {
            const prompt = card.getAttribute('data-prompt');
            if (prompt) {
                if (userInput) {
                    userInput.value = prompt;
                    userInput.style.height = 'auto';
                }
                updateSendButtonState();
                handleSendPrompt();
            }
        });
    });

    chipBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tmpl = btn.getAttribute('data-template');
            if (tmpl && userInput) {
                userInput.value = tmpl;
                userInput.focus();
                userInput.style.height = 'auto';
                userInput.style.height = Math.min(userInput.scrollHeight, 180) + 'px';
                updateSendButtonState();
            }
        });
    });

    async function handleSendPrompt(promptOverride = null, existingElementId = null) {
        const prompt = promptOverride || userInput.value.trim();
        if (!prompt) return;

        // Auto-open Smart Asset Wizard for landing page/funnel requests (only if not already generating)
        const lower = prompt.toLowerCase().trim();
        const isFromWizard = prompt.includes('custom wizard specifications:') || prompt.includes('Configuration:');
        const isGenericBuild = !isFromWizard && (
            /^(build|create|make|design|generate)\s+(me\s+)?(a\s+)?(landing\s*page|website|funnel|crm\s*setup|lead\s*page)[\s\.\?!]*$/i.test(lower) || 
            /^(landing\s*page|funnel)\s*(bana\s*do|bna\s*do|create\s*kro|build\s*kro)[\s\.\?!]*$/i.test(lower) ||
            lower.startsWith('make me a funnel') ||
            lower.startsWith('create a funnel') ||
            lower.startsWith('build a funnel') ||
            lower.startsWith('build me a landing page') ||
            lower.startsWith('create a landing page')
        );

        if (isGenericBuild && !isGenerating) {
            userInput.value = '';
            userInput.style.height = 'auto';
            if (sendBtn) sendBtn.disabled = false;
            openWizardModal(prompt);
            return;
        }

        // IF CURRENTLY GENERATING: Put prompt into Pending Queue!
        if (isGenerating && !promptOverride) {
            userInput.value = '';
            userInput.style.height = 'auto';
            if (welcomeScreen) welcomeScreen.classList.add('hidden');

            const queuedElementId = 'queued_msg_' + Date.now();
            const queuedMsgWrap = appendMessageUI('user', prompt, null, true, queuedElementId);
            promptQueue.push({ prompt: prompt, elementId: queuedElementId });
            updateQueueUI();
            scrollToBottom();
            return;
        }

        // Start active generation
        isGenerating = true;
        updateSendButtonState();
        currentAbortController = new AbortController();

        // Extract prior history before appending new user prompt
        const activeThreadObj = getThreadById(currentThreadId);
        const history = (activeThreadObj && activeThreadObj.messages) ? activeThreadObj.messages.slice(-10).map(m => ({
            role: m.role,
            content: m.content
        })) : [];

        const currentAttachments = [...pendingAttachments];
        pendingAttachments = [];
        renderAttachmentPreviews();

        if (!promptOverride) {
            userInput.value = '';
            userInput.style.height = 'auto';
        }

        if (welcomeScreen) welcomeScreen.classList.add('hidden');

        // Append or activate User Message
        let userMsgWrap = null;
        if (existingElementId) {
            userMsgWrap = document.getElementById(existingElementId);
            if (userMsgWrap) {
                userMsgWrap.classList.remove('queued-message');
                const queuedBadge = userMsgWrap.querySelector('.queued-status-badge');
                if (queuedBadge) queuedBadge.remove();
            }
            addMessageToCurrentThread('user', prompt, [], existingElementId);
        } else {
            const msgId = 'msg_' + Date.now();
            userMsgWrap = appendMessageUI('user', prompt, msgId, false, null, currentAttachments);
            addMessageToCurrentThread('user', prompt, [], msgId);
        }

        if (userMsgWrap) {
            userMsgWrap.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

        if (loadingIndicator) loadingIndicator.classList.remove('hidden');

        const botMsgWrap = document.createElement('div');
        const botMsgId = 'msg_' + Date.now() + '_bot';
        botMsgWrap.className = 'message-wrapper assistant';
        botMsgWrap.id = botMsgId;
        botMsgWrap.innerHTML = `
            <div class="assistant-avatar thinking-pulse" id="current-bot-avatar">⚡</div>
            <div class="assistant-body" id="current-bot-body">
                <div class="ai-thinking-card" id="current-thinking-card">
                    <div class="ai-thinking-header">
                        <div class="thinking-spinner">
                            <div class="spinner-ring"></div>
                            <span class="sparkle-icon">✨</span>
                        </div>
                        <div class="thinking-text-wrapper">
                            <span class="thinking-title">Copilot is thinking...</span>
                            <span class="thinking-status" id="thinking-status-text">Analyzing prompt & scoping requirements...</span>
                        </div>
                    </div>
                    <div class="thinking-skeleton-lines">
                        <div class="skeleton-shimmer-line line-long"></div>
                        <div class="skeleton-shimmer-line line-medium"></div>
                        <div class="skeleton-shimmer-line line-short"></div>
                    </div>
                </div>
            </div>
            <div class="message-actions-bar">
                <button type="button" class="msg-action-btn copy-msg-btn" title="Copy Response">📋</button>
                <button type="button" class="msg-action-btn delete delete-msg-btn" title="Delete Message">🗑️</button>
            </div>
        `;
        messagesList.appendChild(botMsgWrap);
        bindMessageActions(botMsgWrap, botMsgId);

        const botBodyEl = botMsgWrap.querySelector('.assistant-body');
        const botAvatarEl = botMsgWrap.querySelector('.assistant-avatar');

        // Dynamic cycling thinking status messages
        const thinkingStatuses = [
            'Analyzing prompt & scoping requirements...',
            'Formulating smart clarifying questions & blueprint...',
            'Checking HighLevel taxonomy & pipelines...',
            'Preparing execution strategy...',
            'Streaming response...'
        ];
        let statusIdx = 0;
        const statusInterval = setInterval(() => {
            statusIdx = (statusIdx + 1) % thinkingStatuses.length;
            const statusEl = document.getElementById('thinking-status-text');
            if (statusEl) {
                statusEl.style.opacity = '0';
                setTimeout(() => {
                    if (statusEl) {
                        statusEl.textContent = thinkingStatuses[statusIdx];
                        statusEl.style.opacity = '1';
                    }
                }, 180);
            }
        }, 1500);

        function removeThinkingState() {
            clearInterval(statusInterval);
            const thinkingCard = document.getElementById('current-thinking-card');
            if (thinkingCard) thinkingCard.remove();
            if (botAvatarEl) botAvatarEl.classList.remove('thinking-pulse');
        }

        // Typewriter Streaming Engine
        let typewriterQueue = '';
        let displayedText = '';
        let isTypewriterRunning = false;
        let isStreamDone = false;
        let recordedBadges = [];

        window._stopActiveStream = () => {
            isStreamDone = true;
            typewriterQueue = '';
            isTypewriterRunning = false;
            removeThinkingState();
            const stopMsg = (displayedText ? '\n\n' : '') + '*[Response generation stopped by user]*';
            let textContainer = botBodyEl.querySelector('.agent-markdown-text');
            if (textContainer) {
                textContainer.innerHTML = (typeof marked !== 'undefined' ? marked.parse(displayedText + stopMsg) : escapeHtml(displayedText + stopMsg));
            } else {
                botBodyEl.innerHTML = typeof marked !== 'undefined' ? marked.parse(stopMsg) : stopMsg;
            }
            addMessageToCurrentThread('assistant', (displayedText || '') + stopMsg, recordedBadges, botMsgId);
            onGenerationComplete();
        };

        function onGenerationComplete() {
            window._stopActiveStream = null;
            isGenerating = false;
            currentAbortController = null;
            updateSendButtonState();
            if (loadingIndicator) loadingIndicator.classList.add('hidden');

            // Process next prompt in queue if any exists!
            if (promptQueue.length > 0) {
                const nextItem = promptQueue.shift();
                updateQueueUI();
                setTimeout(() => {
                    handleSendPrompt(nextItem.prompt, nextItem.elementId);
                }, 300);
            }
        }

        function processTypewriterTick() {
            if (typewriterQueue.length > 0) {
                const qLen = typewriterQueue.length;
                let stepSize = 24;
                if (isStreamDone) stepSize = qLen; // flush instantly when stream completes
                else if (qLen > 300) stepSize = 160;
                else if (qLen > 100) stepSize = 80;
                else if (qLen > 40) stepSize = 40;

                const chunk = typewriterQueue.slice(0, stepSize);
                typewriterQueue = typewriterQueue.slice(stepSize);
                displayedText += chunk;

                let textContainer = botBodyEl.querySelector('.agent-markdown-text');
                if (!textContainer) {
                    textContainer = document.createElement('div');
                    textContainer.className = 'agent-markdown-text';
                    botBodyEl.appendChild(textContainer);
                }
                textContainer.innerHTML = (typeof marked !== 'undefined' ? marked.parse(displayedText) : escapeHtml(displayedText)) + '<span class="streaming-cursor"></span>';
            }

            if (typewriterQueue.length > 0 || !isStreamDone) {
                setTimeout(processTypewriterTick, 4);
            } else {
                isTypewriterRunning = false;
                let textContainer = botBodyEl.querySelector('.agent-markdown-text');
                if (textContainer && displayedText) {
                    textContainer.innerHTML = typeof marked !== 'undefined' ? marked.parse(displayedText) : escapeHtml(displayedText);
                }
                if (displayedText) {
                    addMessageToCurrentThread('assistant', displayedText, recordedBadges, botMsgId);
                }
                fetchModelsCatalog();
                onGenerationComplete();
            }
        }

        function enqueueIncomingChunk(text) {
            removeThinkingState();
            typewriterQueue += text;
            if (!isTypewriterRunning) {
                isTypewriterRunning = true;
                processTypewriterTick();
            }
        }

        try {
            const response = await fetch('/api/chat-agent', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                signal: currentAbortController.signal,
                body: JSON.stringify({
                    prompt: prompt,
                    location_id: ghlConfig.locationId,
                    access_token: ghlConfig.accessToken,
                    selected_model: modelSelector ? modelSelector.value : 'gemini-3.6-flash',
                    history: history,
                    attachments: currentAttachments
                })
            });

            if (!response.ok) {
                removeThinkingState();
                const errData = await response.json().catch(() => ({ detail: response.statusText }));
                const errMsg = `⚠️ **Error (${response.status}):** ${errData.detail || 'Execution failed.'}`;
                botBodyEl.innerHTML = typeof marked !== 'undefined' ? marked.parse(errMsg) : errMsg;
                addMessageToCurrentThread('assistant', errMsg, [], botMsgId);
                onGenerationComplete();
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
                                removeThinkingState();
                                const toolBadge = document.createElement('div');
                                toolBadge.className = 'tool-execution-badge';
                                toolBadge.innerHTML = `⚡ Invoking GHL API: <strong>${data.name}</strong> (${escapeHtml(JSON.stringify(data.args))})`;
                                botBodyEl.appendChild(toolBadge);
                                recordedBadges.push({ type: 'tool_start', text: toolBadge.innerHTML });
                            } else if (data.type === 'tool_result') {
                                removeThinkingState();
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
                            } else if (data.type === 'chunk') {
                                enqueueIncomingChunk(data.text || '');
                            } else if (data.type === 'done') {
                                isStreamDone = true;
                            }
                        } catch (e) {
                            console.warn('JSON parse error:', e);
                        }
                    }
                }
            }

            isStreamDone = true;
            if (!isTypewriterRunning) {
                removeThinkingState();
                onGenerationComplete();
            }
        } catch (err) {
            removeThinkingState();
            if (err.name === 'AbortError') {
                isStreamDone = true;
                typewriterQueue = '';
                isTypewriterRunning = false;
                const stopMsg = (displayedText ? '\n\n' : '') + '*[Response generation stopped by user]*';
                let textContainer = botBodyEl.querySelector('.agent-markdown-text');
                if (textContainer) {
                    textContainer.innerHTML = (typeof marked !== 'undefined' ? marked.parse(displayedText + stopMsg) : escapeHtml(displayedText + stopMsg));
                } else {
                    botBodyEl.innerHTML = typeof marked !== 'undefined' ? marked.parse(stopMsg) : stopMsg;
                }
                addMessageToCurrentThread('assistant', (displayedText || '') + stopMsg, recordedBadges, botMsgId);
            } else {
                const errStr = `⚠️ **Connection Error:** ${err.message}`;
                botBodyEl.innerHTML = typeof marked !== 'undefined' ? marked.parse(errStr) : errStr;
                addMessageToCurrentThread('assistant', errStr, [], botMsgId);
            }
            onGenerationComplete();
        }
    }

    function appendMessageUI(role, content, messageId = null, isQueued = false, customElementId = null, attachments = []) {
        const msgWrap = document.createElement('div');
        const id = customElementId || messageId || ('msg_' + Date.now());
        msgWrap.id = id;
        msgWrap.className = `message-wrapper ${role} ${isQueued ? 'queued-message' : ''}`;
        msgWrap.setAttribute('data-content', content);

        let attachmentsHtml = '';
        if (attachments && attachments.length > 0) {
            attachmentsHtml = `
                <div class="user-attachments-grid">
                    ${attachments.map(att => {
                        const isImg = att.type === 'image' || (att.mime_type && att.mime_type.startsWith('image/'));
                        if (isImg) {
                            return `<img src="${att.data}" class="user-att-preview-img" alt="${escapeHtml(att.name)}" title="${escapeHtml(att.name)}" onclick="window.open('${att.data}', '_blank')">`;
                        } else {
                            return `<div class="user-att-doc-pill"><span>${getFileIcon(att.name)}</span> <span>${escapeHtml(att.name)}</span></div>`;
                        }
                    }).join('')}
                </div>
            `;
        }

        if (role === 'user') {
            msgWrap.innerHTML = `
                <div class="user-body">
                    ${isQueued ? '<div class="queued-status-badge">⏳ Queued — Will generate next</div>' : ''}
                    ${attachmentsHtml}
                    <div>${escapeHtml(content)}</div>
                </div>
                <div class="user-avatar">👤</div>
                <div class="message-actions-bar">
                    <button type="button" class="msg-action-btn copy-msg-btn" title="Copy Message">📋</button>
                    <button type="button" class="msg-action-btn delete delete-msg-btn" title="Delete Message">🗑️</button>
                </div>
            `;
        }
        messagesList.appendChild(msgWrap);
        bindMessageActions(msgWrap, id);
        return msgWrap;
    }

    function renderAssistantMessageUI(msg) {
        const msgWrap = document.createElement('div');
        const id = msg.id || ('msg_' + Date.now());
        msgWrap.id = id;
        msgWrap.className = 'message-wrapper assistant';
        msgWrap.setAttribute('data-content', msg.content || '');

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
            <div class="message-actions-bar">
                <button type="button" class="msg-action-btn copy-msg-btn" title="Copy Response">📋</button>
                <button type="button" class="msg-action-btn delete delete-msg-btn" title="Delete Message">🗑️</button>
            </div>
        `;
        messagesList.appendChild(msgWrap);
        bindMessageActions(msgWrap, id);
    }

    function bindMessageActions(msgWrap, messageId) {
        const copyBtn = msgWrap.querySelector('.copy-msg-btn');
        const deleteBtn = msgWrap.querySelector('.delete-msg-btn');

        if (copyBtn) {
            copyBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const text = msgWrap.getAttribute('data-content') || msgWrap.querySelector('.agent-markdown-text, .user-body')?.textContent || '';
                navigator.clipboard.writeText(text).then(() => {
                    copyBtn.textContent = '✓';
                    setTimeout(() => { copyBtn.textContent = '📋'; }, 1500);
                });
            });
        }

        if (deleteBtn) {
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                deleteMessageFromThread(messageId, msgWrap);
            });
        }
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

