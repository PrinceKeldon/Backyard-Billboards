/**
 * Happy Hour Hub - Color Palette Customizer v2
 * This improved version fixes the palette selection and color saving issues
 */

// Default color palette
const DEFAULT_PALETTE = {
  primary: '#FF595E',    // Bright Red
  secondary: '#FFCF3F',  // Golden Yellow
  accent: '#FFCF3F',     // Gold
  light: '#FFF5E1',      // Cream
  dark: '#252525'        // Dark gray
};

// Predefined color palettes
const PREDEFINED_PALETTES = {
  default: { ...DEFAULT_PALETTE },
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

// Current state
let state = {
  currentPalette: 'default',
  customPalettes: {},
  colors: { ...DEFAULT_PALETTE }
};

/**
 * Initialize the color palette system
 */
function initColorPaletteSystem() {
  console.log('Initializing color palette system v2');
  
  // Load saved data from localStorage
  loadSavedData();
  
  // Apply the current palette on load
  applyColorPalette(state.currentPalette);
  
  // Register event listeners for color customizer UI
  document.addEventListener('DOMContentLoaded', setupUIEventListeners);
}

/**
 * Load saved palette data from localStorage
 */
function loadSavedData() {
  try {
    // Load current palette selection
    const savedPalette = localStorage.getItem('hhh_current_palette');
    if (savedPalette) {
      state.currentPalette = savedPalette;
    }
    
    // Load custom palettes
    const savedCustomPalettes = localStorage.getItem('hhh_custom_palettes');
    if (savedCustomPalettes) {
      state.customPalettes = JSON.parse(savedCustomPalettes);
    }
    
    // Set current colors based on selected palette
    if (state.currentPalette === 'custom') {
      state.colors = { ...state.customPalettes.custom };
    } else if (PREDEFINED_PALETTES[state.currentPalette]) {
      state.colors = { ...PREDEFINED_PALETTES[state.currentPalette] };
    } else if (state.customPalettes[state.currentPalette]) {
      state.colors = { ...state.customPalettes[state.currentPalette] };
    } else {
      state.colors = { ...DEFAULT_PALETTE };
    }
    
    console.log('Loaded saved palette data:', state.currentPalette);
  } catch (error) {
    console.error('Error loading saved palette data:', error);
    resetToDefault();
  }
}

/**
 * Set up all UI event listeners for the color customizer
 */
function setupUIEventListeners() {
  // Get UI elements
  const colorPickerBtn = document.getElementById('openColorPaletteBtn');
  const paletteSelector = document.getElementById('palette-selector');
  const colorInputs = document.querySelectorAll('.color-swatch input[type="color"]');
  const saveBtn = document.getElementById('save-palette');
  const resetBtn = document.getElementById('reset-palette');
  const closeBtn = document.querySelector('#colorPaletteModal .btn-close');
  const dismissBtns = document.querySelectorAll('[data-bs-dismiss="modal"]');

  // Set up palette selector
  if (paletteSelector) {
    // Clear existing options
    paletteSelector.innerHTML = '';
    
    // Add predefined palette options
    for (const key in PREDEFINED_PALETTES) {
      const option = document.createElement('option');
      option.value = key;
      option.textContent = key.charAt(0).toUpperCase() + key.slice(1);
      paletteSelector.appendChild(option);
    }
    
    // Add custom palette options
    for (const key in state.customPalettes) {
      if (key !== 'custom') { // 'custom' is a special temporary palette
        const option = document.createElement('option');
        option.value = key;
        option.textContent = key.charAt(0).toUpperCase() + key.slice(1) + ' (Custom)';
        paletteSelector.appendChild(option);
      }
    }
    
    // Set selected option
    paletteSelector.value = state.currentPalette;
    
    // Add change event listener
    paletteSelector.addEventListener('change', (e) => {
      const selectedPalette = e.target.value;
      applyColorPalette(selectedPalette);
    });
  }
  
  // Set up color picker button
  if (colorPickerBtn) {
    colorPickerBtn.addEventListener('click', showColorPickerModal);
  }
  
  // Set up color inputs
  colorInputs.forEach(input => {
    // Set initial value
    const colorKey = input.dataset.color;
    if (colorKey && state.colors[colorKey]) {
      input.value = state.colors[colorKey];
    }
    
    // Add change event listener
    input.addEventListener('input', (e) => {
      const colorKey = e.target.dataset.color;
      if (colorKey) {
        // Update current color
        state.colors[colorKey] = e.target.value;
        
        // Apply color immediately for live preview
        document.documentElement.style.setProperty(`--bb-${colorKey}`, state.colors[colorKey]);
        
        // Update RGB values for Bootstrap
        updateRgbValue(state.colors[colorKey], `--bs-${colorKey === 'accent' ? 'warning' : colorKey}-rgb`);
        
        // Set to custom palette
        state.currentPalette = 'custom';
        if (paletteSelector) {
          // Add custom option if it doesn't exist
          if (!paletteSelector.querySelector('option[value="custom"]')) {
            const option = document.createElement('option');
            option.value = 'custom';
            option.textContent = 'Custom';
            paletteSelector.appendChild(option);
          }
          paletteSelector.value = 'custom';
        }
        
        // Save to custom palette
        state.customPalettes.custom = { ...state.colors };
        savePaletteData();
        
        // Update preview
        updatePreview();
      }
    });
  });
  
  // Set up save button
  if (saveBtn) {
    saveBtn.addEventListener('click', () => {
      const name = prompt('Enter a name for your custom palette:', '');
      if (name && name.trim()) {
        saveCustomPalette(name.trim());
      }
    });
  }
  
  // Set up reset button
  if (resetBtn) {
    resetBtn.addEventListener('click', resetToDefault);
  }
  
  // Set up close button and dismiss buttons
  if (closeBtn) {
    closeBtn.addEventListener('click', hideColorPickerModal);
  }
  
  dismissBtns.forEach(btn => {
    btn.addEventListener('click', hideColorPickerModal);
  });
  
  // Update color input values on modal open
  document.addEventListener('show.bs.modal', function(e) {
    if (e.target.id === 'colorPaletteModal') {
      updateColorInputs();
      updatePreview();
    }
  });
  
  // Update initial preview
  updatePreview();
}

/**
 * Show the color picker modal
 */
function showColorPickerModal() {
  const modal = document.getElementById('colorPaletteModal');
  if (modal) {
    modal.classList.add('show');
    modal.style.display = 'block';
    modal.setAttribute('aria-hidden', 'false');
    document.body.classList.add('modal-open');
    
    // Add backdrop
    if (!document.getElementById('color-palette-backdrop')) {
      const backdrop = document.createElement('div');
      backdrop.id = 'color-palette-backdrop';
      backdrop.className = 'modal-backdrop fade show';
      document.body.appendChild(backdrop);
      
      // Close on backdrop click
      backdrop.addEventListener('click', hideColorPickerModal);
    }
    
    // Update color inputs with current values
    updateColorInputs();
    
    // Update preview
    updatePreview();
  }
}

/**
 * Hide the color picker modal
 */
function hideColorPickerModal() {
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

/**
 * Apply a specific color palette
 * @param {string} paletteName - The name of the palette to apply
 */
function applyColorPalette(paletteName) {
  console.log('Applying palette:', paletteName);
  
  // Determine palette source
  let palette;
  if (paletteName === 'custom' && state.customPalettes.custom) {
    palette = state.customPalettes.custom;
  } else if (PREDEFINED_PALETTES[paletteName]) {
    palette = PREDEFINED_PALETTES[paletteName];
  } else if (state.customPalettes[paletteName]) {
    palette = state.customPalettes[paletteName];
  } else {
    palette = DEFAULT_PALETTE;
    paletteName = 'default';
  }
  
  // Update state
  state.currentPalette = paletteName;
  state.colors = { ...palette };
  
  // Apply colors to CSS variables
  document.documentElement.style.setProperty('--bb-primary', palette.primary);
  document.documentElement.style.setProperty('--bb-secondary', palette.secondary);
  document.documentElement.style.setProperty('--bb-accent', palette.accent);
  document.documentElement.style.setProperty('--bb-light', palette.light);
  document.documentElement.style.setProperty('--bb-dark', palette.dark);
  
  // Update RGB values for Bootstrap
  updateRgbValue(palette.primary, '--bs-primary-rgb');
  updateRgbValue(palette.secondary, '--bs-secondary-rgb');
  updateRgbValue(palette.accent, '--bs-warning-rgb');
  
  // Update color inputs if they exist
  updateColorInputs();
  
  // Update preview
  updatePreview();
  
  // Save current palette selection
  localStorage.setItem('hhh_current_palette', paletteName);
  
  console.log('Applied palette:', paletteName);
}

/**
 * Save the current custom palette with a given name
 * @param {string} name - The name for the custom palette
 */
function saveCustomPalette(name) {
  // Create safe name
  const safeName = name.toLowerCase().replace(/\s+/g, '_');
  
  // Save to custom palettes
  state.customPalettes[safeName] = { ...state.colors };
  state.currentPalette = safeName;
  
  // Save to localStorage
  savePaletteData();
  
  // Update palette selector
  const paletteSelector = document.getElementById('palette-selector');
  if (paletteSelector) {
    // Add option if it doesn't exist
    if (!paletteSelector.querySelector(`option[value="${safeName}"]`)) {
      const option = document.createElement('option');
      option.value = safeName;
      option.textContent = name + ' (Custom)';
      paletteSelector.appendChild(option);
    }
    
    // Select the new option
    paletteSelector.value = safeName;
  }
  
  // Save current palette selection
  localStorage.setItem('hhh_current_palette', safeName);
  
  console.log('Saved custom palette:', name);
  
  // Show confirmation
  alert(`Color palette "${name}" saved successfully!`);
}

/**
 * Reset to default palette
 */
function resetToDefault() {
  state.currentPalette = 'default';
  state.colors = { ...DEFAULT_PALETTE };
  
  // Apply default palette
  applyColorPalette('default');
  
  // Update palette selector
  const paletteSelector = document.getElementById('palette-selector');
  if (paletteSelector) {
    paletteSelector.value = 'default';
  }
  
  console.log('Reset to default palette');
}

/**
 * Save all palette data to localStorage
 */
function savePaletteData() {
  localStorage.setItem('hhh_custom_palettes', JSON.stringify(state.customPalettes));
  localStorage.setItem('hhh_current_palette', state.currentPalette);
}

/**
 * Update the color inputs with the current palette values
 */
function updateColorInputs() {
  const colorInputs = document.querySelectorAll('.color-swatch input[type="color"]');
  colorInputs.forEach(input => {
    const colorKey = input.dataset.color;
    if (colorKey && state.colors[colorKey]) {
      input.value = state.colors[colorKey];
    }
  });
}

/**
 * Update the preview elements with current palette colors
 */
function updatePreview() {
  // Update preview card background
  const previewCard = document.querySelector('.preview-card');
  if (previewCard) {
    previewCard.style.background = `linear-gradient(to right, ${state.colors.primary}, ${state.colors.secondary})`;
  }
}

/**
 * Update a CSS RGB variable from a hex color
 * @param {string} hex - Hex color code
 * @param {string} cssVar - CSS variable name
 */
function updateRgbValue(hex, cssVar) {
  // Remove # if present
  hex = hex.replace('#', '');
  
  // Convert hex to RGB
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  
  // Update CSS variable
  document.documentElement.style.setProperty(cssVar, `${r}, ${g}, ${b}`);
}

// Initialize the color palette system
initColorPaletteSystem();