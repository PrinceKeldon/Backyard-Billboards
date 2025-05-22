/**
 * Happy Hour Hub - Personalized Color Palette Generator
 * Allows users to customize the app's color scheme to their preferences
 */

// Default color palette
const defaultPalette = {
  primary: '#FF595E',    // Bright Red
  secondary: '#FFCF3F',  // Golden Yellow
  accent: '#FFCF3F',     // Gold
  light: '#FFF5E1',      // Cream
  dark: '#252525'        // Dark gray
};

// Predefined color palettes
const palettes = {
  default: { ...defaultPalette },
  sunset: {
    primary: '#FF5E5B',
    secondary: '#FFCA3A', 
    accent: '#8AC926',
    light: '#FFF8DC',
    dark: '#252525'
  },
  ocean: {
    primary: '#3D5A80',
    secondary: '#98C1D9',
    accent: '#EE6C4D',
    light: '#E0FBFC',
    dark: '#293241'
  },
  forest: {
    primary: '#588157',
    secondary: '#A3B18A',
    accent: '#DAD7CD',
    light: '#FEFAE0',
    dark: '#3A5A40'
  },
  neon: {
    primary: '#FF00FF',
    secondary: '#00FFFF',
    accent: '#FFFF00',
    light: '#F5F5F5',
    dark: '#1A1A1A'
  }
};

// Current palette (defaults to user's saved choice or default)
let currentPalette = 'default';

/**
 * Initialize the color palette
 */
function initColorPalette() {
  // Load saved palette from localStorage
  const savedPalette = localStorage.getItem('colorPalette');
  if (savedPalette && palettes[savedPalette]) {
    currentPalette = savedPalette;
  }
  
  // Apply the current palette
  applyColorPalette(currentPalette);
  
  // Set up event listeners once DOM is loaded
  document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM loaded, initializing color palette customizer");
    
    // Initialize the Bootstrap modal
    const colorModal = document.getElementById('colorPaletteModal');
    if (colorModal) {
      console.log("Color palette modal found in DOM");
      // Create a Bootstrap modal instance to ensure proper functionality
      const modalInstance = new bootstrap.Modal(colorModal);
      
      // Get the modal trigger button
      const modalTrigger = document.querySelector('a[data-bs-target="#colorPaletteModal"]');
      if (modalTrigger) {
        console.log("Modal trigger button found");
        modalTrigger.addEventListener('click', (e) => {
          e.preventDefault();
          console.log("Modal trigger clicked, showing modal");
          modalInstance.show();
        });
      }
    } else {
      console.error("Color palette modal not found in DOM");
    }
    
    const paletteSelector = document.getElementById('palette-selector');
    if (paletteSelector) {
      console.log("Palette selector found, populating options");
      // Populate selector with options
      for (const palette in palettes) {
        const option = document.createElement('option');
        option.value = palette;
        option.textContent = palette.charAt(0).toUpperCase() + palette.slice(1);
        if (palette === currentPalette) {
          option.selected = true;
        }
        paletteSelector.appendChild(option);
      }
      
      // Add event listener for changes
      paletteSelector.addEventListener('change', (e) => {
        console.log("Palette changed to:", e.target.value);
        applyColorPalette(e.target.value);
      });
    } else {
      console.error("Palette selector not found in DOM");
    }
    
    // Set up the color customizer
    setupColorCustomizer();
  });
}

/**
 * Apply a color palette
 * @param {string} paletteName - The name of the palette to apply
 */
function applyColorPalette(paletteName) {
  if (!palettes[paletteName]) {
    console.error(`Palette "${paletteName}" not found`);
    return;
  }
  
  // Update current palette
  currentPalette = paletteName;
  localStorage.setItem('colorPalette', paletteName);
  
  // Apply colors to CSS variables
  const palette = palettes[paletteName];
  document.documentElement.style.setProperty('--bb-primary', palette.primary);
  document.documentElement.style.setProperty('--bb-secondary', palette.secondary);
  document.documentElement.style.setProperty('--bb-accent', palette.accent);
  document.documentElement.style.setProperty('--bb-light', palette.light);
  document.documentElement.style.setProperty('--bb-dark', palette.dark);
  
  // Update RGB values for Bootstrap
  updateRgbValues(palette.primary, '--bs-primary-rgb');
  updateRgbValues(palette.secondary, '--bs-secondary-rgb');
  updateRgbValues(palette.accent, '--bs-warning-rgb');
  
  // Update preview swatches
  updateColorSwatches();
}

/**
 * Convert hex color to RGB values and update CSS variable
 * @param {string} hex - Hex color code
 * @param {string} cssVar - CSS variable name to update
 */
function updateRgbValues(hex, cssVar) {
  // Remove # if present
  hex = hex.replace('#', '');
  
  // Convert hex to RGB
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  
  // Update CSS variable
  document.documentElement.style.setProperty(cssVar, `${r}, ${g}, ${b}`);
}

/**
 * Update color swatches in the customizer
 */
function updateColorSwatches() {
  const swatches = document.querySelectorAll('.color-swatch');
  const palette = palettes[currentPalette];
  
  swatches.forEach(swatch => {
    const colorKey = swatch.dataset.color;
    if (palette[colorKey]) {
      swatch.style.backgroundColor = palette[colorKey];
      const input = swatch.querySelector('input[type="color"]');
      if (input) {
        input.value = palette[colorKey];
      }
    }
  });
}

/**
 * Set up the color customizer panel
 */
