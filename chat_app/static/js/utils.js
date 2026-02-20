function formatTime(isoStr) {
    return new Date(isoStr).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function formatLastSeen(isoStr, isOnline) {
    if (isOnline) return 'Online';
    if (!isoStr) return 'Offline';
    const lastSeen = new Date(isoStr);
    const now = new Date();
    const diffSeconds = (now - lastSeen) / 1000;
    if (diffSeconds < 60) return 'Last seen just now';
    const timeStr = lastSeen.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);
    if (lastSeen.toDateString() === now.toDateString()) return `Last seen today at ${timeStr}`;
    if (lastSeen.toDateString() === yesterday.toDateString()) return `Last seen yesterday at ${timeStr}`;
    return `Last seen ${lastSeen.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}
