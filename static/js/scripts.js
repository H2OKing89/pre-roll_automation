// static/js/scripts.js

document.addEventListener('DOMContentLoaded', function() {
    console.log('JavaScript is loaded and running.');

    // Theme Toggle Functionality
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    const currentTheme = localStorage.getItem('theme') || 'light';

    if (currentTheme === 'dark') {
        document.body.classList.add('dark-theme');
    }

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', function() {
            document.body.classList.toggle('dark-theme');
            let theme = 'light';
            if (document.body.classList.contains('dark-theme')) {
                theme = 'dark';
            }
            localStorage.setItem('theme', theme);
        });
    }
});
