/**
 * AI Recommendations Feature
 * Handles the AI recommendation form submission and display
 */
document.addEventListener('DOMContentLoaded', function() {
  // Get references to AI recommendation elements
  const aiRecommendationForm = document.getElementById('aiRecommendationForm');
  const recommendationResults = document.getElementById('recommendationResults');
  const recommendationList = document.getElementById('recommendationList');
  const recommendationReasoning = document.getElementById('recommendationReasoning');
  const getRecommendationsBtn = document.getElementById('getRecommendationsBtn');
  const recommendationError = document.getElementById('recommendationError');
  const loadingIndicator = document.getElementById('recommendationsLoading');
  
  // Track request for cancellation
  let abortController = null;
  
  if (aiRecommendationForm) {
    aiRecommendationForm.addEventListener('submit', function(e) {
      e.preventDefault();
      
      // Hide any previous error
      if (recommendationError) {
        recommendationError.classList.add('d-none');
      }
      
      // Hide previous results
      if (recommendationResults) {
        recommendationResults.style.display = 'none';
      }
      
      // Create abort controller for this request
      abortController = new AbortController();
      
      // Show loading state
      getRecommendationsBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Generating...';
      getRecommendationsBtn.disabled = true;
      
      // Show loading indicator
      if (loadingIndicator) {
        loadingIndicator.classList.remove('d-none');
      }
      
      // Set up cancel button functionality
      const cancelButton = document.getElementById('cancelRecommendationsBtn');
      if (cancelButton) {
        cancelButton.onclick = function() {
          if (abortController) {
            abortController.abort();
            abortController = null;
            
            // Reset UI
            getRecommendationsBtn.innerHTML = '<i class="fas fa-magic me-1"></i> Get Recommendations';
            getRecommendationsBtn.disabled = false;
            loadingIndicator.classList.add('d-none');
            
            // Show cancelled message
            if (recommendationError) {
              recommendationError.textContent = 'Request cancelled. You can try again with different preferences.';
              recommendationError.classList.remove('d-none');
              setTimeout(() => {
                recommendationError.classList.add('d-none');
              }, 5000);
            }
          }
        };
      }
      
      // Get URL for the request - use the form's action or fallback to hard-coded URL
      let url = aiRecommendationForm.getAttribute('action');
      if (!url) {
        url = '/ai_recommendation';
        console.warn('Form is missing action attribute, using fallback URL');
      }
      
      // Collect form data
      const formData = new FormData(aiRecommendationForm);
      
      // Make AJAX request
      fetch(url, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData,
        signal: abortController.signal
      })
      .then(response => {
        if (!response.ok) {
          throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
        }
        return response.json();
      })
      .then(data => {
        // Reset controller
        abortController = null;
        
        // Reset UI
        getRecommendationsBtn.innerHTML = '<i class="fas fa-magic me-1"></i> Get Recommendations';
        getRecommendationsBtn.disabled = false;
        
        // Hide loading indicator
        if (loadingIndicator) {
          loadingIndicator.classList.add('d-none');
        }
        
        if (data.status === 'success' && data.recommendations && data.recommendations.length > 0) {
          // Clear previous results
          recommendationList.innerHTML = '';
          
          // Add each recommendation to the list
          data.recommendations.forEach(recommendation => {
            const item = document.createElement('div');
            item.className = 'list-group-item bg-dark text-light border-secondary mb-3';
            
            let districtBadge = '';
            if (recommendation.district) {
              districtBadge = `<span class="badge bg-secondary ms-2">${recommendation.district}</span>`;
            }
            
            let ratingStars = '';
            if (recommendation.rating) {
              ratingStars = `<div class="mb-1"><i class="fas fa-star text-warning"></i> <strong>${recommendation.rating}</strong></div>`;
            }
            
            item.innerHTML = `
              <div class="d-flex justify-content-between align-items-start">
                <div>
                  <h5 class="mb-1">${recommendation.business_name}</h5>
                  <p class="mb-1">
                    <i class="fas fa-tag me-1 text-primary"></i>
                    ${recommendation.deal}
                  </p>
                  <p class="mb-1">
                    <i class="fas fa-map-marker-alt me-1 text-danger"></i>
                    ${recommendation.location} ${districtBadge}
                  </p>
                  ${ratingStars}
                  <div class="mt-2 mb-0 text-info fst-italic">
                    <i class="fas fa-info-circle me-1"></i>
                    ${recommendation.explanation || "Perfect match for your preferences!"}
                  </div>
                </div>
                <div>
                  <a href="/deal/${encodeURIComponent(recommendation.business_name)}" class="btn btn-primary btn-sm">
                    <i class="fas fa-eye me-1"></i> View
                  </a>
                </div>
              </div>
            `;
            
            recommendationList.appendChild(item);
          });
          
          // Add reasoning
          recommendationReasoning.textContent = data.reasoning || "Based on your preferences, these venues offer the best match for your criteria.";
          
          // Show results
          recommendationResults.style.display = 'block';
        } else {
          // Show error
          if (recommendationError) {
            recommendationError.textContent = data.reasoning || "No recommendations found. Try different preferences.";
            recommendationError.classList.remove('d-none');
          } else {
            alert('Error generating recommendations: ' + (data.reasoning || 'No matching venues found.'));
          }
        }
      })
      .catch(error => {
        // Reset controller
        abortController = null;
        
        // Reset UI
        getRecommendationsBtn.innerHTML = '<i class="fas fa-magic me-1"></i> Get Recommendations';
        getRecommendationsBtn.disabled = false;
        
        // Hide loading indicator
        if (loadingIndicator) {
          loadingIndicator.classList.add('d-none');
        }
        
        // Don't show abort errors (user cancelled)
        if (error.name === 'AbortError') {
          console.log('Request was cancelled by user');
          return;
        }
        
        console.error('Error generating recommendations:', error);
        
        if (recommendationError) {
          recommendationError.textContent = 'Error generating recommendations. Please try again.';
          recommendationError.classList.remove('d-none');
        } else {
          alert('Error generating recommendations. Please try again.');
        }
      });
    });
  }
});