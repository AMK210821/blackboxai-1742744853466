// Main JavaScript for VREC Library Management System

// API Helper Class
class API {
    constructor(baseUrl = '/api') {
        this.baseUrl = baseUrl;
    }

    // Generic request method
    async request(endpoint, options = {}) {
        const token = localStorage.getItem('token');
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': token ? `Bearer ${token}` : ''
            }
        };

        try {
            showLoading();
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                ...defaultOptions,
                ...options,
                headers: {
                    ...defaultOptions.headers,
                    ...(options.headers || {})
                }
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'API request failed');
            }

            return data;
        } catch (error) {
            showToast(error.message, 'error');
            throw error;
        } finally {
            hideLoading();
        }
    }

    // HTTP method wrappers
    get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
}

// Authentication Helper Class
class Auth {
    constructor() {
        this.token = localStorage.getItem('token');
        this.user = null;
    }

    async init() {
        if (this.token) {
            try {
                const response = await api.get('/auth/profile');
                this.user = response.user;
                return true;
            } catch (error) {
                this.logout();
                return false;
            }
        }
        return false;
    }

    isAuthenticated() {
        return !!this.token;
    }

    async login(credentials) {
        try {
            const response = await api.post('/auth/login', credentials);
            this.token = response.token;
            this.user = response.user;
            localStorage.setItem('token', this.token);
            localStorage.setItem('userId', this.user.id);
            return true;
        } catch (error) {
            throw error;
        }
    }

    logout() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('token');
        localStorage.removeItem('userId');
        window.location.href = '/login';
    }

    getUser() {
        return this.user;
    }
}

// UI Helper Class
class UI {
    static showToast(message, type = 'error') {
        const toast = document.createElement('div');
        toast.className = `toast ${type === 'error' ? 'bg-red-500' : 'bg-green-500'} text-white px-6 py-3 rounded-lg shadow-lg mb-3`;
        toast.textContent = message;

        const container = document.getElementById('toastContainer');
        container.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    static showLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.remove('hidden');
        }
    }

    static hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.add('hidden');
        }
    }

    static formatDate(date) {
        return new Date(date).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    static formatCurrency(amount) {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR'
        }).format(amount);
    }
}

// Barcode Scanner Helper Class
class BarcodeScanner {
    constructor(containerId) {
        this.containerId = containerId;
        this.quaggaInstance = null;
    }

    init() {
        return new Promise((resolve, reject) => {
            Quagga.init({
                inputStream: {
                    name: "Live",
                    type: "LiveStream",
                    target: document.querySelector(`#${this.containerId}`),
                    constraints: {
                        facingMode: "environment"
                    },
                },
                decoder: {
                    readers: ["ean_reader", "ean_8_reader", "code_128_reader", "code_39_reader"]
                }
            }, (err) => {
                if (err) {
                    reject(err);
                    return;
                }
                this.quaggaInstance = Quagga;
                resolve();
            });
        });
    }

    start(onDetected) {
        Quagga.start();
        Quagga.onDetected((result) => {
            onDetected(result.codeResult.code);
        });
    }

    stop() {
        if (this.quaggaInstance) {
            this.quaggaInstance.stop();
        }
    }
}

// QR Code Payment Helper Class
class QRPayment {
    constructor(containerId) {
        this.containerId = containerId;
    }

    generateQR(data) {
        const container = document.getElementById(this.containerId);
        container.innerHTML = '';
        
        return QRCode.toCanvas(container, data, {
            width: 256,
            margin: 1,
            color: {
                dark: '#000000',
                light: '#ffffff'
            }
        });
    }

    generateUPILink(paymentData) {
        const {
            payeeName = 'VREC Library',
            payeeVPA = 'library@upi',
            amount,
            transactionNote
        } = paymentData;

        return `upi://pay?pa=${payeeVPA}&pn=${encodeURIComponent(payeeName)}&am=${amount}&cu=INR&tn=${encodeURIComponent(transactionNote)}`;
    }
}

// Form Validation Helper Class
class FormValidator {
    static validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    static validatePassword(password) {
        return password.length >= 6;
    }

    static validateRequired(value) {
        return value.trim().length > 0;
    }

    static validateForm(formData, rules) {
        const errors = {};

        for (const [field, validations] of Object.entries(rules)) {
            for (const validation of validations) {
                switch (validation) {
                    case 'required':
                        if (!this.validateRequired(formData[field])) {
                            errors[field] = `${field} is required`;
                        }
                        break;
                    case 'email':
                        if (!this.validateEmail(formData[field])) {
                            errors[field] = 'Invalid email format';
                        }
                        break;
                    case 'password':
                        if (!this.validatePassword(formData[field])) {
                            errors[field] = 'Password must be at least 6 characters';
                        }
                        break;
                }
            }
        }

        return {
            isValid: Object.keys(errors).length === 0,
            errors
        };
    }
}

// Initialize global instances
const api = new API();
const auth = new Auth();
const showToast = UI.showToast;
const showLoading = UI.showLoading;
const hideLoading = UI.hideLoading;

// Document ready handler
document.addEventListener('DOMContentLoaded', async () => {
    // Initialize authentication
    const isAuthenticated = await auth.init();
    
    // Handle authentication based redirects
    const publicPages = ['/login', '/register'];
    const currentPath = window.location.pathname;
    
    if (!isAuthenticated && !publicPages.includes(currentPath)) {
        window.location.href = '/login';
    } else if (isAuthenticated && publicPages.includes(currentPath)) {
        window.location.href = `/${auth.getUser().role}-dashboard`;
    }

    // Setup logout handler
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => auth.logout());
    }

    // Setup mobile menu handler
    const menuBtn = document.getElementById('mobileMenuBtn');
    const sidebar = document.getElementById('sidebar');
    if (menuBtn && sidebar) {
        menuBtn.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });
    }
});

// Export global utilities
window.api = api;
window.auth = auth;
window.UI = UI;
window.FormValidator = FormValidator;
window.showToast = showToast;
window.showLoading = showLoading;
window.hideLoading = hideLoading;