function setupColorCustomizer() {
  const customizer = document.getElementById('color-customizer');
  if (!customizer) return;
  
  // Set up color pickers
  const colorInputs = customizer.querySelectorAll('input[type="color"]');
  colorInputs.forEach(input => {
    // Set initial value
    const colorKey = input.dataset.color;
    const palette = palettes[currentPalette];
    if (colorKey && palette[colorKey]) {
      input.value = palette[colorKey];
    }
    
    // Add change event listener
    input.addEventListener('change', (e) => {
      const colorKey = e.target.dataset.color;
      if (colorKey) {
        // Create custom palette if it doesn't exist
        if (!palettes.custom) {
          palettes.custom = { ...palettes[currentPalette] };
        }
        
        // Update custom palette
        palettes.custom[colorKey] = e.target.value;
        
        // Apply custom palette
        applyColorPalette('custom');
        
        // Update selector
        const selector = document.getElementById('palette-selector');
        if (selector) {
          selector.value = 'custom';
          
          // Add custom option if it doesn't exist
          if (!selector.querySelector('option[value="custom"]')) {
            const option = document.createElement('option');
            option.value = 'custom';
            option.textContent = 'Custom';
            selector.appendChild(option);
          }
        }
      }
    });
  });
  
  // Set up save button
  const saveButton = document.getElementById('save-palette');
  if (saveButton) {
    saveButton.addEventListener('click', () => {
      const name = prompt('Enter a name for your custom palette:');
      if (name && name.trim()) {
        // Save current custom palette with new name
        const safeName = name.trim().toLowerCase().replace(/\s+/g, '-');
        palettes[safeName] = { ...palettes.custom };
        
        // Update selector
        const selector = document.getElementById('palette-selector');
        if (selector) {
          const option = document.createElement('option');
          option.value = safeName;
          option.textContent = name.trim();
          option.selected = true;
          selector.appendChild(option);
          
          // Update current palette
          currentPalette = safeName;
          localStorage.setItem('colorPalette', safeName);
          
          // Save to localStorage
          savePalettesToStorage();
        }
      }
    });
  }
  
  // Set up reset button
  const resetButton = document.getElementById('reset-palette');
  if (resetButton) {
    resetButton.addEventListener('click', () => {
      applyColorPalette('default');
      
      // Update selector
      const selector = document.getElementById('palette-selector');
      if (selector) {
        selector.value = 'default';
      }
    });
  }
}

/**
 * Save custom palettes to localStorage
 */
function savePalettesToStorage() {
  const customPalettes = {};
  
  // Extract custom palettes
  for (const key in palettes) {
    if (key !== 'default' && key !== 'sunset' && key !== 'ocean' && 
        key !== 'forest' && key !== 'neon') {
      customPalettes[key] = palettes[key];
    }
  }
  
  // Save to localStorage
  if (Object.keys(customPalettes).length > 0) {
    localStorage.setItem('customPalettes', JSON.stringify(customPalettes));
  }
}

/**
 * Load custom palettes from localStorage
 */
function loadPalettesFromStorage() {
  const savedPalettes = localStorage.getItem('customPalettes');
  if (savedPalettes) {
    try {
      const customPalettes = JSON.parse(savedPalettes);
      // Add custom palettes to available palettes
      for (const key in customPalettes) {
        palettes[key] = customPalettes[key];
      }
    } catch (e) {
      console.error('Error loading custom palettes:', e);
    }
  }
}

// Load custom palettes on script load
loadPalettesFromStorage();

/**
 * Close the color palette modal
 */
function closeColorPaletteModal() {
  const modal = document.getElementById('colorPaletteModal');
  if (modal) {
    modal.classList.remove('show');
    modal.style.display = 'none';
    modal.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('modal-open');
    
    // Remove backdrop
    const backdrop = document.getElementById('color-palette-backdrop');
    if (backdrop) {
      backdrop.remove();
    }
  }
}

// Wait for DOM to be fully loaded before initializing
document.addEventListener('DOMContentLoaded', () => {
  console.log("DOM fully loaded, starting color palette initialization");
  
  // Initialize the color palette system
  initColorPalette();
  
  // Force Bootstrap modal to be properly initialized
  const colorModal = document.getElementById('colorPaletteModal');
  if (colorModal) {
    // Manually create modal instance with Bootstrap
    try {
      window.colorPaletteModalInstance = new bootstrap.Modal(colorModal);
      console.log("Modal instance created successfully");
    } catch (error) {
      console.error("Error creating modal instance:", error);
    }
    
    // Add manual event listener to color palette button
    const colorButton = document.getElementById('openColorPaletteBtn');
    if (colorButton) {
      console.log("Color button found, adding click handler");
      colorButton.addEventListener('click', function(e) {
        e.preventDefault();
        console.log("Color button clicked");
        
        // Use pure JavaScript to show the modal
        const modal = document.getElementById('colorPaletteModal');
        if (modal) {
          console.log("Showing modal with direct DOM manipulation");
          modal.classList.add('show');
          modal.style.display = 'block';
          modal.setAttribute('aria-hidden', 'false');
          document.body.classList.add('modal-open');
          
          // Add backdrop
          const backdrop = document.createElement('div');
          backdrop.className = 'modal-backdrop fade show';
          backdrop.id = 'color-palette-backdrop';
          document.body.appendChild(backdrop);
          
          // Set up close button functionality
          const closeButtons = modal.querySelectorAll('[data-bs-dismiss="modal"], .btn-close');
          closeButtons.forEach(button => {
            button.addEventListener('click', function() {
              closeColorPaletteModal();
            });
          });
          
          // Also close on backdrop click
          backdrop.addEventListener('click', function() {
            closeColorPaletteModal();
          });
        } else {
          console.error("Modal element not found");
        }
      });
    } else {
      console.error("Color button not found");
    }
  } else {
    console.error("Color palette modal element not found in DOM");
  }
});