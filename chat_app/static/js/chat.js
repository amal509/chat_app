document.addEventListener('DOMContentLoaded', function () {
    const { roomName, currentUserId, otherUserId } = window.CHAT_CONFIG;
    const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const socket = new WebSocket(`${wsScheme}://${window.location.host}/ws/chat/${roomName}/`);

    const chatBox = document.getElementById('chatBox');
    const msgInput = document.getElementById('msgInput');

    // Send read receipts for unread received messages on socket open
    const unreadIds = [];
    document.querySelectorAll('.msg.received[data-id]').forEach(function (el) {
        unreadIds.push(parseInt(el.dataset.id));
    });
    if (unreadIds.length > 0) {
        socket.addEventListener('open', function () {
            socket.send(JSON.stringify({ type: 'read_receipt', message_ids: unreadIds }));
        });
    }

    socket.onmessage = function (e) {
        const data = JSON.parse(e.data);

        if (data.type === 'message') {
            const isSent = data.sender_id === currentUserId;
            const div = document.createElement('div');
            div.className = `msg ${isSent ? 'sent' : 'received'}`;
            div.dataset.id = data.message_id;
            const menuHtml =
                `<button class="msg-menu-btn">&#8964;</button>` +
                `<div class="msg-menu">` +
                `<button data-msg-id="${data.message_id}" data-delete-type="for_me">Delete for Me</button>` +
                (isSent ? `<button data-msg-id="${data.message_id}" data-delete-type="for_everyone">Delete for Everyone</button>` : '') +
                `</div>`;
            div.innerHTML = menuHtml +
                `<span class="msg-content">${escapeHtml(data.message)}</span>` +
                `<div class="meta"><span class="msg-time">${formatTime(data.timestamp)}</span>` +
                (isSent ? `<span class="tick">${data.is_read ? '&#10003;&#10003;' : '&#10003;'}</span>` : '') +
                `</div>`;
            chatBox.appendChild(div);
            chatBox.scrollTop = chatBox.scrollHeight;

            if (!isSent) {
                socket.send(JSON.stringify({ type: 'read_receipt', message_ids: [data.message_id] }));
            }
        }

        if (data.type === 'read_receipt') {
            data.message_ids.forEach(function (id) {
                const el = document.querySelector(`.msg[data-id="${id}"]`);
                if (el) {
                    const tick = el.querySelector('.tick');
                    if (tick) {
                        tick.classList.add('read');
                        tick.innerHTML = '&#10003;&#10003;';
                    }
                }
            });
        }

        if (data.type === 'message_deleted') {
            const el = document.querySelector(`.msg[data-id="${data.message_id}"]`);
            if (el) {
                if (data.delete_type === 'for_everyone') {
                    el.classList.add('is-deleted');
                    el.querySelector('.msg-menu-btn')?.remove();
                    el.querySelector('.msg-menu')?.remove();
                    const content = el.querySelector('.msg-content');
                    if (content) content.textContent = '🚫 This message was deleted';
                    el.querySelector('.tick')?.remove();
                } else {
                    el.remove();
                }
            }
        }
    };

    socket.onclose = function () {
        console.log('WebSocket disconnected.');
    };

    function sendMessage() {
        const message = msgInput.value.trim();
        if (message === '') return;
        socket.send(JSON.stringify({
            type: 'message',
            message: message,
            receiver_id: otherUserId,
        }));
        msgInput.value = '';
    }

    document.getElementById('sendBtn').addEventListener('click', sendMessage);
    msgInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') sendMessage();
    });

    // Unified click handler: context menu toggle + delete via event delegation
    document.addEventListener('click', function (e) {
        const deleteBtn = e.target.closest('.msg-menu button[data-msg-id]');
        if (deleteBtn) {
            document.querySelectorAll('.msg-menu.show').forEach(function (m) { m.classList.remove('show'); });
            socket.send(JSON.stringify({
                type: 'delete_message',
                message_id: parseInt(deleteBtn.dataset.msgId),
                delete_type: deleteBtn.dataset.deleteType,
            }));
            return;
        }

        if (e.target.classList.contains('msg-menu-btn')) {
            e.stopPropagation();
            const menu = e.target.nextElementSibling;
            const isOpen = menu.classList.contains('show');
            document.querySelectorAll('.msg-menu.show').forEach(function (m) { m.classList.remove('show'); });
            if (!isOpen) menu.classList.add('show');
            return;
        }

        document.querySelectorAll('.msg-menu.show').forEach(function (m) { m.classList.remove('show'); });
    });

    // Format message timestamps on page load
    document.querySelectorAll('.msg-time[data-iso]').forEach(function (el) {
        el.textContent = formatTime(el.dataset.iso);
    });

    // Format last-seen on page load
    const statusEl = document.querySelector('.header .info .status');
    if (statusEl) {
        statusEl.textContent = formatLastSeen(statusEl.dataset.lastSeenIso, statusEl.dataset.isOnline === 'true');
    }

    chatBox.scrollTop = chatBox.scrollHeight;

    // Presence WebSocket
    const presenceSocket = new WebSocket(`${wsScheme}://${window.location.host}/ws/presence/`);
    presenceSocket.onmessage = function (e) {
        const data = JSON.parse(e.data);
        if (data.type === 'presence_update' && data.user_id === otherUserId) {
            const st = document.querySelector('.header .info .status');
            st.dataset.isOnline = data.is_online ? 'true' : 'false';
            if (data.last_seen_iso) st.dataset.lastSeenIso = data.last_seen_iso;
            st.textContent = formatLastSeen(data.last_seen_iso, data.is_online);
        }
    };
});
