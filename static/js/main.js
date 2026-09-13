/**
 * Smart Parking Management System - JavaScript Interactions
 * Vanilla JavaScript implementation
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Auto-hide Django Messages after 4 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 4000);
    });

    // 2. Mobile Sidebar Toggle & Overlay
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarOverlay = document.getElementById('sidebarOverlay');

    if (sidebarToggle && sidebar && sidebarOverlay) {
        sidebarToggle.addEventListener('click', function () {
            sidebar.classList.toggle('sidebar-open');
            sidebarOverlay.classList.toggle('show');
        });

        sidebarOverlay.addEventListener('click', function () {
            sidebar.classList.remove('sidebar-open');
            sidebarOverlay.classList.remove('show');
        });
    }

    // 3. Delete Confirmation Prompts
    const deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            const message = btn.getAttribute('data-confirm-delete') || 'Are you sure you want to proceed with this deletion? This action cannot be undone.';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // 4. Visual Slot Card Quick Booking Selection
    const slotCards = document.querySelectorAll('.slot-card.status-available');
    slotCards.forEach(function (card) {
        card.style.cursor = 'pointer';
        card.addEventListener('click', function (e) {
            // Avoid double navigation if clicking an anchor inside
            if (e.target.tagName.toLowerCase() !== 'a') {
                const bookUrl = card.getAttribute('data-book-url');
                if (bookUrl) {
                    window.location.href = bookUrl;
                }
            }
        });
    });

    // 5. Initialize Bootstrap Tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
