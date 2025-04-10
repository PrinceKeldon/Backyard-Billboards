/**
 * Backyard Billboards - Main JavaScript
 */

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the animated cityscape background
    initCityscape();
    
    // Update cityscape periodically to reflect current time
    setInterval(updateCityscape, 60000); // Update every minute
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

/**
 * Cityscape Animation
 * Mimics Berlin's skyline and changes based on the time of day
 */

// Initialize the cityscape
function initCityscape() {
    // Create windows for buildings
    createBuildingWindows();
    
    // Create stars (they will be hidden/shown based on time)
    createStars();
    
    // Set initial cityscape appearance based on current time
    updateCityscape();
}

// Update cityscape appearance based on current time
function updateCityscape() {
    const now = new Date();
    const hour = now.getHours();
    
    // Get all the relevant elements
    const celestialBody = document.getElementById('celestial-body');
    const cityScapeSky = document.querySelector('.cityscape-sky');
    const stars = document.querySelectorAll('.star');
    const windows = document.querySelectorAll('.window');
    
    // Times of day
    const isMorning = hour >= 5 && hour < 10;
    const isDay = hour >= 10 && hour < 17;
    const isEvening = hour >= 17 && hour < 21;
    const isNight = hour >= 21 || hour < 5;
    
    // Clear existing sky classes
    cityScapeSky.classList.remove('morning-sky', 'day-sky', 'evening-sky', 'night-sky');
    
    // Clear celestial body classes
    celestialBody.classList.remove('sun', 'moon');
    
    // Set position of celestial body based on time (0-24 hour)
    let celestialPosition = (hour / 24) * 100;
    // Adjust for night time (sun below horizon)
    if (isNight) {
        // For night, we want moon to be visible and positioned appropriately
        // Start at 60% left at 21:00, reach 20% left by 5:00
        if (hour >= 21) {
            celestialPosition = 60 - ((hour - 21) / 8) * 40;
        } else {
            celestialPosition = 20 - ((hour) / 5) * 20;
        }
        
        // Position the moon vertically based on time
        // Highest at midnight, lower towards dusk and dawn
        let moonHeight;
        if (hour >= 21) {
            moonHeight = 20 + ((hour - 21) / 3) * 15; // Rising from 20% to 35%
        } else if (hour < 3) {
            moonHeight = 35; // Highest at 35% from top
        } else {
            moonHeight = 35 - ((hour - 3) / 2) * 15; // Lowering from 35% to 20%
        }
        
        celestialBody.style.left = `${celestialPosition}%`;
        celestialBody.style.top = `${moonHeight}%`;
        celestialBody.classList.add('moon');
    } else {
        // For day, position sun in an arc from left to right
        // Sunrise at 5:00 (10% left, 50% top), noon at 12:00 (50% left, 10% top), sunset at 20:00 (90% left, 50% top)
        let sunLeft, sunTop;
        
        if (hour >= 5 && hour <= 12) {
            // Morning to noon (move from left edge upward to center)
            const progress = (hour - 5) / 7;
            sunLeft = 10 + (progress * 40);
            sunTop = 50 - (progress * 40);
        } else {
            // Noon to evening (move from center downward to right edge)
            const progress = (hour - 12) / 8;
            sunLeft = 50 + (progress * 40);
            sunTop = 10 + (progress * 40);
        }
        
        celestialBody.style.left = `${sunLeft}%`;
        celestialBody.style.top = `${sunTop}%`;
        celestialBody.classList.add('sun');
    }
    
    // Set sky appearance based on time
    if (isMorning) {
        cityScapeSky.classList.add('morning-sky');
    } else if (isDay) {
        cityScapeSky.classList.add('day-sky');
    } else if (isEvening) {
        cityScapeSky.classList.add('evening-sky');
    } else {
        cityScapeSky.classList.add('night-sky');
    }
    
    // Toggle stars visibility based on time
    stars.forEach(star => {
        if (isNight || isEvening) {
            star.style.opacity = ''; // Use CSS animation
        } else {
            star.style.opacity = '0'; // Hide stars during day
        }
    });
    
    // Update windows to reflect time of day
    updateBuildingWindows(isNight, isEvening);
}

// Create the building windows
function createBuildingWindows() {
    const buildings = document.querySelectorAll('.building');
    const windowsContainer = document.createElement('div');
    windowsContainer.id = 'windows-container';
    document.querySelector('.cityscape-buildings').appendChild(windowsContainer);
    
    buildings.forEach((building, index) => {
        const buildingHeight = parseInt(window.getComputedStyle(building).height);
        const buildingWidth = parseInt(window.getComputedStyle(building).width);
        const buildingLeft = building.offsetLeft;
        
        // Create 3-6 windows per building depending on size
        const numWindows = Math.floor(Math.random() * 4) + 3;
        
        for (let i = 0; i < numWindows; i++) {
            const window = document.createElement('div');
            window.classList.add('window');
            
            // Random positions for windows, but ensure they're within the building
            const windowLeft = buildingLeft + Math.floor(Math.random() * (buildingWidth - 15)) + 5;
            const windowTop = Math.floor(Math.random() * (buildingHeight - 40)) + 20;
            
            window.style.left = `${windowLeft}px`;
            window.style.top = `${windowTop}px`;
            
            windowsContainer.appendChild(window);
        }
    });
}

// Update windows to be lit during night/evening
function updateBuildingWindows(isNight, isEvening) {
    const windows = document.querySelectorAll('.window');
    
    windows.forEach(window => {
        // Windows are lit at night, with some randomization
        if (isNight || isEvening) {
            // Make most windows lit up in evening/night, with some randomization
            // - Probability of window being lit is 80%
            if (Math.random() < 0.8) {
                window.classList.add('window-lit');
                
                // Set window color based on time
                if (isNight) {
                    window.style.backgroundColor = 'var(--window-night)';
                } else if (isEvening) {
                    window.style.backgroundColor = 'var(--window-evening)';
                }
            } else {
                window.classList.remove('window-lit');
                window.style.backgroundColor = 'rgba(255, 255, 255, 0.2)';
            }
        } else {
            // During day, windows are less visible
            window.classList.remove('window-lit');
            window.style.backgroundColor = 'rgba(255, 255, 255, 0.2)';
        }
    });
}

// Create stars for the night sky
function createStars() {
    const starsContainer = document.getElementById('stars-container');
    const numberOfStars = 50;
    
    for (let i = 0; i < numberOfStars; i++) {
        const star = document.createElement('div');
        star.classList.add('star');
        
        // Random positions for stars
        star.style.left = `${Math.floor(Math.random() * 100)}%`;
        star.style.top = `${Math.floor(Math.random() * 80)}%`;
        
        // Add random animation delay for twinkling effect
        star.style.animationDelay = `${Math.random() * 4}s`;
        
        starsContainer.appendChild(star);
    }
}

