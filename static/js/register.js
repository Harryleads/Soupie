document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.getElementById('registerForm');
    const registerText = document.getElementById('registerText');
    const registerLoading = document.getElementById('registerLoading');
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
            registerText.classList.add('hidden');
            registerLoading.classList.remove('hidden');
            registerForm.querySelector('button').disabled = true;
        } else {
            registerText.classList.remove('hidden');
            registerLoading.classList.add('hidden');
            registerForm.querySelector('button').disabled = false;
        }
    }

    function validateForm() {
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm_password').value;
        const email = document.getElementById('email').value;
        const phone = document.getElementById('phone').value;
        
        if (!email && !phone) {
            showAlert('Please provide either an email or phone number');
            return false;
        }
        
        if (password.length < 6) {
            showAlert('Password must be at least 6 characters long');
            return false;
        }
        
        if (password !== confirmPassword) {
            showAlert('Passwords do not match');
            return false;
        }
        
        return true;
    }

    registerForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        if (!validateForm()) {
            return;
        }
        
        const formData = {
            first_name: document.getElementById('first_name').value,
            last_name: document.getElementById('last_name').value,
            email: document.getElementById('email').value,
            phone: document.getElementById('phone').value,
            password: document.getElementById('password').value
        };
        
        setLoading(true);
        alertContainer.innerHTML = '';
        
        try {
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showAlert('Account created successfully! Redirecting to onboarding...', 'success');
                
                setTimeout(() => {
                    window.location.href = '/onboarding';
                }, 1500);
            } else {
                showAlert(data.error || 'Registration failed');
            }
        } catch (error) {
            showAlert('Network error. Please try again.');
            console.error('Registration error:', error);
        } finally {
            setLoading(false);
        }
    });
});
