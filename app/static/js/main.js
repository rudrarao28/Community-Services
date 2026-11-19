/**
 * University Library Management System
 * Core UI/UX JavaScript (Dark mode, Toasts, Validation, Modals)
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Dark Mode Management
    const themeToggleBtn = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');
    const htmlElement = document.documentElement;

    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const currentTheme = htmlElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            setTheme(newTheme);
        });
    }

    function setTheme(theme) {
        htmlElement.setAttribute('data-bs-theme', theme);
        localStorage.setItem('theme', theme);
        if (themeIcon) {
            if (theme === 'dark') {
                themeIcon.classList.remove('bi-moon-stars');
                themeIcon.classList.add('bi-sun');
            } else {
                themeIcon.classList.remove('bi-sun');
                themeIcon.classList.add('bi-moon-stars');
            }
        }
    }

    // 2. Admin Sidebar Toggle for Small Screens
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('show');
        });
    }

    // 3. Initialize Bootstrap Toasts
    const toastElList = [].slice.call(document.querySelectorAll('.toast'));
    toastElList.map(toastEl => {
        const toast = new bootstrap.Toast(toastEl, { delay: 6000 });
        toast.show();
    });

    // 4. Client-side Form Validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
});

/**
 * Universal Action Confirmation Modal Trigger
 * @param {string} title - Modal heading
 * @param {string} message - Warning message
 * @param {string} formAction - URL or form target
 * @param {string} btnClass - Button variant (btn-danger, btn-primary)
 * @param {string} btnText - Confirm button text
 */
function confirmAction(title, message, formAction, btnClass = 'btn-danger', btnText = 'Confirm') {
    let modal = document.getElementById('universalConfirmModal');
    if (!modal) {
        const modalHtml = `
        <div class="modal fade" id="universalConfirmModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="universalConfirmTitle">Confirm Action</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body" id="universalConfirmBody">
                        Are you sure you want to proceed?
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <form id="universalConfirmForm" method="POST" action="">
                            <input type="hidden" name="csrf_token" value="${window.CSRF_TOKEN || ''}">
                            <button type="submit" id="universalConfirmSubmitBtn" class="btn btn-danger">Confirm</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>`;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        modal = document.getElementById('universalConfirmModal');
    }

    document.getElementById('universalConfirmTitle').innerText = title;
    document.getElementById('universalConfirmBody').innerHTML = message;
    const form = document.getElementById('universalConfirmForm');
    form.action = formAction;
    
    const submitBtn = document.getElementById('universalConfirmSubmitBtn');
    submitBtn.className = `btn ${btnClass}`;
    submitBtn.innerText = btnText;

    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}
