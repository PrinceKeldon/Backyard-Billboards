/**
 * Backyard Billboards - Main JavaScript
 */

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Theme toggle functionality
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    const themeText = document.getElementById('theme-text');
    const htmlElement = document.documentElement;
    
    // Check for saved theme preference or use default (dark)
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);
    
    // Toggle theme when button is clicked
    themeToggle.addEventListener('click', () => {
        const currentTheme = htmlElement.getAttribute('data-bs-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
        localStorage.setItem('theme', newTheme);
    });
    
    // Set theme to either light or dark
    function setTheme(theme) {
        htmlElement.setAttribute('data-bs-theme', theme);
        const footer = document.getElementById('main-footer');
        const navbar = document.getElementById('main-navbar');
        
        // Apply smooth transitions
        document.body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
        
        if (theme === 'dark') {
            themeIcon.classList.remove('fa-sun');
            themeIcon.classList.add('fa-moon');
            themeText.textContent = 'Light Mode';
            
            // Dark theme always requires navbar-dark for proper contrast
            navbar.classList.add('navbar-dark');
            navbar.classList.remove('navbar-light');
            
            // The gradient background is handled by CSS, so we don't need to toggle bg-dark/light
            // We just need to make sure we're using the right text contrast classes
        } else {
            themeIcon.classList.remove('fa-moon');
            themeIcon.classList.add('fa-sun');
            themeText.textContent = 'Dark Mode';
            
            // Light theme might look better with dark text on our gradient navbar
            navbar.classList.remove('navbar-dark');
            navbar.classList.add('navbar-light');
        }
        
        // Add a nice animation effect
        document.body.classList.add('theme-transition');
        setTimeout(() => {
            document.body.classList.remove('theme-transition');
        }, 500);
        
        // Update button styles based on theme
        updateButtonStyles(theme);
    }
    
    // Update button styles based on theme
    function updateButtonStyles(theme) {
        const themeToggle = document.getElementById('theme-toggle');
        
        if (theme === 'dark') {
            themeToggle.classList.remove('btn-dark');
            themeToggle.classList.add('btn-outline-light');
        } else {
            themeToggle.classList.remove('btn-outline-light');
            themeToggle.classList.add('btn-outline-primary');
        }
    }
    
    // Format dates using time ago
    function timeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const seconds = Math.floor((now - date) / 1000);
        
        // Time intervals in seconds
        const intervals = {
            year: 31536000,
            month: 2592000,
            week: 604800,
            day: 86400,
            hour: 3600,
            minute: 60,
            second: 1
        };
        
        // Check each interval
        for (const [unit, secondsInUnit] of Object.entries(intervals)) {
            const interval = Math.floor(seconds / secondsInUnit);
            
            if (interval >= 1) {
                return interval + ' ' + unit + (interval > 1 ? 's' : '') + ' ago';
            }
        }
        
        return 'just now';
    }
    
    // Apply time ago to elements with data-time attribute
    document.querySelectorAll('[data-time]').forEach(element => {
        const timeStr = element.getAttribute('data-time');
        if (timeStr) {
            element.textContent = timeAgo(timeStr);
        }
    });
    
    // Enable card hover effects
    const dealCards = document.querySelectorAll('.deal-card');
    dealCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.classList.add('shadow-lg');
        });
        
        card.addEventListener('mouseleave', function() {
            this.classList.remove('shadow-lg');
        });
    });
    
    // Handle form validation
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

// Register custom filter for Jinja templates to display time ago
// Note: This is just for reference, as it would be implemented on the server side
function registerTimeAgoFilter() {
    // This would be implemented in Python, shown here for documentation
    // In the actual implementation, we'd use the utils.py get_time_ago function
    console.log('Time ago filter would be registered server-side');
}
