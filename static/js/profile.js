document.addEventListener('DOMContentLoaded', function() {
    const personalInfoForm = document.getElementById('personalInfoForm');
    const preferencesForm = document.getElementById('preferencesForm');
    const passwordForm = document.getElementById('passwordForm');
    const exportDataBtn = document.getElementById('exportData');
    const deleteAccountBtn = document.getElementById('deleteAccount');
    const alertContainer = document.getElementById('alertContainer');

    function showAlert(message, type = 'error') {
        alertContainer.innerHTML = `
            <div class="alert alert-${type}">
                ${message}
            </div>
        `;
        setTimeout(() => {
            alertContainer.innerHTML = '';
        }, 5000);
    }

    // Load user profile data
    async function loadProfileData() {
        try {
            const response = await fetch('/api/profile');
            const data = await response.json();
            
            if (response.ok) {
                // Populate personal information form
                document.getElementById('firstName').value = data.user.first_name || '';
                document.getElementById('lastName').value = data.user.last_name || '';
                document.getElementById('email').value = data.user.email || '';
                document.getElementById('phone').value = data.user.phone || '';
                
                // Populate preferences
                document.getElementById('journalReminders').value = data.preferences.journal_reminders || 'daily';
                document.getElementById('theme').value = data.preferences.theme || 'light';
                document.getElementById('privacyLevel').value = data.preferences.privacy_level || 'private';
                document.getElementById('aiInsights').checked = data.preferences.ai_insights !== false;
                document.getElementById('emailNotifications').checked = data.preferences.email_notifications !== false;
            } else {
                showAlert('Error loading profile data');
            }
        } catch (error) {
            showAlert('Network error loading profile data');
            console.error('Profile error:', error);
        }
    }

    // Update personal information
    personalInfoForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(personalInfoForm);
        const data = Object.fromEntries(formData);
        
        try {
            const response = await fetch('/api/profile/update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                showAlert('Personal information updated successfully', 'success');
            } else {
                showAlert(result.error || 'Error updating information');
            }
        } catch (error) {
            showAlert('Network error updating information');
            console.error('Update error:', error);
        }
    });

    // Update preferences
    preferencesForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(preferencesForm);
        const data = Object.fromEntries(formData);
        
        // Convert checkboxes to boolean
        data.ai_insights = document.getElementById('aiInsights').checked;
        data.email_notifications = document.getElementById('emailNotifications').checked;
        
        try {
            const response = await fetch('/api/profile/preferences', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                showAlert('Preferences updated successfully', 'success');
            } else {
                showAlert(result.error || 'Error updating preferences');
            }
        } catch (error) {
            showAlert('Network error updating preferences');
            console.error('Preferences error:', error);
        }
    });

    // Change password
    passwordForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const newPassword = document.getElementById('newPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        
        if (newPassword !== confirmPassword) {
            showAlert('New passwords do not match');
            return;
        }
        
        if (newPassword.length < 6) {
            showAlert('Password must be at least 6 characters long');
            return;
        }
        
        const formData = new FormData(passwordForm);
        const data = Object.fromEntries(formData);
        
        try {
            const response = await fetch('/api/profile/password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                showAlert('Password changed successfully', 'success');
                passwordForm.reset();
            } else {
                showAlert(result.error || 'Error changing password');
            }
        } catch (error) {
            showAlert('Network error changing password');
            console.error('Password error:', error);
        }
    });

    // Export data
    exportDataBtn.addEventListener('click', async function() {
        try {
            const response = await fetch('/api/profile/export');
            const blob = await response.blob();
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'soupie-data-export.json';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            showAlert('Data exported successfully', 'success');
        } catch (error) {
            showAlert('Error exporting data');
            console.error('Export error:', error);
        }
    });

    // Delete account
    deleteAccountBtn.addEventListener('click', function() {
        if (confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
            if (confirm('This will permanently delete all your data. Are you absolutely sure?')) {
                deleteAccount();
            }
        }
    });

    async function deleteAccount() {
        try {
            const response = await fetch('/api/profile/delete', {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (response.ok) {
                showAlert('Account deleted successfully. Redirecting to login...', 'success');
                setTimeout(() => {
                    window.location.href = '/login';
                }, 2000);
            } else {
                showAlert(result.error || 'Error deleting account');
            }
        } catch (error) {
            showAlert('Network error deleting account');
            console.error('Delete error:', error);
        }
    }

    // Load profile data on page load
    loadProfileData();
});
