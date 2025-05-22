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
  
  // Set up event listeners for palette selector
  document.addEventListener('DOMContentLoaded', () => {
    const paletteSelector = document.getElementById('palette-selector');
    if (paletteSelector) {
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
        applyColorPalette(e.target.value);
      });
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

// Initialize color palette
initColorPalette();