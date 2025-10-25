document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const loginText = document.getElementById('loginText');
    const loginLoading = document.getElementById('loginLoading');
    const alertContainer = document.getElementById('alertContainer');

    function showAlert(message, type = 'error') {
        alertContainer.innerHTML = `
            <div class="alert alert-${type}">
                ${message}
            </div>
        `;
    }

    function setLoading(loading) {
        if (loading) {
            loginText.classList.add('hidden');
            loginLoading.classList.remove('hidden');
            loginForm.querySelector('button').disabled = true;
        } else {
            loginText.classList.remove('hidden');
            loginLoading.classList.add('hidden');
            loginForm.querySelector('button').disabled = false;
        }
    }

    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        
        if (!email || !password) {
            showAlert('Please fill in all fields');
            return;
        }
        
        setLoading(true);
        alertContainer.innerHTML = '';
        
        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    password: password
                })
            });
            
            const data = await response.json();
            console.log('Login response data:', data);
            
            if (response.ok) {
                showAlert('Login successful! Redirecting...', 'success');
                console.log('Login successful, onboarding_done:', data.onboarding_done);
                
                // Set flag to trigger mood popup on dashboard
                sessionStorage.setItem('justLoggedIn', 'true');
                
                // Redirect based on onboarding status
                console.log('About to redirect, onboarding_done:', data.onboarding_done);
                setTimeout(() => {
                    if (data.onboarding_done) {
                        console.log('Redirecting to dashboard...');
                        window.location.href = '/dashboard';
                    } else {
                        console.log('Redirecting to onboarding...');
                        window.location.href = '/onboarding';
                    }
                }, 500);
            } else {
                showAlert(data.error || 'Login failed');
            }
        } catch (error) {
            showAlert('Network error. Please try again.');
            console.error('Login error:', error);
        } finally {
            setLoading(false);
        }
    });
});
