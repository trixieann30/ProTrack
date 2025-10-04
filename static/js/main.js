// // ProTrack Main JavaScript File

// document.addEventListener('DOMContentLoaded', function() {
//     // Initialize tooltips
//     var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
//     var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
//         return new bootstrap.Tooltip(tooltipTriggerEl);
//     });

//     // Initialize popovers
//     var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
//     var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
//         return new bootstrap.Popover(popoverTriggerEl);
//     });

//     // Form validation
//     const forms = document.querySelectorAll('form');
//     forms.forEach(form => {
//         form.addEventListener('submit', function(e) {
//             if (!form.checkValidity()) {
//                 e.preventDefault();
//                 e.stopPropagation();
//             }
//             form.classList.add('was-validated');
//         });
//     });

//     // Auto-hide alerts
//     const alerts = document.querySelectorAll('.alert');
//     alerts.forEach(alert => {
//         if (!alert.classList.contains('alert-danger')) {
//             setTimeout(() => {
//                 const bsAlert = new bootstrap.Alert(alert);
//                 bsAlert.close();
//             }, 5000);
//         }
//     });

//     // Loading states for buttons - FIXED VERSION
//     // Attach to form submit instead of button click
//     const formsWithSubmit = document.querySelectorAll('form');
//     formsWithSubmit.forEach(form => {
//         form.addEventListener('submit', function(e) {
//             // Only show loading if form is valid
//             if (this.checkValidity()) {
//                 const submitButton = this.querySelector('button[type="submit"]');
//                 if (submitButton) {
//                     const originalText = submitButton.innerHTML;
//                     submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Processing...';
//                     submitButton.disabled = true;
                    
//                     // Store original text in case we need to restore it
//                     submitButton.dataset.originalText = originalText;
//                 }
//             }
//         });
//     });

//     // Smooth scrolling for anchor links
//     document.querySelectorAll('a[href^="#"]').forEach(anchor => {
//         anchor.addEventListener('click', function (e) {
//             e.preventDefault();
//             const target = document.querySelector(this.getAttribute('href'));
//             if (target) {
//                 target.scrollIntoView({
//                     behavior: 'smooth',
//                     block: 'start'
//                 });
//             }
//         });
//     });

//     // Search functionality (if search input exists)
//     const searchInput = document.querySelector('#searchInput');
//     if (searchInput) {
//         searchInput.addEventListener('input', function() {
//             const searchTerm = this.value.toLowerCase();
//             const searchableItems = document.querySelectorAll('.searchable-item');
            
//             searchableItems.forEach(item => {
//                 const text = item.textContent.toLowerCase();
//                 if (text.includes(searchTerm)) {
//                     item.style.display = 'block';
//                 } else {
//                     item.style.display = 'none';
//                 }
//             });
//         });
//     }

//     // Stats animation on dashboard
//     const animateNumbers = () => {
//         const numbers = document.querySelectorAll('.animate-number');
//         numbers.forEach(number => {
//             const target = parseInt(number.textContent);
//             const increment = target / 20;
//             let current = 0;
            
//             const timer = setInterval(() => {
//                 current += increment;
//                 if (current >= target) {
//                     number.textContent = target;
//                     clearInterval(timer);
//                 } else {
//                     number.textContent = Math.ceil(current);
//                 }
//             }, 50);
//         });
//     };

//     // Call animate numbers if on dashboard
//     if (window.location.pathname.includes('dashboard')) {
//         setTimeout(animateNumbers, 500);
//     }

//     // Form field character counter
//     const textareas = document.querySelectorAll('textarea[maxlength]');
//     textareas.forEach(textarea => {
//         const maxLength = textarea.getAttribute('maxlength');
//         const counter = document.createElement('div');
//         counter.className = 'character-counter text-muted small text-end mt-1';
//         counter.textContent = `0/${maxLength}`;
//         textarea.parentNode.appendChild(counter);

//         textarea.addEventListener('input', function() {
//             const currentLength = this.value.length;
//             counter.textContent = `${currentLength}/${maxLength}`;
            
//             if (currentLength > maxLength * 0.9) {
//                 counter.classList.add('text-warning');
//             } else {
//                 counter.classList.remove('text-warning');
//             }
//         });
//     });

