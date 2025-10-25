// Dark Mode Toggle Functionality
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    // Update navigation toggle button text
    const toggleText = document.querySelector('.theme-toggle-text');
    const toggleIcon = document.querySelector('.theme-toggle-icon');
    
    if (toggleText && toggleIcon) {
        if (newTheme === 'dark') {
            toggleText.textContent = 'Light';
            toggleIcon.textContent = '☀️';
        } else {
            toggleText.textContent = 'Dark';
            toggleIcon.textContent = '🌙';
        }
    }
    
    // Update profile page theme toggle
    const profileToggleTitle = document.querySelector('.theme-toggle-title');
    const profileToggleDescription = document.querySelector('.theme-toggle-description');
    const profileToggleIcon = document.querySelector('.theme-toggle-icon-large');
    
    if (profileToggleTitle && profileToggleDescription && profileToggleIcon) {
        if (newTheme === 'dark') {
            profileToggleTitle.textContent = 'Light Mode';
            profileToggleDescription.textContent = 'Switch to light theme';
            profileToggleIcon.textContent = '☀️';
        } else {
            profileToggleTitle.textContent = 'Dark Mode';
            profileToggleDescription.textContent = 'Switch to dark theme';
            profileToggleIcon.textContent = '🌙';
        }
    }
}

// Initialize theme on page load
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    const html = document.documentElement;
    
    html.setAttribute('data-theme', savedTheme);
    
    // Update navigation toggle button based on saved theme
    const toggleText = document.querySelector('.theme-toggle-text');
    const toggleIcon = document.querySelector('.theme-toggle-icon');
    
    if (toggleText && toggleIcon) {
        if (savedTheme === 'dark') {
            toggleText.textContent = 'Light';
            toggleIcon.textContent = '☀️';
        } else {
            toggleText.textContent = 'Dark';
            toggleIcon.textContent = '🌙';
        }
    }
    
    // Update profile page theme toggle based on saved theme
    const profileToggleTitle = document.querySelector('.theme-toggle-title');
    const profileToggleDescription = document.querySelector('.theme-toggle-description');
    const profileToggleIcon = document.querySelector('.theme-toggle-icon-large');
    
    if (profileToggleTitle && profileToggleDescription && profileToggleIcon) {
        if (savedTheme === 'dark') {
            profileToggleTitle.textContent = 'Light Mode';
            profileToggleDescription.textContent = 'Switch to light theme';
            profileToggleIcon.textContent = '☀️';
        } else {
            profileToggleTitle.textContent = 'Dark Mode';
            profileToggleDescription.textContent = 'Switch to dark theme';
            profileToggleIcon.textContent = '🌙';
        }
    }
}

// Auto-initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeTheme);
