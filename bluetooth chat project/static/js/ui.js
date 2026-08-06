/**
 * BlueGhost UI Helper & Notification Manager
 */
const BlueGhostUI = (function() {

    function init() {
        requestNotificationPermission();
    }

    function requestNotificationPermission() {
        if ('Notification' in window && Notification.permission !== 'granted' && Notification.permission !== 'denied') {
            Notification.requestPermission();
        }
    }

    function showNotification(title, body, icon = '👻') {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(`${icon} ${title}`, {
                body: body,
                icon: '/static/images/logo.png'
            });
        }
    }

    function openImageModal(imgSrc) {
        const modalImg = document.getElementById('modalImg');
        if (modalImg) {
            modalImg.src = imgSrc;
            const modal = new bootstrap.Modal(document.getElementById('imageModal'));
            modal.show();
        }
    }

    function toggleReconnectBanner(show, ghostName = '') {
        const banner = document.getElementById('reconnectBanner');
        const msg = document.getElementById('reconnectMsg');
        if (banner) {
            if (show) {
                if (msg) msg.innerText = `${ghostName || 'Ghost'} moved out of range. Attempting reconnection automatically...`;
                banner.classList.remove('d-none');
            } else {
                banner.classList.add('d-none');
            }
        }
    }

    return {
        init: init,
        showNotification: showNotification,
        openImageModal: openImageModal,
        toggleReconnectBanner: toggleReconnectBanner
    };
})();