//     // Copy to clipboard functionality
//     const copyButtons = document.querySelectorAll('.btn-copy');
//     copyButtons.forEach(button => {
//         button.addEventListener('click', function() {
//             const targetId = this.getAttribute('data-target');
//             const targetElement = document.querySelector(targetId);
            
//             if (targetElement) {
//                 navigator.clipboard.writeText(targetElement.textContent).then(() => {
//                     const originalText = this.innerHTML;
//                     this.innerHTML = '<i class="fas fa-check me-1"></i>Copied!';
//                     this.classList.add('btn-success');
                    
//                     setTimeout(() => {
//                         this.innerHTML = originalText;
//                         this.classList.remove('btn-success');
//                     }, 2000);
//                 });
//             }
//         });
//     });

//     // Skills and certifications tag input
//     const tagInputs = document.querySelectorAll('.tag-input');
//     tagInputs.forEach(input => {
//         input.addEventListener('keypress', function(e) {
//             if (e.key === 'Enter' || e.key === ',') {
//                 e.preventDefault();
//                 // Add tag functionality here
//             }
//         });
//     });

//     // Profile picture preview
//     const profilePictureInput = document.querySelector('#id_profile_picture');
//     if (profilePictureInput) {
//         profilePictureInput.addEventListener('change', function() {
//             const file = this.files[0];
//             if (file) {
//                 const reader = new FileReader();
//                 reader.onload = function(e) {
//                     const preview = document.querySelector('#profile-preview');
//                     if (preview) {
//                         preview.src = e.target.result;
//                     }
//                 };
//                 reader.readAsDataURL(file);
//             }
//         });
//     }
// });

// // Utility functions
// const ProTrack = {
//     // Show toast notification
//     showToast: function(message, type = 'info') {
//         const toastContainer = document.querySelector('#toast-container') || this.createToastContainer();
        
//         const toast = document.createElement('div');
//         toast.className = `toast align-items-center text-white bg-${type} border-0`;
//         toast.setAttribute('role', 'alert');
//         toast.innerHTML = `
//             <div class="d-flex">
//                 <div class="toast-body">${message}</div>
//                 <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
//             </div>
//         `;
        
//         toastContainer.appendChild(toast);
//         const bsToast = new bootstrap.Toast(toast);
//         bsToast.show();
        
//         toast.addEventListener('hidden.bs.toast', () => {
//             toast.remove();
//         });
//     },

//     // Create toast container if it doesn't exist
//     createToastContainer: function() {
//         const container = document.createElement('div');
//         container.id = 'toast-container';
//         container.className = 'toast-container position-fixed top-0 end-0 p-3';
//         container.style.zIndex = '1055';
//         document.body.appendChild(container);
//         return container;
//     },

//     // Format date
//     formatDate: function(dateString) {
//         const options = { 
//             year: 'numeric', 
//             month: 'long', 
//             day: 'numeric',
//             hour: '2-digit',
//             minute: '2-digit'
//         };
//         return new Date(dateString).toLocaleDateString('en-US', options);
//     },

//     // Validate email
//     validateEmail: function(email) {
//         const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
//         return re.test(email);
//     },

//     // Validate phone number
//     validatePhone: function(phone) {
//         const re = /^\+?[\d\s\-\(\)]+$/;
//         return re.test(phone) && phone.replace(/\D/g, '').length >= 10;
//     },

//     // Generate random color for avatars
//     getRandomColor: function() {
//         const colors = ['#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8', '#6f42c1'];
//         return colors[Math.floor(Math.random() * colors.length)];
//     },

//     // Debounce function for search
//     debounce: function(func, wait, immediate) {
//         let timeout;
//         return function executedFunction(...args) {
//             const later = () => {
//                 timeout = null;
//                 if (!immediate) func(...args);
//             };
//             const callNow = immediate && !timeout;
//             clearTimeout(timeout);
//             timeout = setTimeout(later, wait);
//             if (ca=llNow) func(...args);
//         };
//     }
// };

// // Make ProTrack utilities globally available
// window.ProTrack = ProTrack;

// ProTrack Main JavaScript File - Simplified Version

document.addEventListener('DOMContentLoaded', function() {
    console.log('Main.js loaded');
    
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

    // Auto-hide success alerts only
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert:not(.alert-danger)');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});