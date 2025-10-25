document.addEventListener('DOMContentLoaded', function() {
    const journalForm = document.getElementById('journalForm');
    const journalContent = document.getElementById('journalContent');
    const saveText = document.getElementById('saveText');
    const saveLoading = document.getElementById('saveLoading');
    const alertContainer = document.getElementById('alertContainer');
    const journalEntries = document.getElementById('journalEntries');

    function showAlert(message, type = 'error') {
        alertContainer.innerHTML = `
            <div class="alert alert-${type}">
                ${message}
            </div>
        `;
    }

    function setLoading(loading) {
        if (loading) {
            saveText.classList.add('hidden');
            saveLoading.classList.remove('hidden');
            journalForm.querySelector('button').disabled = true;
        } else {
            saveText.classList.remove('hidden');
            saveLoading.classList.add('hidden');
            journalForm.querySelector('button').disabled = false;
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

    function formatSoupieResponse(text) {
        console.log('Original text:', text); // Debug log
        
        if (!text) return '';
        
        // Manual approach - split by ** and rebuild
        const parts = text.split(/(\*\*[^*]+\*\*)/g);
        let formatted = '';
        
        for (let i = 0; i < parts.length; i++) {
            const part = parts[i];
            if (part.startsWith('**') && part.endsWith('**')) {
                // This is a bold section
                const content = part.slice(2, -2); // Remove **
                formatted += `<strong>${content}</strong>`;
            } else {
                // Regular text
                formatted += part.replace(/\n/g, '<br>');
            }
        }
        
        console.log('Formatted text:', formatted); // Debug log
        
        // Return the formatted content directly
        return formatted;
    }

    function renderJournalEntry(entry) {
        return `
            <div class="journal-entry">
                <div class="journal-content">${entry.content}</div>
                ${entry.ai_summary ? `
                    <div class="soupie-thoughts">
                        <strong>What Soupie thinks:</strong>
                        <div class="soupie-content" id="soupie-content-${entry.id}"></div>
                    </div>
                ` : ''}
                <div class="journal-meta">
                    <span>${formatDate(entry.created_at)}</span>
                    <button onclick="generateSummary('${entry.id}')" class="btn btn-secondary" style="padding: 0.5rem 1rem; font-size: 0.9rem;">
                        ${entry.ai_summary ? 'Regenerate Soupie\'s thoughts' : 'What does Soupie think?'}
                    </button>
                </div>
            </div>
        `;
    }

    function renderJournalEntries(entries) {
        if (entries.length === 0) {
            journalEntries.innerHTML = `
                <p style="text-align: center; color: #636e72; padding: 2rem;">
                    No journal entries yet. Start writing your first entry above!
                </p>
            `;
            return;
        }

        const html = entries.map(entry => renderJournalEntry(entry)).join('');
        journalEntries.innerHTML = html;
        
        // Now populate the formatted content for each entry
        entries.forEach(entry => {
            if (entry.ai_summary) {
                console.log('Processing entry:', entry.id, 'with summary:', entry.ai_summary);
                const contentDiv = document.getElementById(`soupie-content-${entry.id}`);
                if (contentDiv) {
                    const formatted = formatSoupieResponse(entry.ai_summary);
                    console.log('Setting innerHTML to:', formatted);
                    contentDiv.innerHTML = formatted;
                } else {
                    console.log('Content div not found for entry:', entry.id);
                }
            }
        });
    }

    async function loadJournalEntries() {
        try {
            const response = await fetch('/api/journal/private');
            const data = await response.json();
            
            if (response.ok) {
                renderJournalEntries(data.journals);
            } else {
                journalEntries.innerHTML = `
                    <p style="text-align: center; color: #e17055; padding: 2rem;">
                        Error loading journal entries. Please refresh the page.
                    </p>
                `;
            }
        } catch (error) {
            console.error('Error loading journal entries:', error);
            journalEntries.innerHTML = `
                <p style="text-align: center; color: #e17055; padding: 2rem;">
                    Error loading journal entries. Please refresh the page.
                </p>
            `;
        }
    }

    async function saveJournalEntry() {
        const content = journalContent.value.trim();
        
        if (!content) {
            showAlert('Please write something before saving');
            return;
        }
        
        setLoading(true);
        alertContainer.innerHTML = '';
        
        try {
            const response = await fetch('/api/journal/private', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    content: content
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showAlert('Journal entry saved successfully!', 'success');
                journalContent.value = '';
                loadJournalEntries(); // Reload entries
            } else {
                showAlert(data.error || 'Failed to save journal entry');
            }
        } catch (error) {
            showAlert('Network error. Please try again.');
            console.error('Save journal error:', error);
        } finally {
            setLoading(false);
        }
    }

    // Global function for AI summary generation
    window.generateSummary = async function(entryId) {
        try {
            const response = await fetch(`/api/journal/private/${entryId}/summarize`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showAlert('Soupie\'s thoughts generated successfully!', 'success');
                loadJournalEntries(); // Reload to show the summary
            } else {
                showAlert(data.error || 'Failed to generate summary');
            }
        } catch (error) {
            showAlert('Network error. Please try again.');
            console.error('Generate summary error:', error);
        }
    };

    // Event listeners
    journalForm.addEventListener('submit', function(e) {
        e.preventDefault();
        saveJournalEntry();
    });

    // Load journal entries on page load
    loadJournalEntries();
    
    // Test function for debugging
    window.testFormatting = function() {
        const testText = '**Test Bold** and **Key Insight:** test content';
        const result = formatSoupieResponse(testText);
        console.log('Test formatting result:', result);
        
        // Create a test div to see the result
        const testDiv = document.createElement('div');
        testDiv.innerHTML = result;
        testDiv.style.border = '1px solid red';
        testDiv.style.padding = '10px';
        testDiv.style.margin = '10px';
        document.body.appendChild(testDiv);
    };
});
