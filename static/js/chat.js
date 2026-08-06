/**
 * BlueGhost Chat Engine & Message Renderer
 */
const BlueGhostChat = (function() {
    const activeTimers = {};

    function renderMessage(containerId, msg, currentGhostName) {
        const container = document.getElementById(containerId);
        if (!container) return;

        // Clear empty placeholder if exists
        const placeholder = document.getElementById('emptyChatPlaceholder');
        if (placeholder) {
            placeholder.remove();
        }

        const isSent = msg.sender_ghost === currentGhostName;
        const msgWrapper = document.createElement('div');
        msgWrapper.className = `msg-wrapper ${isSent ? 'sent' : 'received'}`;
        msgWrapper.id = `msg-${msg.msg_id}`;

        let contentHtml = '';
        if (msg.msg_type === 'image' && msg.file_path) {
            contentHtml = `
                <div>${escapeHtml(msg.content || '')}</div>
                <img src="${msg.file_path}" class="msg-image mt-2" onclick="BlueGhostUI.openImageModal('${msg.file_path}')" alt="Attachment">
            `;
        } else if (msg.msg_type === 'file' && msg.file_path) {
            contentHtml = `
                <div>${escapeHtml(msg.content || '')}</div>
                <a href="${msg.file_path}" download="${msg.file_name || 'attachment'}" class="text-decoration-none">
                    <div class="msg-file-card">
                        <i class="fa-solid fa-file-arrow-down fa-2x text-cyan me-2"></i>
                        <div>
                            <div class="fw-bold text-white small text-truncate" style="max-width: 180px;">${escapeHtml(msg.file_name || 'File')}</div>
                            <div class="text-muted" style="font-size: 0.7rem;">${formatBytes(msg.file_size)}</div>
                        </div>
                    </div>
                </a>
            `;
        } else {
            contentHtml = `<div>${escapeHtml(msg.content)}</div>`;
        }

        let selfDestructBadge = '';
        if (msg.self_destruct_seconds && msg.self_destruct_seconds > 0) {
            selfDestructBadge = `
                <span class="self-destruct-tag" id="timer-badge-${msg.msg_id}">
                    <i class="fa-solid fa-fire"></i> <span class="countdown-val">${msg.self_destruct_seconds}s</span>
                </span>
            `;
        }

        const statusIcon = isSent ? (msg.status === 'read' ? '<i class="fa-solid fa-check-double text-info"></i>' : '<i class="fa-solid fa-check text-muted"></i>') : '';

        msgWrapper.innerHTML = `
            <div class="msg-bubble">
                ${contentHtml}
            </div>
            <div class="msg-meta">
                ${selfDestructBadge}
                <span>${formatTime(msg.timestamp)}</span>
                ${statusIcon}
            </div>
        `;

        container.appendChild(msgWrapper);
        container.scrollTop = container.scrollHeight;

        // Handle live self-destruct countdown timer
        if (msg.self_destruct_seconds && msg.self_destruct_seconds > 0) {
            startCountdownTimer(msg.msg_id, msg.self_destruct_seconds, msg.timestamp, msg.expires_at);
        }
    }

    function startCountdownTimer(msgId, seconds, timestampStr, expiresAtStr) {
        if (activeTimers[msgId]) return;

        let remaining = seconds;
        if (expiresAtStr) {
            const exp = new Date(expiresAtStr + "Z").getTime();
            const now = new Date().getTime();
            remaining = Math.max(0, Math.ceil((exp - now) / 1000));
        }

        const interval = setInterval(() => {
            remaining--;
            const badgeEl = document.querySelector(`#timer-badge-${msgId} .countdown-val`);
            if (badgeEl) {
                badgeEl.innerText = `${remaining}s`;
            }

            if (remaining <= 0) {
                clearInterval(interval);
                delete activeTimers[msgId];
                const msgNode = document.getElementById(`msg-${msgId}`);
                if (msgNode) {
                    msgNode.style.transition = 'all 0.5s ease';
                    msgNode.style.opacity = '0';
                    msgNode.style.transform = 'scale(0.8)';
                    setTimeout(() => {
                        msgNode.remove();
                        BlueGhostAudio.play('ghost_vanished');
                    }, 500);
                }
            }
        }, 1000);

        activeTimers[msgId] = interval;
    }

    function escapeHtml(text) {
        if (!text) return '';
        return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    }

    function formatTime(tsStr) {
        if (!tsStr) return '';
        const d = new Date(tsStr);
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    function formatBytes(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    return {
        renderMessage: renderMessage
    };
})();
