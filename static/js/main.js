// ProTrack Main JavaScript File - Enhanced Version
// Optimized for smooth login/register experience

document.addEventListener('DOMContentLoaded', function() {
    console.log('ProTrack Main.js loaded');
    
    // ========================================
    // BOOTSTRAP COMPONENTS INITIALIZATION
    // ========================================
    
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize Bootstrap popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // ========================================
    // ALERT AUTO-HIDE
    // ========================================
    
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert:not(.alert-danger)');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // ========================================
    // LOGIN FORM ENHANCEMENTS
    // ========================================
    
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        // Real-time validation for login
        const usernameInput = loginForm.querySelector('input[name="username"]');
        const passwordInput = loginForm.querySelector('input[name="password"]');
        
        if (usernameInput) {
            usernameInput.addEventListener('input', function() {
                validateField(this, this.value.trim().length >= 3, 'Username must be at least 3 characters');
            });
            
            // Remove whitespace on blur
            usernameInput.addEventListener('blur', function() {
                this.value = this.value.trim();
            });
        }
        
        if (passwordInput) {
            passwordInput.addEventListener('input', function() {
                validateField(this, this.value.length >= 1, 'Password is required');
            });
        }
        
        // Form submission with loading state
        loginForm.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            
            // Check if form is valid
            if (usernameInput && passwordInput) {
                if (usernameInput.value.trim().length < 3 || passwordInput.value.length < 1) {
                    e.preventDefault();
                    showToast('Please fill in all required fields correctly', 'danger');
                    return;
                }
            }
            
            // Show loading state
            if (submitBtn) {
                const originalHTML = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Logging in...';
                submitBtn.disabled = true;
                
                // Store original text for error recovery
                submitBtn.dataset.originalText = originalHTML;
            }
        });
    }

    // ========================================
    // REGISTER FORM ENHANCEMENTS
    // ========================================
    
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        // Get all form fields
        const firstNameInput = registerForm.querySelector('input[name="first_name"]');
        const lastNameInput = registerForm.querySelector('input[name="last_name"]');
        const usernameInput = registerForm.querySelector('input[name="username"]');
        const emailInput = registerForm.querySelector('input[name="email"]');
        const phoneInput = registerForm.querySelector('input[name="phone_number"]');
        const password1Input = registerForm.querySelector('input[name="password1"]');
        const password2Input = registerForm.querySelector('input[name="password2"]');
        
        // Real-time validation for first name
        if (firstNameInput) {
            firstNameInput.addEventListener('input', function() {
                const value = this.value.trim();
                validateField(this, value.length >= 2 && /^[a-zA-Z\s]+$/.test(value), 
                    'First name must be at least 2 characters and contain only letters');
            });
        }
        
        // Real-time validation for last name
        if (lastNameInput) {
            lastNameInput.addEventListener('input', function() {
                const value = this.value.trim();
                validateField(this, value.length >= 2 && /^[a-zA-Z\s]+$/.test(value), 
                    'Last name must be at least 2 characters and contain only letters');
            });
        }
        
        // Real-time validation for username
        if (usernameInput) {
            usernameInput.addEventListener('input', function() {
                const value = this.value.trim();
                validateField(this, value.length >= 3 && /^[a-zA-Z0-9_]+$/.test(value), 
                    'Username must be at least 3 characters (letters, numbers, underscore only)');
            });
            
            usernameInput.addEventListener('blur', function() {
                this.value = this.value.trim().toLowerCase();
            });
        }
        
        // Real-time validation for email
        if (emailInput) {
            emailInput.addEventListener('input', function() {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                validateField(this, emailRegex.test(this.value.trim()), 
                    'Please enter a valid email address');
            });
            
            emailInput.addEventListener('blur', function() {
                this.value = this.value.trim().toLowerCase();
            });
        }
        
        // Real-time validation for phone number
        if (phoneInput) {
            phoneInput.addEventListener('input', function() {
                const phoneRegex = /^[\d\s\-\(\)\+]+$/;
                const digitsOnly = this.value.replace(/\D/g, '');
                validateField(this, phoneRegex.test(this.value) && digitsOnly.length >= 10, 
                    'Phone number must be at least 10 digits');
            });
        }
        
        // Password strength indicator
        if (password1Input) {
            // Create password strength indicator
            const strengthIndicator = document.createElement('div');
            strengthIndicator.className = 'password-strength mt-2';
            strengthIndicator.innerHTML = `
                <div class="progress" style="height: 5px;">
                    <div class="progress-bar" role="progressbar" style="width: 0%"></div>
                </div>
                <small class="text-muted strength-text"></small>
            `;
            password1Input.closest('.mb-3').appendChild(strengthIndicator);
            
            const progressBar = strengthIndicator.querySelector('.progress-bar');
            const strengthText = strengthIndicator.querySelector('.strength-text');
            
            password1Input.addEventListener('input', function() {
                const password = this.value;
                const strength = calculatePasswordStrength(password);
                
                // Update progress bar
                progressBar.style.width = strength.percentage + '%';
                progressBar.className = 'progress-bar ' + strength.colorClass;
                strengthText.textContent = strength.text;
                strengthText.className = 'text-muted strength-text ' + strength.textClass;
                
                // Validate password
                validateField(this, password.length >= 8, 
                    'Password must be at least 8 characters');
            });
        }
        
        // Password confirmation matching
        if (password2Input && password1Input) {
            password2Input.addEventListener('input', function() {
                const match = this.value === password1Input.value;
                validateField(this, match && this.value.length > 0, 
                    'Passwords must match');
            });
            
            // Also check when first password changes
            password1Input.addEventListener('input', function() {
                if (password2Input.value.length > 0) {
                    const match = password2Input.value === this.value;
                    validateField(password2Input, match, 'Passwords must match');
                }
            });
        }
        
        // Form submission with validation
        registerForm.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            let isValid = true;
            
            // Validate all required fields
            const requiredFields = [
                { field: usernameInput, minLength: 3, name: 'Username' },
                { field: emailInput, minLength: 5, name: 'Email' },
                { field: password1Input, minLength: 8, name: 'Password' },
                { field: password2Input, minLength: 8, name: 'Confirm Password' }
            ];
            
            requiredFields.forEach(item => {
                if (item.field && item.field.value.trim().length < item.minLength) {
                    isValid = false;
                    item.field.classList.add('is-invalid');
                }
            });
            
            // Check password match
            if (password1Input && password2Input && password1Input.value !== password2Input.value) {
                isValid = false;
                showToast('Passwords do not match', 'danger');
                e.preventDefault();
                return;
            }
            
            if (!isValid) {
                e.preventDefault();
                showToast('Please fill in all required fields correctly', 'danger');
                return;
            }
            
            // Show loading state
            if (submitBtn) {
                const originalHTML = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Creating Account...';
                submitBtn.disabled = true;
                submitBtn.dataset.originalText = originalHTML;
            }
        });
    }

    // ========================================
    // SMOOTH SCROLLING
    // ========================================
    
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });

    // ========================================
    // DASHBOARD ANIMATIONS
    // ========================================
    
    if (window.location.pathname.includes('dashboard')) {
        // Animate numbers
        setTimeout(() => {
            const numbers = document.querySelectorAll('.animate-number');
            numbers.forEach(number => {
                const target = parseInt(number.textContent);
                const increment = target / 30;
                let current = 0;
                
                const timer = setInterval(() => {
                    current += increment;
                    if (current >= target) {
                        number.textContent = target;
                        clearInterval(timer);
                    } else {
                        number.textContent = Math.ceil(current);
                    }
                }, 40);
            });
        }, 300);
    }
});

