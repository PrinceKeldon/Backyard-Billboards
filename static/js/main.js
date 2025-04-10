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
    
    // Window style types to choose from
    const windowTypes = [
        'window-small', 'window-standard', 'window-large',
        'window-wide', 'window-square', 'window-rounded',
        'window-arched', 'window-circular'
    ];
    
    buildings.forEach((building, buildingIndex) => {
        const buildingHeight = parseInt(window.getComputedStyle(building).height);
        const buildingWidth = parseInt(window.getComputedStyle(building).width);
        const buildingLeft = building.offsetLeft;
        
        // For TV Tower building (styled as Fernsehturm)
        if (building.classList.contains('building-4')) {
            // Add special windows for the TV Tower sphere
            const sphereCenter = buildingLeft + (buildingWidth / 2);
            const sphereTop = 35; // Relative to the top of the building
            
            // Add 8-10 small circular windows in the sphere
            const numTowerWindows = Math.floor(Math.random() * 3) + 8;
            for (let i = 0; i < numTowerWindows; i++) {
                const windowElement = document.createElement('div');
                windowElement.classList.add('window', 'window-tv-tower');
                
                // Position windows in a circle around the sphere
                const angle = (i / numTowerWindows) * Math.PI * 2;
                const radius = 8;
                const windowLeft = sphereCenter + Math.cos(angle) * radius;
                const windowTop = sphereTop + Math.sin(angle) * radius;
                
                windowElement.style.left = `${windowLeft}px`;
                windowElement.style.top = `${windowTop}px`;
                
                windowsContainer.appendChild(windowElement);
            }
        }
        
        // Determine pattern type for this building
        const patternType = Math.floor(Math.random() * 3);
        
        // Choose a window style for this building
        // Buildings in groups of 3 will share window styles for visual consistency
        const windowTypeIndex = Math.floor(buildingIndex / 3) % windowTypes.length;
        const windowType = windowTypes[windowTypeIndex];
        
        // Calculate number of windows based on building size
        // Larger buildings get more windows
        const baseWindowCount = 5;
        const sizeMultiplier = buildingHeight * buildingWidth / 5000;
        const numWindows = Math.floor(baseWindowCount + sizeMultiplier * 10);
        
        // Create the windows
        if (patternType === 0) {
            // Grid pattern
            createGridWindows(building, windowType, numWindows, windowsContainer);
        } else if (patternType === 1) {
            // Random pattern
            createRandomWindows(building, windowType, numWindows, windowsContainer);
        } else {
            // Row pattern
            createRowWindows(building, windowType, numWindows, windowsContainer);
        }
    });
    
    // Add special feature: Rooftop lights on some buildings
    buildings.forEach((building) => {
        // 30% chance for a building to have a rooftop light
        if (Math.random() < 0.3) {
            const buildingWidth = parseInt(window.getComputedStyle(building).width);
            const buildingLeft = building.offsetLeft;
            
            const roofLight = document.createElement('div');
            roofLight.classList.add('window', 'window-small');
            
            // Position at the top of the building
            roofLight.style.left = `${buildingLeft + (buildingWidth / 2) - 2}px`;
            roofLight.style.top = `${parseInt(window.getComputedStyle(building).top) - 5}px`;
            roofLight.style.backgroundColor = 'rgba(255, 0, 0, 0.6)';
            
            windowsContainer.appendChild(roofLight);
        }
    });
}

// Create windows in a grid pattern
function createGridWindows(building, windowType, numWindows, container) {
    const buildingHeight = parseInt(window.getComputedStyle(building).height);
    const buildingWidth = parseInt(window.getComputedStyle(building).width);
    const buildingLeft = building.offsetLeft;
    const buildingTop = parseInt(window.getComputedStyle(building).top) || 0;
    
    // Calculate rows and columns based on building dimensions
    const cols = Math.max(2, Math.floor(buildingWidth / 15));
    const rows = Math.max(2, Math.ceil(numWindows / cols));
    
    // Calculate spacing
    const hSpacing = buildingWidth / (cols + 1);
    const vSpacing = buildingHeight / (rows + 1);
    
    // Create windows in a grid
    for (let row = 1; row <= rows; row++) {
        for (let col = 1; col <= cols; col++) {
            // Skip some windows randomly for variety
            if (Math.random() < 0.2) continue;
            
            const windowElement = document.createElement('div');
            windowElement.classList.add('window', windowType);
            
            // Calculate position
            const windowLeft = buildingLeft + (col * hSpacing);
            const windowTop = buildingTop + (row * vSpacing);
            
            windowElement.style.left = `${windowLeft}px`;
            windowElement.style.top = `${windowTop}px`;
            
            container.appendChild(windowElement);
        }
    }
}

