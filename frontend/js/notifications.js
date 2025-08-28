// frontend/js/notifications.js

function showNotification(message, type = 'info', duration = 3000) {
    const container = document.querySelector('.notification-container') || createContainer();

    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;

    container.appendChild(notification);

    // Animate in
    setTimeout(() => {
        notification.classList.add('show');
    }, 10); // Small delay to allow for CSS transition

    // Animate out and remove
    setTimeout(() => {
        notification.classList.remove('show');
        notification.addEventListener('transitionend', () => {
            notification.remove();
            if (container.childElementCount === 0) {
                container.remove();
            }
        });
    }, duration);
}

function createContainer() {
    const container = document.createElement('div');
    container.className = 'notification-container';
    document.body.appendChild(container);
    return container;
}

// Make it globally available
window.showNotification = showNotification;
