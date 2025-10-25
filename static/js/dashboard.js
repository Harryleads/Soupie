document.addEventListener('DOMContentLoaded', function() {
    const recentActivity = document.getElementById('recentActivity');
    const alertContainer = document.getElementById('alertContainer');
    const emptyState = document.getElementById('emptyState');
    const recentActivitySection = document.getElementById('recentActivitySection');
    const quickActionsSection = document.getElementById('quickActionsSection');
    
    // Chat interface elements
    const chatContainer = document.getElementById('chatContainer');
    const chatMessages = document.getElementById('chatMessages');
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    const chatSendBtn = document.getElementById('chatSendBtn');
    
    // Feature elements
    const featureBubbles = document.querySelectorAll('.feature-bubble');
    const featureContent = document.getElementById('featureContent');
    const backToChatBtn = document.getElementById('backToChatBtn');
    const featureTitle = document.getElementById('featureTitle');
    const featureBody = document.getElementById('featureBody');
    
    // Chat state
    let chatHistory = [];
    let moodPopupShown = false;

    function showAlert(message, type = 'error') {
        alertContainer.innerHTML = `
            <div class="alert alert-${type}">
                ${message}
            </div>
        `;
    }

    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    function updateCurrentDate() {
        const now = new Date();
        const dateText = now.toLocaleDateString('en-US', {
            weekday: 'long',
            month: 'short',
            day: 'numeric'
        });
        
        const dateElement = document.querySelector('.date-text');
        if (dateElement) {
            dateElement.textContent = `Today, ${dateText}`;
        } else {
            // Try alternative selector
            const altElement = document.querySelector('.current-date .date-text');
            if (altElement) {
                altElement.textContent = `Today, ${dateText}`;
            }
        }
        
        // Update day buttons to show current week and highlight today
        updateDayButtons(now);
    }

    function updateDayButtons(currentDate) {
        const dayButtons = document.querySelectorAll('.day-btn');
        const dayNames = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];
        const today = currentDate.getDay(); // 0 = Sunday, 1 = Monday, etc.
        
        dayButtons.forEach((button, index) => {
            // Update button text
            button.textContent = dayNames[index];
            
            // Remove active class from all buttons
            button.classList.remove('active');
            
            // Add active class to today's button
            if (index === today) {
                button.classList.add('active');
            }
        });
    }

    function updateDashboardStats(stats) {
        // Update streak
        const streakElements = document.querySelectorAll('.summary-card:nth-child(1) .summary-value');
        streakElements.forEach(element => {
            element.textContent = stats.streak || 0;
        });
        
        // Update entries
        const entriesElements = document.querySelectorAll('.summary-card:nth-child(2) .summary-value');
        entriesElements.forEach(element => {
            element.textContent = stats.total_journals || 0;
        });
    }

    function renderRecentActivity(activities) {
        if (activities.length === 0) {
            recentActivity.innerHTML = `
                <p style="text-align: center; color: #636e72; padding: 2rem;">
                    No recent activity. Start writing your first journal entry!
                </p>
            `;
            return;
        }

        const html = activities.map(activity => `
            <div class="journal-entry">
                <div class="journal-content">${activity.content}</div>
                <div class="journal-meta">
                    <span>${formatDate(activity.created_at)}</span>
                </div>
            </div>
        `).join('');
        
        recentActivity.innerHTML = html;
    }

    function updateDashboardVisibility(data) {
        const totalEntries = data.stats.private_journals + data.stats.open_journals;
        
        if (totalEntries === 0) {
            // Show empty state for new users
            emptyState.style.display = 'block';
            recentActivitySection.style.display = 'none';
            quickActionsSection.style.display = 'none';
        } else {
            // Show activity sections for existing users
            emptyState.style.display = 'none';
            recentActivitySection.style.display = 'block';
            quickActionsSection.style.display = 'block';
        }
    }

    async function loadDashboardData() {
        try {
            const response = await fetch('/api/dashboard');
            const data = await response.json();
            
            if (response.ok) {
                // Update dashboard visibility based on user data
                updateDashboardVisibility(data);
                
                // Update recent activity
                renderRecentActivity(data.recent_activity);
                
                // Update today's mood display
                const todayMoodElement = document.getElementById('todayMood');
                if (todayMoodElement && data.stats.today_mood) {
                    todayMoodElement.textContent = data.stats.today_mood;
                }
                
                // Update streak and entries from API data
                updateDashboardStats(data.stats);
                
                // Load profile insights if available
                await loadProfileInsights();
                
            } else {
                showAlert('Error loading dashboard data');
                console.error('Dashboard error:', data);
            }
        } catch (error) {
            showAlert('Network error. Please refresh the page.');
            console.error('Dashboard error:', error);
        }
    }

    async function loadProfileInsights() {
        try {
            const response = await fetch('/api/profile/insights');
            const data = await response.json();
            
            if (response.ok && data.insights) {
                displayInsights(data.insights);
            }
        } catch (error) {
            console.log('No insights available yet');
        }
    }

    function displayInsights(insights) {
        // Create insights section if it doesn't exist
        let insightsSection = document.getElementById('insightsSection');
        if (!insightsSection) {
            insightsSection = document.createElement('div');
            insightsSection.id = 'insightsSection';
            insightsSection.className = 'card';
            insightsSection.innerHTML = `
                <h3 style="color: #2c3e50; margin-bottom: 1.5rem;">Your Mental Health Insights</h3>
                <div id="insightsContent"></div>
            `;
            
            // Insert after dashboard grid
            const dashboardGrid = document.querySelector('.dashboard-grid');
            dashboardGrid.parentNode.insertBefore(insightsSection, dashboardGrid.nextSibling);
        }
        
        const insightsContent = document.getElementById('insightsContent');
        
        // Display mental health index
        const mhi = insights.mental_health_index || 50;
        const cluster = insights.cluster_primary || 'cluster_resilient';
        const summary = insights.summary_text || 'Thank you for sharing your experiences.';
        
        insightsContent.innerHTML = `
            <div class="insights-overview">
                <div class="mhi-display">
                    <h4>Mental Health Index: ${mhi}/100</h4>
                    <div class="mhi-bar">
                        <div class="mhi-fill" style="width: ${mhi}%; background: ${getMhiColor(mhi)};"></div>
                    </div>
                </div>
                
                <div class="cluster-info">
                    <h4>Current Pattern: ${formatClusterName(cluster)}</h4>
                    <p class="summary-text">${summary}</p>
                </div>
                
                ${insights.domain_scores ? `
                <div class="domain-scores">
                    <h4>Wellness Areas</h4>
                    <div class="scores-grid">
                        ${Object.entries(insights.domain_scores).map(([domain, score]) => `
                            <div class="score-item">
                                <span class="score-label">${formatDomainName(domain)}</span>
                                <div class="score-bar">
                                    <div class="score-fill" style="width: ${score}%; background: ${getScoreColor(score)};"></div>
                                </div>
                                <span class="score-value">${Math.round(score)}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
            </div>
        `;
    }

    function getMhiColor(mhi) {
        if (mhi >= 70) return '#4CAF50';
        if (mhi >= 50) return '#FF9800';
        return '#F44336';
    }

    function getScoreColor(score) {
        if (score >= 70) return '#4CAF50';
        if (score >= 50) return '#FF9800';
        return '#F44336';
    }

    function formatClusterName(cluster) {
        const names = {
            'cluster_affective_low': 'Low Energy Pattern',
            'cluster_anxiety': 'Anxiety Pattern',
            'cluster_burnout': 'Burnout Pattern',
            'cluster_stress_overload': 'Stress Overload Pattern',
            'cluster_resilient': 'Resilient Pattern'
        };
        return names[cluster] || 'Wellness Pattern';
    }

    function formatDomainName(domain) {
        const names = {
            'mood_stability': 'Mood Stability',
            'energy_function': 'Energy & Focus',
            'social_engagement': 'Social Connection',
            'cognitive_flexibility': 'Mental Flexibility',
            'protective_strength': 'Support Systems'
        };
        return names[domain] || domain;
    }

    // Chat functionality

    function addMessage(content, isUser = false, suggestedFeatures = []) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${isUser ? 'user' : 'ai'}`;
        
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = `message-bubble ${isUser ? 'user' : 'ai'}`;
        
        if (isUser) {
            bubbleDiv.textContent = content;
        } else {
            // For AI messages, support HTML content and CTAs
            bubbleDiv.innerHTML = content;
            
            // Add CTA buttons if suggested features are provided
            if (suggestedFeatures && suggestedFeatures.length > 0) {
                const ctaContainer = document.createElement('div');
                ctaContainer.className = 'chat-cta-container';
                ctaContainer.style.marginTop = '0.75rem';
                
                suggestedFeatures.forEach(feature => {
                    const ctaButton = document.createElement('button');
                    ctaButton.className = 'chat-cta-button';
                    ctaButton.textContent = getFeatureDisplayName(feature);
                    ctaButton.onclick = () => showFeature(feature);
                    ctaContainer.appendChild(ctaButton);
                });
                
                bubbleDiv.appendChild(ctaContainer);
            }
        }
        
        messageDiv.appendChild(bubbleDiv);
        chatMessages.appendChild(messageDiv);
        
        // Auto-scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Store in chat history
        chatHistory.push({ content, isUser, timestamp: new Date(), suggestedFeatures });
    }

    function getFeatureDisplayName(feature) {
        const names = {
            'private-journal': '📝 Private Journal',
            'open-journal': '🌍 Community Journal',
            'mood-tracker': '😊 Track Mood',
            'weekly-progress': '📊 Weekly Progress',
            'emotional-checkin': '💭 Emotional Check-in',
            'tips-advice': '💡 Tips & Advice',
            'profile-insights': '📈 My Insights'
        };
        return names[feature] || feature;
    }

    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chat-message ai';
        typingDiv.id = 'typingIndicator';
        
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'message-bubble ai';
        bubbleDiv.innerHTML = '<span class="typing-dots">...</span>';
        
        typingDiv.appendChild(bubbleDiv);
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    async function sendMessage() {
        const message = chatInput.value.trim();
        if (!message) return;

        // Add user message
        addMessage(message, true);
        chatInput.value = '';
        chatSendBtn.disabled = true;
        
        // Show typing indicator
        showTypingIndicator();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    message,
                    chat_history: chatHistory
                })
            });

            const data = await response.json();
            
            if (response.ok) {
                // Remove typing indicator
                removeTypingIndicator();
                
                // Add AI response with suggested features
                addMessage(data.response, false, data.suggested_features || []);
            } else {
                removeTypingIndicator();
                addMessage('Sorry, I encountered an error. Please try again.');
                showAlert(data.error || 'Chat error');
            }
        } catch (error) {
            removeTypingIndicator();
            addMessage('Sorry, I\'m having trouble connecting. Please try again.');
            showAlert('Network error. Please check your connection.');
        } finally {
            chatSendBtn.disabled = false;
        }
    }

    // Feature functionality
    function showFeature(featureName) {
        console.log('showFeature called with:', featureName);
        
        const featureTitles = {
            'private-journal': 'Private Journal',
            'open-journal': 'Community Journal',
            'mood-tracker': 'Mood Tracker',
            'weekly-progress': 'Weekly Progress',
            'emotional-checkin': 'Emotional Check-in',
            'tips-advice': 'Tips & Advice',
            'profile-insights': 'Profile & Insights'
        };

        featureTitle.textContent = featureTitles[featureName] || 'Feature';
        
        // Hide chat and bubbles, show feature content
        chatContainer.style.display = 'none';
        document.querySelector('.feature-bubbles').style.display = 'none';
        featureContent.classList.add('active');
        
        // Load feature content
        loadFeatureContent(featureName);
    }

    function loadFeatureContent(featureName) {
        let content = '';
        
        switch(featureName) {
            case 'private-journal':
                content = `
                    <div class="card">
                        <h3>Write in Your Private Journal</h3>
                        <p>Share your thoughts and feelings in a safe, private space.</p>
                        <form id="privateJournalForm">
                            <textarea class="journal-textarea" id="privateJournalContent" placeholder="What's on your mind today?"></textarea>
                            <div style="margin-top: 1rem;">
                                <button type="submit" class="btn btn-primary">Save Entry</button>
                            </div>
                        </form>
                    </div>
                `;
                break;
            case 'open-journal':
                content = `
                    <div class="card">
                        <h3>Share with the Community</h3>
                        <p>Connect with others by sharing your experiences (anonymously).</p>
                        <form id="openJournalForm">
                            <textarea class="journal-textarea" id="openJournalContent" placeholder="Share your thoughts with the community..."></textarea>
                            <div style="margin-top: 1rem;">
                                <select class="form-control" id="emotionTag" style="margin-bottom: 1rem;">
                                    <option value="">Select an emotion</option>
                                    <option value="happy">😊 Happy</option>
                                    <option value="sad">😢 Sad</option>
                                    <option value="anxious">😰 Anxious</option>
                                    <option value="grateful">🙏 Grateful</option>
                                    <option value="confused">😕 Confused</option>
                                    <option value="hopeful">🌟 Hopeful</option>
                                </select>
                                <button type="submit" class="btn btn-primary">Share with Community</button>
                            </div>
                        </form>
                    </div>
                `;
                break;
            case 'mood-tracker':
                // Instead of showing feature content, directly show the mood popup
                console.log('mood-tracker case triggered, showing mood popup');
                showMoodPopup();
                return; // Exit early to prevent feature content from showing
            case 'weekly-progress':
                content = `
                    <div class="card">
                        <h3>Weekly Progress Review</h3>
                        <p>Let's look at your wellness journey this week.</p>
                        <div id="progressContent">
                            <p>Loading your progress data...</p>
                        </div>
                    </div>
                `;
                // Load weekly mood report
                loadWeeklyProgress();
                break;
            case 'emotional-checkin':
                content = `
                    <div class="card">
                        <h3>Emotional Check-in</h3>
                        <p>Take a moment to reflect on your emotional state.</p>
                        <form id="emotionalCheckinForm">
                            <div class="form-group">
                                <label>How would you describe your overall emotional state today?</label>
                                <select class="form-control" id="emotionalState">
                                    <option value="">Select an option</option>
                                    <option value="very-positive">Very positive and optimistic</option>
                                    <option value="positive">Generally positive</option>
                                    <option value="neutral">Neutral or mixed</option>
                                    <option value="negative">Somewhat negative</option>
                                    <option value="very-negative">Very negative or distressed</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>What's contributing most to how you feel right now?</label>
                                <textarea class="form-control" id="emotionalContributors" rows="3" placeholder="Share what's affecting your emotions..."></textarea>
                            </div>
                            <button type="submit" class="btn btn-primary">Complete Check-in</button>
                        </form>
                    </div>
                `;
                break;
            case 'tips-advice':
                content = `
                    <div class="card">
                        <h3>Personalized Tips & Advice</h3>
                        <p>Get personalized wellness tips based on your current state.</p>
                        <div id="tipsContent">
                            <p>Loading personalized tips...</p>
                        </div>
                    </div>
                `;
                break;
            case 'profile-insights':
                content = `
                    <div class="card">
                        <h3>Your Mental Health Insights</h3>
                        <p>View your personalized mental health patterns and progress.</p>
                        <div id="insightsContent">
                            <p>Loading your insights...</p>
                        </div>
                    </div>
                `;
                break;
            default:
                content = '<div class="card"><h3>Feature Coming Soon</h3><p>This feature is under development.</p></div>';
        }
        
        featureBody.innerHTML = content;
        
        // Set up feature-specific event listeners
        setupFeatureListeners(featureName);
    }

    function setupFeatureListeners(featureName) {
        switch(featureName) {
            case 'private-journal':
                const privateForm = document.getElementById('privateJournalForm');
                if (privateForm) {
                    privateForm.addEventListener('submit', async (e) => {
                        e.preventDefault();
                        const content = document.getElementById('privateJournalContent').value;
                        if (!content.trim()) return;
                        
                        try {
                            const response = await fetch('/api/journal/private', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ content })
                            });
                            
                            if (response.ok) {
                                showAlert('Journal entry saved successfully!', 'success');
                                document.getElementById('privateJournalContent').value = '';
                            } else {
                                showAlert('Error saving journal entry');
                            }
                        } catch (error) {
                            showAlert('Network error saving journal entry');
                        }
                    });
                }
                break;
            case 'open-journal':
                const openForm = document.getElementById('openJournalForm');
                if (openForm) {
                    openForm.addEventListener('submit', async (e) => {
                        e.preventDefault();
                        const content = document.getElementById('openJournalContent').value;
                        const emotionTag = document.getElementById('emotionTag').value;
                        if (!content.trim()) return;
                        
                        try {
                            const response = await fetch('/api/journal/open', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ content, emotion_tag: emotionTag })
                            });
                            
                            if (response.ok) {
                                showAlert('Shared with community successfully!', 'success');
                                document.getElementById('openJournalContent').value = '';
                                document.getElementById('emotionTag').value = '';
                            } else {
                                showAlert('Error sharing with community');
                            }
                        } catch (error) {
                            showAlert('Network error sharing with community');
                        }
                    });
                }
                break;
            case 'mood-tracker':
                updateMoodTracker();
                break;
        }
    }

    function hideFeature() {
        featureContent.classList.remove('active');
        chatContainer.style.display = 'block';
        document.querySelector('.feature-bubbles').style.display = 'block';
    }

    // Event listeners
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        sendMessage();
    });
    
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Auto-resize textarea
    chatInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 100) + 'px';
    });
    
    backToChatBtn.addEventListener('click', hideFeature);
    
    // Feature bubble clicks
    featureBubbles.forEach(bubble => {
        bubble.addEventListener('click', () => {
            const feature = bubble.dataset.feature;
            showFeature(feature);
        });
    });

    // Mood popup functionality
    function showMoodPopup() {
        // Remove the moodPopupShown check to allow popup on login
        
        const popup = document.createElement('div');
        popup.className = 'mood-popup-overlay';
        popup.innerHTML = `
            <div class="mood-popup">
                <div class="mood-popup-header">
                    <h3>How are you feeling today?</h3>
                    <button class="mood-popup-close" onclick="this.closest('.mood-popup-overlay').remove()">×</button>
                </div>
                <div class="mood-popup-content">
                    <p>Take a quick moment to check in with yourself.</p>
                    <div class="mood-popup-options horizontal">
                        <button class="mood-popup-btn" data-mood="excellent">😄<br>Excellent</button>
                        <button class="mood-popup-btn" data-mood="good">😊<br>Good</button>
                        <button class="mood-popup-btn" data-mood="okay">😐<br>Okay</button>
                        <button class="mood-popup-btn" data-mood="poor">😔<br>Poor</button>
                        <button class="mood-popup-btn" data-mood="terrible">😢<br>Terrible</button>
                    </div>
                    <div class="mood-popup-notes" style="margin-top: 1rem; display: none;">
                        <textarea class="form-control" id="moodPopupNotes" placeholder="Any additional thoughts? (optional)" rows="2"></textarea>
                    </div>
                    <div class="mood-popup-actions" style="margin-top: 1rem; display: none;">
                        <button class="btn btn-primary" id="saveMoodBtn">Save Mood</button>
                        <button class="btn btn-secondary" onclick="this.closest('.mood-popup-overlay').remove()">Skip</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(popup);
        
        // Add event listeners
        const moodBtns = popup.querySelectorAll('.mood-popup-btn');
        const notesDiv = popup.querySelector('.mood-popup-notes');
        const actionsDiv = popup.querySelector('.mood-popup-actions');
        const saveBtn = popup.querySelector('#saveMoodBtn');
        
        let selectedMood = null;
        
        moodBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                // Remove previous selection
                moodBtns.forEach(b => b.classList.remove('selected'));
                btn.classList.add('selected');
                selectedMood = btn.dataset.mood;
                
                // Show notes and actions
                notesDiv.style.display = 'block';
                actionsDiv.style.display = 'flex';
            });
        });
        
        saveBtn.addEventListener('click', async () => {
            if (!selectedMood) return;
            
            const notes = popup.querySelector('#moodPopupNotes').value;
            
            try {
                const response = await fetch('/api/mood/track', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mood: selectedMood, notes })
                });
                
                if (response.ok) {
                    showAlert('Mood tracked successfully!', 'success');
                    
                    // Update mood card in real-time
                    const todayMoodElement = document.getElementById('todayMood');
                    if (todayMoodElement) {
                        todayMoodElement.textContent = selectedMood.charAt(0).toUpperCase() + selectedMood.slice(1);
                        todayMoodElement.classList.add('mood-updated');
                        // Remove animation class after animation completes
                        setTimeout(() => {
                            todayMoodElement.classList.remove('mood-updated');
                        }, 1000);
                    }
                    
                    popup.remove();
                } else {
                    showAlert('Error tracking mood');
                }
            } catch (error) {
                showAlert('Network error tracking mood');
            }
        });
    }

    // Check if user has tracked mood today
    async function checkTodaysMood() {
        try {
            const response = await fetch('/api/mood/history?days=1');
            const data = await response.json();
            
            if (response.ok && data.mood_records.length === 0) {
                // No mood tracked today, show popup after a short delay
                setTimeout(() => {
                    showMoodPopup();
                }, 2000);
            }
        } catch (error) {
            console.log('Could not check mood history');
        }
    }

    // Update mood tracker to save to database
    function updateMoodTracker() {
        const moodBtns = document.querySelectorAll('.mood-btn');
        moodBtns.forEach(btn => {
            btn.addEventListener('click', async () => {
                const mood = btn.dataset.mood;
                
                try {
                    const response = await fetch('/api/mood/track', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ mood })
                    });
                    
                    if (response.ok) {
                        document.getElementById('moodResult').style.display = 'block';
                        document.getElementById('moodResult').innerHTML = `
                            <strong>Mood recorded:</strong> ${btn.textContent.trim()}<br>
                            <small>Thank you for tracking your mood. This helps us understand your patterns.</small>
                        `;
                    } else {
                        showAlert('Error saving mood');
                    }
                } catch (error) {
                    showAlert('Network error saving mood');
                }
            });
        });
    }

    // Update date display with current date (with small delay to ensure DOM is ready)
    setTimeout(() => {
        updateCurrentDate();
    }, 100);
    
    // Load dashboard data on page load
    loadDashboardData();
    
    // Load weekly progress data
    async function loadWeeklyProgress() {
        try {
            const response = await fetch('/api/mood/weekly-report');
            const data = await response.json();
            
            if (response.ok) {
                const progressContent = document.getElementById('progressContent');
                const summary = data.weekly_summary;
                
                progressContent.innerHTML = `
                    <div class="weekly-summary">
                        <div class="summary-stats">
                            <div class="stat-item">
                                <h4>Total Entries</h4>
                                <p class="stat-number">${summary.total_entries}</p>
                            </div>
                            <div class="stat-item">
                                <h4>Most Common Mood</h4>
                                <p class="stat-text">${summary.most_common_mood}</p>
                            </div>
                            <div class="stat-item">
                                <h4>Average Mood Score</h4>
                                <p class="stat-number">${summary.average_mood_score}/5</p>
                            </div>
                        </div>
                        
                        <div class="mood-distribution">
                            <h4>Mood Distribution This Week</h4>
                            <div class="mood-bars">
                                ${Object.entries(summary.mood_distribution).map(([mood, count]) => `
                                    <div class="mood-bar-item">
                                        <span class="mood-label">${mood}</span>
                                        <div class="mood-bar">
                                            <div class="mood-bar-fill" style="width: ${(count / summary.total_entries) * 100}%"></div>
                                        </div>
                                        <span class="mood-count">${count}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        
                        ${data.recent_records.length > 0 ? `
                        <div class="recent-moods">
                            <h4>Recent Mood Entries</h4>
                            <div class="mood-entries">
                                ${data.recent_records.slice(0, 5).map(record => `
                                    <div class="mood-entry">
                                        <span class="mood-entry-mood">${record.mood}</span>
                                        <span class="mood-entry-date">${new Date(record.created_at).toLocaleDateString()}</span>
                                        ${record.notes ? `<span class="mood-entry-notes">${record.notes}</span>` : ''}
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        ` : ''}
                    </div>
                `;
            } else {
                document.getElementById('progressContent').innerHTML = `
                    <p>No mood data available yet. Start tracking your mood to see your weekly progress!</p>
                `;
            }
        } catch (error) {
            document.getElementById('progressContent').innerHTML = `
                <p>Error loading progress data. Please try again.</p>
            `;
        }
    }

    // Initialize card interactions
    function initializeCardInteractions() {
        // Card action buttons (excluding primary buttons that are links)
        const cardActionBtns = document.querySelectorAll('.card-action-btn:not(.primary), .wellness-btn');
        console.log('Found card action buttons:', cardActionBtns.length);
        
        cardActionBtns.forEach(btn => {
            console.log('Button found:', btn, 'data-feature:', btn.getAttribute('data-feature'));
            btn.addEventListener('click', function() {
                const feature = this.getAttribute('data-feature');
                console.log('Button clicked, feature:', feature);
                if (feature) {
                    showFeature(feature);
                }
            });
        });
        
        // Question prompts
        const questionPrompts = document.querySelectorAll('.question-prompt');
        questionPrompts.forEach(prompt => {
            prompt.addEventListener('click', function() {
                const question = this.getAttribute('data-prompt');
                if (question) {
                    chatInput.value = question;
                    sendMessage();
                }
            });
        });
        
        // Day buttons
        const dayBtns = document.querySelectorAll('.day-btn');
        dayBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                // Remove active class from all buttons
                dayBtns.forEach(b => b.classList.remove('active'));
                // Add active class to clicked button
                this.classList.add('active');
            });
        });
    }

    // Check for login flag and show mood popup immediately
    if (sessionStorage.getItem('justLoggedIn') === 'true') {
        // Clear the flag
        sessionStorage.removeItem('justLoggedIn');
        // Show mood popup immediately
        showMoodPopup();
    } else {
        // Check for mood tracking after dashboard loads (only for regular visits)
        setTimeout(() => {
            checkTodaysMood();
        }, 1000);
    }
    
    // Initialize card interactions after everything is loaded
    setTimeout(() => {
        initializeCardInteractions();
        
        // Also add direct event listener for mood tracker button as backup
        const moodTrackerBtn = document.querySelector('.wellness-btn[data-feature="mood-tracker"]');
        if (moodTrackerBtn) {
            console.log('Found mood tracker button, adding direct listener');
            moodTrackerBtn.addEventListener('click', function(e) {
                e.preventDefault();
                console.log('Mood tracker button clicked directly');
                showMoodPopup();
            });
        } else {
            console.log('Mood tracker button not found');
        }
    }, 100);
});