// Create windows in random positions
function createRandomWindows(building, windowType, numWindows, container) {
    const buildingHeight = parseInt(window.getComputedStyle(building).height);
    const buildingWidth = parseInt(window.getComputedStyle(building).width);
    const buildingLeft = building.offsetLeft;
    const buildingTop = parseInt(window.getComputedStyle(building).top) || 0;
    
    // Get window dimensions to ensure they fit within building
    const windowWidth = windowType === 'window-wide' ? 14 : (windowType === 'window-large' ? 10 : 8);
    const windowHeight = windowType === 'window-wide' ? 10 : (windowType === 'window-large' ? 16 : 12);
    
    // Create windows in random positions
    for (let i = 0; i < numWindows; i++) {
        const windowElement = document.createElement('div');
        windowElement.classList.add('window', windowType);
        
        // Calculate safe area within building
        const maxLeft = buildingWidth - windowWidth - 4;
        const maxTop = buildingHeight - windowHeight - 4;
        
        // Calculate random position within safe area
        const windowLeft = buildingLeft + Math.floor(Math.random() * maxLeft) + 4;
        const windowTop = buildingTop + Math.floor(Math.random() * maxTop) + 4;
        
        windowElement.style.left = `${windowLeft}px`;
        windowElement.style.top = `${windowTop}px`;
        
        container.appendChild(windowElement);
    }
}

// Create windows in rows
function createRowWindows(building, windowType, numWindows, container) {
    const buildingHeight = parseInt(window.getComputedStyle(building).height);
    const buildingWidth = parseInt(window.getComputedStyle(building).width);
    const buildingLeft = building.offsetLeft;
    const buildingTop = parseInt(window.getComputedStyle(building).top) || 0;
    
    // Calculate rows and windows per row
    const rows = Math.min(6, Math.max(3, Math.floor(buildingHeight / 20)));
    const windowsPerRow = Math.ceil(numWindows / rows);
    
    // Get window dimensions
    const windowWidth = windowType === 'window-wide' ? 14 : (windowType === 'window-large' ? 10 : 8);
    
    // Calculate spacing
    const hSpacing = (buildingWidth - (windowsPerRow * windowWidth)) / (windowsPerRow + 1);
    const vSpacing = buildingHeight / (rows + 1);
    
    // Create windows in rows
    for (let row = 1; row <= rows; row++) {
        // Randomly skip some rows
        if (Math.random() < 0.1) continue;
        
        for (let i = 0; i < windowsPerRow; i++) {
            // Skip some windows randomly for variety
            if (Math.random() < 0.15) continue;
            
            const windowElement = document.createElement('div');
            windowElement.classList.add('window', windowType);
            
            // Calculate position
            const windowLeft = buildingLeft + (i * windowWidth) + ((i + 1) * hSpacing);
            const windowTop = buildingTop + (row * vSpacing);
            
            windowElement.style.left = `${windowLeft}px`;
            windowElement.style.top = `${windowTop}px`;
            
            container.appendChild(windowElement);
        }
    }
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
                    // Add glow effect for night
                    window.style.boxShadow = '0 0 5px var(--window-night)';
                } else if (isEvening) {
                    window.style.backgroundColor = 'var(--window-evening)';
                    // Add subtle glow effect for evening
                    window.style.boxShadow = '0 0 3px var(--window-evening)';
                }
            } else {
                window.classList.remove('window-lit');
                window.style.backgroundColor = 'rgba(255, 255, 255, 0.2)';
                window.style.boxShadow = 'none';
            }
        } else {
            // During day, windows are less visible
            window.classList.remove('window-lit');
            window.style.backgroundColor = 'rgba(255, 255, 255, 0.2)';
            window.style.boxShadow = 'none';
        }
        
        // Special case for TV tower - always lit
        if (window.classList.contains('window-tv-tower')) {
            window.style.backgroundColor = isNight ? 'rgba(255, 220, 120, 0.8)' : 'rgba(255, 255, 255, 0.8)';
            window.style.boxShadow = isNight ? '0 0 4px rgba(255, 220, 120, 0.8)' : 'none';
        }
        
        // Rooftop lights always on at night - safety lights for aircraft
        if (window.style.backgroundColor === 'rgba(255, 0, 0, 0.6)') {
            if (isNight) {
                window.style.boxShadow = '0 0 8px red';
                // Make it blink
                window.style.animation = 'twinkle 2s infinite';
            } else {
                window.style.boxShadow = 'none';
                window.style.animation = 'none';
            }
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

