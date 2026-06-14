document.addEventListener('DOMContentLoaded', function () {
    // Loading state on form submit
    const loginForm = document.getElementById('loginForm');
    const loginBtn = document.getElementById('loginBtn');
    const loginBtnText = document.getElementById('loginBtnText');
    const loginBtnSpinner = document.getElementById('loginBtnSpinner');

    if (loginForm && loginBtn && loginBtnText && loginBtnSpinner) {
        loginForm.addEventListener('submit', function () {
            loginBtn.disabled = true;
            loginBtnText.textContent = 'Sedang login...';
            loginBtnSpinner.style.display = 'inline-block';
        });
    }

    // Password visibility toggle
    const togglePassword = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('passwordInput');
    const toggleIcon = document.getElementById('toggleIcon');

    if (!togglePassword || !passwordInput || !toggleIcon) return;

    const syncIcon = () => {
        const isPassword = passwordInput.type === 'password';
        if (isPassword) {
            toggleIcon.classList.remove('bi-eye-slash');
            toggleIcon.classList.add('bi-eye');
        } else {
            toggleIcon.classList.remove('bi-eye');
            toggleIcon.classList.add('bi-eye-slash');
        }
    };

    syncIcon();

    // Use click handler (external script avoids inline CSP issues)
    togglePassword.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();

        passwordInput.type = passwordInput.type === 'password' ? 'text' : 'password';
        syncIcon();
        passwordInput.focus();
    });
});
