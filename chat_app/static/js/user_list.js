document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.user-last-seen').forEach(function (el) {
        el.textContent = formatLastSeen(el.dataset.lastSeenIso, el.dataset.isOnline === 'true');
    });

    const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const presenceSocket = new WebSocket(`${wsScheme}://${window.location.host}/ws/presence/`);

    presenceSocket.onmessage = function (e) {
        const data = JSON.parse(e.data);

        if (data.type === 'presence_update') {
            const dot = document.querySelector(`.status-dot[data-user-id="${data.user_id}"]`);
            if (dot) dot.classList.toggle('online', data.is_online);

            const lastSeenEl = document.querySelector(`.user-last-seen[data-user-id="${data.user_id}"]`);
            if (lastSeenEl) {
                lastSeenEl.dataset.isOnline = data.is_online ? 'true' : 'false';
                if (data.last_seen_iso) lastSeenEl.dataset.lastSeenIso = data.last_seen_iso;
                lastSeenEl.textContent = formatLastSeen(data.last_seen_iso, data.is_online);
            }
        }

        if (data.type === 'unread_count_update') {
            const badge = document.querySelector(`.unread-badge[data-user-id="${data.sender_id}"]`);
            if (badge) {
                if (data.count > 0) {
                    badge.textContent = data.count_display;
                    badge.style.display = 'flex';
                } else {
                    badge.style.display = 'none';
                }
            }
        }
    };
});
