// Main JavaScript file for Student PDF Hub

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // File size validation
    setupFileValidation();
    
    // Auto-dismiss alerts
    setupAutoDismissAlerts();
    
    // Enhanced form validation
    setupFormValidation();
    
    // Smooth scrolling for anchor links
    setupSmoothScrolling();
});

function setupFileValidation() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;
            
            // Check file size (50MB limit)
            const maxSize = 50 * 1024 * 1024; // 50MB
            if (file.size > maxSize) {
                alert('File size exceeds 50MB limit. Please choose a smaller file.');
                e.target.value = '';
                return;
            }
            
            // Check file type
            const allowedTypes = ['application/pdf', 'application/epub+zip'];
            const allowedExtensions = ['.pdf', '.epub'];
            
            const isValidType = allowedTypes.includes(file.type) || 
                              allowedExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
            
            if (!isValidType) {
                alert('Invalid file type. Only PDF and EPUB files are allowed.');
                e.target.value = '';
                return;
            }
            
            // Display file info
            displayFileInfo(file, input);
        });
    });
}

function displayFileInfo(file, input) {
    // Create or update file info display
    let infoDiv = input.parentNode.querySelector('.file-info');
    if (!infoDiv) {
        infoDiv = document.createElement('div');
        infoDiv.className = 'file-info mt-2';
        input.parentNode.appendChild(infoDiv);
    }
    
    const fileSize = (file.size / 1024 / 1024).toFixed(2);
    infoDiv.innerHTML = `
        <div class="alert alert-info alert-sm">
            <i class="fas fa-file me-2"></i>
            <strong>${file.name}</strong> (${fileSize} MB)
        </div>
    `;
}

function setupAutoDismissAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    
    alerts.forEach(alert => {
        // Auto-dismiss success alerts after 5 seconds
        if (alert.classList.contains('alert-success')) {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        }
    });
}

function setupFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // Prevent double submission
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn.disabled) {
                e.preventDefault();
                return;
            }
            
            // Basic validation
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.classList.add('is-invalid');
                    isValid = false;
                } else {
                    field.classList.remove('is-invalid');
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                return;
            }
            
            // Show loading state
            showLoadingState(submitBtn);
        });
    });
}

function showLoadingState(button) {
    if (!button) return;
    
    const originalHTML = button.innerHTML;
    button.disabled = true;
    
    // Store original text for restoration
    button.dataset.originalHtml = originalHTML;
    
    // Set loading text based on button text
    let loadingText = 'Processing...';
    if (originalHTML.includes('Upload')) {
        loadingText = '<i class="fas fa-spinner fa-spin me-2"></i>Uploading...';
    } else if (originalHTML.includes('Convert')) {
        loadingText = '<i class="fas fa-spinner fa-spin me-2"></i>Converting...';
    } else if (originalHTML.includes('Save')) {
        loadingText = '<i class="fas fa-spinner fa-spin me-2"></i>Saving...';
    } else {
        loadingText = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
    }
    
    button.innerHTML = loadingText;
}

function setupSmoothScrolling() {
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href === '#') return;
            
            const target = document.querySelector(href);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function showToast(message, type = 'info') {
    // Create toast element
    const toastHTML = `
        <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    // Add to toast container (create if doesn't exist)
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    toastContainer.innerHTML = toastHTML;
    const toastElement = toastContainer.querySelector('.toast');
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
}

// URL validation helper
function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}

// Copy to clipboard helper
function copyToClipboard(text) {
    return navigator.clipboard.writeText(text).then(function() {
        return true;
    }).catch(function() {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        const success = document.execCommand('copy');
        document.body.removeChild(textArea);
        return success;
    });
}

// Debounce function for search inputs
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;
        
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        
        if (callNow) func.apply(context, args);
    };
}

// Progress indicator for long operations
function showProgress(element, progress) {
    if (!element.querySelector('.progress')) {
        const progressHTML = `
            <div class="progress mt-2" style="height: 3px;">
                <div class="progress-bar" role="progressbar" style="width: 0%"></div>
            </div>
        `;
        element.insertAdjacentHTML('beforeend', progressHTML);
    }
    
    const progressBar = element.querySelector('.progress-bar');
    progressBar.style.width = progress + '%';
    
    if (progress >= 100) {
        setTimeout(() => {
            const progressElement = element.querySelector('.progress');
            if (progressElement) {
                progressElement.remove();
            }
        }, 1000);
    }
}

// Export utility functions for use in other scripts
window.StudentPDFHub = {
    formatFileSize,
    showToast,
    isValidUrl,
    copyToClipboard,
    debounce,
    showProgress
};