// ========================================
// UTILITY FUNCTIONS
// ========================================

/**
 * Validate a form field and show/hide feedback
 */
function validateField(field, isValid, errorMessage) {
    const feedbackDiv = field.parentElement.querySelector('.invalid-feedback') || 
                       field.parentElement.parentElement.querySelector('.invalid-feedback');
    
    if (isValid) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
        if (feedbackDiv) {
            feedbackDiv.style.display = 'none';
        }
    } else {
        field.classList.remove('is-valid');
        field.classList.add('is-invalid');
        
        // Create or update feedback message
        if (!feedbackDiv) {
            const newFeedback = document.createElement('div');
            newFeedback.className = 'invalid-feedback';
            newFeedback.style.display = 'block';
            newFeedback.textContent = errorMessage;
            
            if (field.parentElement.classList.contains('input-group')) {
                field.parentElement.parentElement.appendChild(newFeedback);
            } else {
                field.parentElement.appendChild(newFeedback);
            }
        } else {
            feedbackDiv.textContent = errorMessage;
            feedbackDiv.style.display = 'block';
        }
    }
}

/**
 * Calculate password strength
 */
function calculatePasswordStrength(password) {
    let strength = 0;
    
    if (password.length >= 8) strength += 25;
    if (password.length >= 12) strength += 15;
    if (/[a-z]/.test(password)) strength += 15;
    if (/[A-Z]/.test(password)) strength += 15;
    if (/[0-9]/.test(password)) strength += 15;
    if (/[^a-zA-Z0-9]/.test(password)) strength += 15;
    
    let result = {
        percentage: strength,
        text: '',
        colorClass: '',
        textClass: ''
    };
    
    if (strength < 40) {
        result.text = 'Weak password';
        result.colorClass = 'bg-danger';
        result.textClass = 'text-danger';
    } else if (strength < 70) {
        result.text = 'Medium strength';
        result.colorClass = 'bg-warning';
        result.textClass = 'text-warning';
    } else {
        result.text = 'Strong password';
        result.colorClass = 'bg-success';
        result.textClass = 'text-success';
    }
    
    return result;
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    let toastContainer = document.getElementById('toast-container');
    
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, { delay: 4000 });
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

/**
 * Debounce function for performance
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Make utilities globally available
window.ProTrack = {
    showToast: showToast,
    validateField: validateField,
    calculatePasswordStrength: calculatePasswordStrength,
    debounce: debounce
};
