/**
 * BlueGhost Main SocketIO Application Controller
 */
document.addEventListener('DOMContentLoaded', () => {
    // Connect to SocketIO server
    const socket = io();

    const myGhostName = document.getElementById('myGhostName') ? document.getElementById('myGhostName').innerText.trim() : 'Ghost';
    let activeDevice = null;
    let selectedSelfDestructSeconds = 0;
    let pendingFileAttachment = null;
    let typingTimeout = null;

    BlueGhostUI.init();
    BlueGhostEmoji.init('emojiPicker', 'messageInput');

    // Socket IO Connection Events
    socket.on('connect', () => {
        console.log('Connected to BlueGhost WebSocket Server');
        socket.emit('start_scan');
    });

    socket.on('scan_results', (data) => {
        const devices = data.devices || [];
        BlueGhostBluetooth.renderDevices('devicesList', 'deviceCount', devices, data.ble_error);
    });

    // Handle Bluetooth connection status changes
    socket.on('connection_status', (data) => {
        const status = data.status;
        const device = data.device;

        if (status === 'connected') {
            activeDevice = device;
            BlueGhostBluetooth.setSelectedDevice(device);
            updateActiveDeviceUI(device, 'connected');
            BlueGhostAudio.play('connected');
            BlueGhostUI.toggleReconnectBanner(false);

            // Fetch chat history for this device
            socket.emit('get_history', { target_ghost: device.ghost_name });

        } else if (status === 'out_of_range' || status === 'reconnecting') {
            BlueGhostUI.toggleReconnectBanner(true, device ? device.ghost_name : 'Ghost');
            BlueGhostAudio.play('disconnected');

        } else if (status === 'disconnected') {
            activeDevice = null;
            updateActiveDeviceUI(null, 'disconnected');
            BlueGhostAudio.play('disconnected');
            BlueGhostUI.toggleReconnectBanner(false);
        }
    });

    // Handle chat history response
    socket.on('chat_history', (data) => {
        const messages = data.messages || [];
        const container = document.getElementById('chatMessages');
        container.innerHTML = '';
        if (messages.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted my-auto" id="emptyChatPlaceholder">
                    <i class="fa-solid fa-ghost fa-3x mb-3 text-secondary opacity-50"></i>
                    <h5>Connected to ${activeDevice ? activeDevice.ghost_name : 'Ghost'}</h5>
                    <p class="small">Start an encrypted offline Bluetooth conversation.</p>
                </div>
            `;
        } else {
            messages.forEach(msg => {
                BlueGhostChat.renderMessage('chatMessages', msg, myGhostName);
            });
        }
    });

    // Handle incoming message
    socket.on('new_message', (msg) => {
        if (msg.sender_ghost !== myGhostName) {
            BlueGhostAudio.play('message_received');
            BlueGhostUI.showNotification(msg.sender_ghost, msg.msg_type === 'text' ? msg.content : `Sent an ${msg.msg_type}`);
            
            // Mark as read
            socket.emit('mark_read', { sender_ghost: msg.sender_ghost });
        }
        BlueGhostChat.renderMessage('chatMessages', msg, myGhostName);
    });

    // Handle message sent confirmation
    socket.on('message_sent_confirm', (msg) => {
        BlueGhostAudio.play('message_sent');
        BlueGhostChat.renderMessage('chatMessages', msg, myGhostName);
    });

    // Typing Haunting status listener
    socket.on('user_typing', (data) => {
        if (data.sender_ghost !== myGhostName) {
            const indicator = document.getElementById('typingIndicator');
            const typingText = document.getElementById('typingText');
            if (indicator && typingText) {
                typingText.innerText = `${data.sender_ghost} is haunting...`;
                indicator.classList.remove('d-none');

                clearTimeout(typingTimeout);
                typingTimeout = setTimeout(() => {
                    indicator.classList.add('d-none');
                }, 3000);
            }
        }
    });

    // Bluetooth scanner button
    const scanBtn = document.getElementById('scanBtn');
    if (scanBtn) {
        scanBtn.addEventListener('click', () => {
            const icon = document.getElementById('scanIcon');
            if (icon) icon.classList.add('fa-spin');
            socket.emit('start_scan');
            setTimeout(() => {
                if (icon) icon.classList.remove('fa-spin');
            }, 3000);
        });
    }

    // Connect button click in device list
    BlueGhostBluetooth.onConnect((device) => {
        socket.emit('connect_device', { address: device.address, device: device });
    });

    // Disconnect button
    const disconnectBtn = document.getElementById('disconnectBtn');
    if (disconnectBtn) {
        disconnectBtn.addEventListener('click', () => {
            socket.emit('disconnect_device');
        });
    }

    // Sound toggle button
    const soundToggleBtn = document.getElementById('soundToggleBtn');
    if (soundToggleBtn) {
        soundToggleBtn.addEventListener('click', () => {
            const enabled = BlueGhostAudio.toggleSound();
            const icon = document.getElementById('soundIcon');
            if (icon) {
                icon.className = enabled ? 'fa-solid fa-volume-high text-info' : 'fa-solid fa-volume-xmark text-muted';
            }
        });
    }

    // Emoji toggle
    const emojiToggleBtn = document.getElementById('emojiToggleBtn');
    if (emojiToggleBtn) {
        emojiToggleBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            BlueGhostEmoji.toggle('emojiPicker');
        });
    }
    document.addEventListener('click', () => {
        const picker = document.getElementById('emojiPicker');
        if (picker && !picker.classList.contains('d-none')) {
            picker.classList.add('d-none');
        }
    });

    // Self-destruct dropdown selector
    document.querySelectorAll('.dropdown-item[data-seconds]').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            document.querySelectorAll('.dropdown-item[data-seconds]').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            selectedSelfDestructSeconds = parseInt(item.getAttribute('data-seconds'), 10);
            document.getElementById('selectedTimerLabel').innerText = item.innerText.split(' ')[0];
        });
    });

    // Typing haunting broadcast
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.addEventListener('input', () => {
            if (activeDevice) {
                socket.emit('typing', { receiver_ghost: activeDevice.ghost_name });
            }
        });
    }

    // Image & File attachments
    const btnAttachImage = document.getElementById('btnAttachImage');
    const imageInput = document.getElementById('imageInput');
    const btnAttachFile = document.getElementById('btnAttachFile');
    const fileInput = document.getElementById('fileInput');

    if (btnAttachImage && imageInput) {
        btnAttachImage.addEventListener('click', () => imageInput.click());
        imageInput.addEventListener('change', (e) => handleFileSelected(e.target.files[0], 'image'));
    }

    if (btnAttachFile && fileInput) {
        btnAttachFile.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => handleFileSelected(e.target.files[0], 'file'));
    }

    const cancelPreviewBtn = document.getElementById('cancelPreviewBtn');
    if (cancelPreviewBtn) {
        cancelPreviewBtn.addEventListener('click', clearFilePreview);
    }

    function handleFileSelected(file, type) {
        if (!file) return;
        pendingFileAttachment = { file: file, type: type };
        
        const previewBar = document.getElementById('filePreviewBar');
        const previewName = document.getElementById('previewFileName');
        const previewSize = document.getElementById('previewFileSize');
        const previewIcon = document.getElementById('previewIcon');

        if (previewName) previewName.innerText = file.name;
        if (previewSize) previewSize.innerText = `${(file.size / 1024).toFixed(1)} KB`;
        if (previewIcon) {
            previewIcon.className = type === 'image' ? 'fa-solid fa-image text-info' : 'fa-solid fa-file text-purple';
        }
        if (previewBar) previewBar.classList.remove('d-none');
    }

    function clearFilePreview() {
        pendingFileAttachment = null;
        if (imageInput) imageInput.value = '';
        if (fileInput) fileInput.value = '';
        const previewBar = document.getElementById('filePreviewBar');
        if (previewBar) previewBar.classList.add('d-none');
    }

    // Message Form Submit
    const messageForm = document.getElementById('messageForm');
    if (messageForm) {
        messageForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!activeDevice) {
                alert('Please select and connect to a nearby Bluetooth Ghost first!');
                return;
            }

            const textContent = messageInput.value.trim();
            if (!textContent && !pendingFileAttachment) return;

            let fileData = null;
            if (pendingFileAttachment) {
                const formData = new FormData();
                formData.append('file', pendingFileAttachment.file);
                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });
                    fileData = await response.json();
                } catch (err) {
                    console.error('File upload failed:', err);
                    alert('Failed to send file attachment.');
                    return;
                }
            }

            const payload = {
                receiver_ghost: activeDevice.ghost_name,
                content: textContent,
                msg_type: pendingFileAttachment ? pendingFileAttachment.type : 'text',
                file_path: fileData ? fileData.file_path : null,
                file_name: fileData ? fileData.file_name : null,
                file_size: fileData ? fileData.file_size : 0,
                self_destruct_seconds: selectedSelfDestructSeconds
            };

            socket.emit('send_message', payload);

            messageInput.value = '';
            clearFilePreview();
        });
    }

    function updateActiveDeviceUI(device, status) {
        const activeGhostName = document.getElementById('activeGhostName');
        const activeDeviceMeta = document.getElementById('activeDeviceMeta');
        const activeAvatar = document.getElementById('activeAvatar');
        const connectedBadge = document.getElementById('connectedBadge');
        const disconnectBtn = document.getElementById('disconnectBtn');

        if (status === 'connected' && device) {
            if (activeGhostName) activeGhostName.innerText = device.ghost_name;
            if (activeDeviceMeta) activeDeviceMeta.innerText = `Online • Distance: ${device.distance}m • ${device.address}`;
            if (activeAvatar) activeAvatar.innerText = device.avatar || '👻';
            if (connectedBadge) connectedBadge.classList.remove('d-none');
            if (disconnectBtn) disconnectBtn.classList.remove('d-none');
        } else {
            if (activeGhostName) activeGhostName.innerText = 'Select a nearby Ghost to chat';
            if (activeDeviceMeta) activeDeviceMeta.innerText = 'Offline • Bluetooth Channel';
            if (activeAvatar) activeAvatar.innerText = '👻';
            if (connectedBadge) connectedBadge.classList.add('d-none');
            if (disconnectBtn) disconnectBtn.classList.add('d-none');
        }
    }

    // Copy Phone URL Button
    const copyUrlBtn = document.getElementById('copyUrlBtn');
    if (copyUrlBtn) {
        copyUrlBtn.addEventListener('click', () => {
            const phoneUrlText = document.getElementById('phoneUrlDisplay') ? document.getElementById('phoneUrlDisplay').innerText.trim() : '';
            if (phoneUrlText) {
                navigator.clipboard.writeText(phoneUrlText).then(() => {
                    const btnText = document.getElementById('copyBtnText');
                    if (btnText) btnText.innerText = 'Copied!';
                    setTimeout(() => {
                        if (btnText) btnText.innerText = 'Copy';
                    }, 2000);
                });
            }
        });
    }
});
