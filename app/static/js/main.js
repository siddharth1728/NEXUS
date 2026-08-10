// Get CSRF Token from meta tag
function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

// Intercept fetch to automatically attach CSRF token if present
const originalFetch = window.fetch;
window.fetch = async function() {
    let [resource, config] = arguments;
    if (!config) {
        config = {};
    }
    
    // For modifying requests, inject CSRF token
    const method = config.method ? config.method.toUpperCase() : 'GET';
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
        if (!config.headers) {
            config.headers = {};
        }
        config.headers['X-CSRF-Token'] = getCsrfToken();
    }
    
    return originalFetch(resource, config);
};

// Global Logout Handler
const logoutBtn = document.getElementById('logout-btn');
if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
        try {
            const response = await fetch('/api/auth/logout', { method: 'POST' });
            if (response.ok) {
                window.location.href = '/login';
            } else {
                alert("Failed to logout.");
            }
        } catch (err) {
            console.error(err);
        }
    });
}
