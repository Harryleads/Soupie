// Authentication utilities
async function checkAuth() {
    console.log('Checking authentication via server...');
    
    try {
        // Make a request to a protected endpoint to verify authentication
        const response = await fetch('/api/dashboard', {
            method: 'GET',
            credentials: 'include' // Include cookies in the request
        });
        
        if (response.ok) {
            console.log('Auth check passed - user is authenticated');
            return true;
        } else {
            console.log('Auth check failed - user not authenticated');
            return false;
        }
    } catch (error) {
        console.log('Auth check error:', error);
        return false;
    }
}

function clearAuth() {
    localStorage.removeItem('token');
    localStorage.removeItem('user_id');
}

function logout() {
    // Clear local storage
    clearAuth();
    
    // Call logout API to clear server-side session
    fetch('/api/logout', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(() => {
        // Redirect to login page
        window.location.href = '/login';
    }).catch(error => {
        console.error('Logout error:', error);
        // Still redirect even if API call fails
        window.location.href = '/login';
    });
}

async function requireAuth() {
    const isAuthenticated = await checkAuth();
    if (!isAuthenticated) {
        window.location.href = '/login';
        return false;
    }
    return true;
}

// Auto-check authentication on page load
document.addEventListener('DOMContentLoaded', async function() {
    // Only check auth on protected pages (not login/register)
    const currentPath = window.location.pathname;
    const publicPages = ['/login', '/register', '/'];
    
    if (!publicPages.includes(currentPath)) {
        // Add a small delay to allow login redirects to complete
        setTimeout(async () => {
            const isAuthenticated = await checkAuth();
            if (!isAuthenticated) {
                console.log('Auth check failed, redirecting to login');
                window.location.href = '/login';
            }
        }, 100);
    }
});
