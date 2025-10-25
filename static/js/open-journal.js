document.addEventListener('DOMContentLoaded', function() {
    const openJournalForm = document.getElementById('openJournalForm');
    const openJournalContent = document.getElementById('openJournalContent');
    const emotionTag = document.getElementById('emotionTag');
    const shareText = document.getElementById('shareText');
    const shareLoading = document.getElementById('shareLoading');
    const alertContainer = document.getElementById('alertContainer');
    const communityPosts = document.getElementById('communityPosts');
    const refreshFeed = document.getElementById('refreshFeed');

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

    function setLoading(loading) {
        if (loading) {
            shareText.classList.add('hidden');
            shareLoading.classList.remove('hidden');
            openJournalForm.querySelector('button').disabled = true;
        } else {
            shareText.classList.remove('hidden');
            shareLoading.classList.add('hidden');
            openJournalForm.querySelector('button').disabled = false;
        }
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

    function getEmotionEmoji(emotion) {
        const emotions = {
            'happy': '😊',
            'sad': '😢',
            'anxious': '😰',
            'angry': '😠',
            'grateful': '🙏',
            'confused': '😕',
            'hopeful': '🌟',
            'lonely': '😔',
            'excited': '🎉',
            'peaceful': '☮️'
        };
        return emotions[emotion] || '💭';
    }

    function renderCommunityPost(post) {
        return `
            <div class="post-item" data-post-id="${post.id}">
                <div class="post-content">${post.content}</div>
                <div class="post-meta">
                    ${post.emotion_tag ? `
                        <div class="post-emotion">
                            ${getEmotionEmoji(post.emotion_tag)} ${post.emotion_tag.charAt(0).toUpperCase() + post.emotion_tag.slice(1)}
                        </div>
                    ` : ''}
                    <div class="post-timestamp">${formatDate(post.created_at)}</div>
                </div>
                <div class="post-actions">
                    <button class="post-action" onclick="addReaction('${post.id}', 'empathy')">
                        💙 I feel this
                    </button>
                    <button class="post-action" onclick="addReaction('${post.id}', 'support')">
                        💪 Sending strength
                    </button>
                    <button class="post-action" onclick="flagPost('${post.id}')">
                        ⚠️ Flag
                    </button>
                </div>
            </div>
        `;
    }

    function renderCommunityPosts(posts) {
        if (posts.length === 0) {
            communityPosts.innerHTML = `
                <div class="empty-feed">
                    <h3>No posts yet</h3>
                    <p>Be the first to share something with the community!</p>
                </div>
            `;
            return;
        }

        const html = posts.map(post => renderCommunityPost(post)).join('');
        communityPosts.innerHTML = html;
    }

    async function loadCommunityPosts() {
        try {
            const response = await fetch('/api/journal/open');
            const data = await response.json();
            
            if (response.ok) {
                renderCommunityPosts(data.journals);
            } else {
                communityPosts.innerHTML = `
                    <p style="text-align: center; color: #e17055; padding: 2rem;">
                        Error loading community posts. Please refresh the page.
                    </p>
                `;
            }
        } catch (error) {
            console.error('Error loading community posts:', error);
            communityPosts.innerHTML = `
                <p style="text-align: center; color: #e17055; padding: 2rem;">
                    Error loading community posts. Please refresh the page.
                </p>
            `;
        }
    }

    async function shareWithCommunity() {
        const content = openJournalContent.value.trim();
        const emotion = emotionTag.value;
        
        if (!content) {
            showAlert('Please write something before sharing');
            return;
        }
        
        setLoading(true);
        alertContainer.innerHTML = '';
        
        try {
            const response = await fetch('/api/journal/open', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    content: content,
                    emotion_tag: emotion
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showAlert('Post shared with community successfully!', 'success');
                openJournalContent.value = '';
                emotionTag.value = '';
                loadCommunityPosts(); // Reload posts
            } else {
                showAlert(data.error || 'Failed to share post');
            }
        } catch (error) {
            showAlert('Network error. Please try again.');
            console.error('Share post error:', error);
        } finally {
            setLoading(false);
        }
    }

    // Global functions for reactions
    window.addReaction = async function(postId, reactionType) {
        try {
            const response = await fetch(`/api/journal/open/${postId}/react`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    reaction_type: reactionType
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showAlert('Reaction added!', 'success');
            } else {
                showAlert(data.error || 'Failed to add reaction');
            }
        } catch (error) {
            showAlert('Network error. Please try again.');
            console.error('Add reaction error:', error);
        }
    };

    window.flagPost = async function(postId) {
        if (confirm('Are you sure you want to flag this post for moderation?')) {
            try {
                const response = await fetch(`/api/journal/open/${postId}/flag`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showAlert('Post flagged for moderation. Thank you for helping keep the community safe.', 'success');
                } else {
                    showAlert(data.error || 'Failed to flag post');
                }
            } catch (error) {
                showAlert('Network error. Please try again.');
                console.error('Flag post error:', error);
            }
        }
    };

    // Event listeners
    openJournalForm.addEventListener('submit', function(e) {
        e.preventDefault();
        shareWithCommunity();
    });

    // Refresh feed button
    if (refreshFeed) {
        refreshFeed.addEventListener('click', function() {
            loadCommunityPosts();
        });
    }

    // Load community posts on page load
    loadCommunityPosts();
});
