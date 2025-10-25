document.addEventListener('DOMContentLoaded', function() {
    const questionContainer = document.getElementById('questionContainer');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');
    const progressFill = document.getElementById('progressFill');
    const currentStepSpan = document.getElementById('currentStep');
    const totalStepsSpan = document.getElementById('totalSteps');
    const alertContainer = document.getElementById('alertContainer');

    let currentStep = 0;
    let responses = {};
    let onboardingLevel = 'balanced'; // Default level

    // Define all onboarding questions
    const questions = [
        // Phase 1: Consent & Tone
        {
            id: 'onboarding_level',
            title: 'Before we start, how would you like our chats to feel?',
            type: 'single',
            options: [
                { value: 'light', label: 'Keep it light 🌤️', description: 'Friendly and supportive' },
                { value: 'balanced', label: 'Balanced ⚖️', description: 'Thoughtful but not overwhelming' },
                { value: 'deep', label: 'Let\'s go deeper 💭', description: 'Deep exploration and reflection' }
            ],
            required: false,
            default: 'balanced'
        },

        // Phase 2: Life Context (Tier 1 Demographics)
        {
            id: 'employment_status',
            title: 'Which of these best describes your current phase of life?',
            type: 'single',
            options: [
                { value: 'student', label: 'Student' },
                { value: 'working_fulltime', label: 'Working full-time' },
                { value: 'self_employed', label: 'Self-employed' },
                { value: 'looking_for_work', label: 'Looking for work' },
                { value: 'other', label: 'Something else' }
            ],
            required: false,
            skipOption: true
        },
        {
            id: 'living_situation',
            title: 'Do you usually live alone or with people?',
            type: 'single',
            options: [
                { value: 'alone', label: 'Alone' },
                { value: 'with_family', label: 'With family' },
                { value: 'with_roommates', label: 'With roommates' },
                { value: 'other', label: 'Other' }
            ],
            required: false,
            skipOption: true
        },
        {
            id: 'therapy_history',
            title: 'Have you ever talked to a therapist or counselor before?',
            type: 'single',
            options: [
                { value: 'currently', label: 'Yes, currently' },
                { value: 'past', label: 'Yes, in the past' },
                { value: 'never', label: 'Never' }
            ],
            required: false,
            skipOption: true
        },
        {
            id: 'medication',
            title: 'Are you currently taking any medication for sleep, mood, or focus?',
            type: 'single',
            options: [
                { value: 'yes', label: 'Yes' },
                { value: 'no', label: 'No' },
                { value: 'prefer_not_to_say', label: 'Prefer not to say' }
            ],
            required: false,
            skipOption: true
        },

        // Phase 3: Mood Snapshot (Tier 2 Emotional State)
        {
            id: 'primary_affect',
            title: 'If you had to pick one word for how you\'ve been feeling lately, what would it be?',
            type: 'single',
            options: [
                { value: 'tired', label: 'Tired' },
                { value: 'okay', label: 'Okay' },
                { value: 'anxious', label: 'Anxious' },
                { value: 'numb', label: 'Numb' },
                { value: 'overwhelmed', label: 'Overwhelmed' },
                { value: 'peaceful', label: 'Peaceful' },
                { value: 'motivated', label: 'Motivated' },
                { value: 'sad', label: 'Sad' },
                { value: 'other', label: 'Other (describe)' }
            ],
            required: false,
            skipOption: true,
            allowCustom: true
        },
        {
            id: 'affect_duration',
            title: 'Has this feeling been there for a while or does it come and go?',
            type: 'single',
            options: [
                { value: 'comes_and_goes', label: 'Comes and goes' },
                { value: 'weeks', label: 'Has been there for weeks' },
                { value: 'hard_to_tell', label: 'Hard to tell' }
            ],
            required: false,
            skipOption: true
        },
        {
            id: 'morning_mood',
            title: 'When you wake up most mornings, what\'s the first feeling that shows up?',
            type: 'text',
            placeholder: 'Describe your typical morning feeling...',
            required: false,
            skipOption: true
        },

        // Phase 4: Function & Energy (Tier 4 Functional Impact)
        {
            id: 'sleep_quality',
            title: 'How\'s your sleep been lately?',
            type: 'single',
            options: [
                { value: 'pretty_good', label: 'Pretty good' },
                { value: 'average', label: 'Average' },
                { value: 'not_great', label: 'Not great' },
                { value: 'terrible', label: 'Terrible' },
                { value: 'prefer_not_to_say', label: 'Prefer not to say' }
            ],
            required: false,
            skipOption: true
        },
        {
            id: 'energy_level',
            title: 'How\'s your energy during the day?',
            type: 'single',
            options: [
                { value: 'high', label: 'High' },
                { value: 'medium', label: 'Medium' },
                { value: 'low', label: 'Low' },
                { value: 'drained', label: 'Drained' },
                { value: 'prefer_not_to_say', label: 'Prefer not to say' }
            ],
            required: false,
            skipOption: true
        },
        {
            id: 'focus_level',
            title: 'How\'s your focus when you need to get things done?',
            type: 'single',
            options: [
                { value: 'sharp_as_usual', label: 'Sharp as usual' },
                { value: 'a_bit_off', label: 'A bit off' },
                { value: 'very_hard', label: 'Very hard to focus' },
                { value: 'prefer_not_to_say', label: 'Prefer not to say' }
            ],
            required: false,
            skipOption: true
        },
        {
            id: 'social_withdrawal',
            title: 'Do you find yourself avoiding people or activities you used to enjoy?',
            type: 'single',
            options: [
                { value: 'no', label: 'No, I\'m social as usual' },
                { value: 'sometimes', label: 'Sometimes' },
                { value: 'quite_often', label: 'Quite often' },
                { value: 'almost_always', label: 'Almost always' },
                { value: 'prefer_not_to_say', label: 'Prefer not to say' }
            ],
            required: false,
            skipOption: true
        },
        {
            id: 'appetite_change',
            title: 'Any changes in your appetite lately?',
            type: 'single',
            options: [
                { value: 'normal', label: 'Eating normally' },
                { value: 'less', label: 'Eating less' },
                { value: 'more', label: 'Eating more' },
                { value: 'cant_tell', label: 'Can\'t tell' },
                { value: 'prefer_not_to_say', label: 'Prefer not to say' }
            ],
            required: false,
            skipOption: true
        },

        // Phase 5: Cognitive Beliefs (Tier 3 CPT Themes) - Conditional
        {
            id: 'belief_safety',
            title: 'Would you say you generally feel safe in most places?',
            type: 'single',
            options: [
                { value: 'yes', label: 'Yes' },
                { value: 'sometimes', label: 'Sometimes' },
                { value: 'rarely', label: 'Rarely' },
                { value: 'prefer_not_to_say', label: 'Prefer not to say' }
            ],
            required: false,
            skipOption: true,
            conditional: true
        },
        {
            id: 'belief_trust',
            title: 'Do you find it easy to trust people?',
            type: 'single',
            options: [
                { value: 'yes', label: 'Yes' },
                { value: 'depends', label: 'Depends' },
                { value: 'not_really', label: 'Not really' },
                { value: 'prefer_not_to_say', label: 'Prefer not to say' }
            ],
            required: false,
            skipOption: true,
            conditional: true
        },
        {
            id: 'belief_control',
            title: 'Do you feel like you have control over what happens in your life?',
            type: 'single',
            options: [
                { value: 'mostly_yes', label: 'Mostly yes' },
                { value: 'sometimes', label: 'Sometimes' },
                { value: 'not_much', label: 'Not much lately' },
                { value: 'prefer_not_to_say', label: 'Prefer not to say' }
            ],
            required: false,
            skipOption: true,
            conditional: true
        },
        {
            id: 'belief_self',
            title: 'Are you usually kind to yourself, or do you tend to be very self-critical?',
            type: 'single',
            options: [
                { value: 'kind', label: 'Kind' },
                { value: 'depends', label: 'Depends' },
                { value: 'very_critical', label: 'Very critical' },
                { value: 'prefer_not_to_say', label: 'Prefer not to say' }
            ],
            required: false,
            skipOption: true,
            conditional: true
        },
        {
            id: 'belief_intimacy',
            title: 'Do you find it easy to open up or get close to people emotionally?',
            type: 'single',
            options: [
                { value: 'easy', label: 'Easy' },
                { value: 'a_bit_hard', label: 'A bit hard' },
                { value: 'very_difficult', label: 'Very difficult' },
                { value: 'prefer_not_to_say', label: 'Prefer not to say' }
            ],
            required: false,
            skipOption: true,
            conditional: true
        },

        // Phase 6: Risk & Resilience (Tier 5)
        {
            id: 'social_support',
            title: 'When things get really heavy, do you have someone you can reach out to?',
            type: 'single',
            options: [
                { value: 'yes_definitely', label: 'Yes, definitely' },
                { value: 'maybe_one_or_two', label: 'Maybe one or two' },
                { value: 'not_really', label: 'Not really' },
                { value: 'prefer_not_to_say', label: 'Prefer not to say' }
            ],
            required: false,
            skipOption: true
        },
        {
            id: 'coping_skills',
            title: 'What helps you calm down or feel grounded?',
            type: 'multiple',
            options: [
                { value: 'music', label: 'Music' },
                { value: 'walks', label: 'Walks' },
                { value: 'journaling', label: 'Journaling' },
                { value: 'talking_to_someone', label: 'Talking to someone' },
                { value: 'breathing_exercises', label: 'Breathing exercises' },
                { value: 'nothing_helps', label: 'Nothing seems to help' },
                { value: 'other', label: 'Other' }
            ],
            required: false,
            skipOption: true,
            allowCustom: true
        },
        {
            id: 'recent_trauma',
            title: 'Have you faced something really difficult or life-changing recently?',
            type: 'single',
            options: [
                { value: 'yes', label: 'Yes' },
                { value: 'not_really', label: 'Not really' },
                { value: 'prefer_not_to_say', label: 'Prefer not to say' }
            ],
            required: false,
            skipOption: true
        },
        {
            id: 'suicidal_thoughts',
            title: 'Sometimes people feel hopeless or think about giving up. Has that ever crossed your mind recently?',
            type: 'single',
            options: [
                { value: 'no', label: 'No' },
                { value: 'yes_briefly', label: 'Yes, briefly' },
                { value: 'yes_often', label: 'Yes, often' },
                { value: 'prefer_not_to_say', label: 'Prefer not to say' }
            ],
            required: false,
            skipOption: true,
            emergency: true
        },

        // Phase 7: Meaning & Motivation
        {
            id: 'personalization_goal',
            title: 'What\'s something you\'d like to feel more of these days?',
            type: 'single',
            options: [
                { value: 'energy', label: 'Energy' },
                { value: 'calm', label: 'Calm' },
                { value: 'hope', label: 'Hope' },
                { value: 'focus', label: 'Focus' },
                { value: 'connection', label: 'Connection' },
                { value: 'joy', label: 'Joy' },
                { value: 'other', label: 'Other' }
            ],
            required: false,
            skipOption: true,
            allowCustom: true
        },
        {
            id: 'purposeful_activities',
            title: 'What usually gives you a sense of purpose or meaning?',
            type: 'text',
            placeholder: 'Describe what gives you purpose...',
            required: false,
            skipOption: true
        },

        // Phase 8: Confirmation & Next Step
        {
            id: 'start_preference',
            title: 'What would you like to start with?',
            type: 'single',
            options: [
                { value: 'mood_tracking', label: 'Mood tracking' },
                { value: 'energy_tips', label: 'Energy tips' },
                { value: 'daily_reflections', label: 'Daily reflections' },
                { value: 'just_chat', label: 'Just chat for now' }
            ],
            required: false,
            skipOption: true
        }
    ];

    // Filter questions based on onboarding level and conditions
    function getFilteredQuestions() {
        return questions.filter(q => {
            if (q.conditional && (onboardingLevel === 'light')) {
                return false;
            }
            return true;
        });
    }

    function updateProgress() {
        const filteredQuestions = getFilteredQuestions();
        const progress = ((currentStep + 1) / filteredQuestions.length) * 100;
        progressFill.style.width = `${progress}%`;
        currentStepSpan.textContent = currentStep + 1;
        totalStepsSpan.textContent = filteredQuestions.length;
    }

    function showQuestion(step) {
        const filteredQuestions = getFilteredQuestions();
        const question = filteredQuestions[step];
        
        if (!question) return;

        let html = `
            <div class="question-card">
                <h2 class="question-title">${question.title}</h2>
                <div class="question-content">
        `;

        if (question.type === 'single') {
            question.options.forEach(option => {
                html += `
                    <label class="option-label">
                        <input type="radio" name="${question.id}" value="${option.value}" class="option-input">
                        <span class="option-text">${option.label}</span>
                        ${option.description ? `<span class="option-description">${option.description}</span>` : ''}
                    </label>
                `;
            });
        } else if (question.type === 'multiple') {
            question.options.forEach(option => {
                html += `
                    <label class="option-label">
                        <input type="checkbox" name="${question.id}" value="${option.value}" class="option-input">
                        <span class="option-text">${option.label}</span>
                    </label>
                `;
            });
        } else if (question.type === 'text') {
            html += `
                <textarea name="${question.id}" class="text-input" placeholder="${question.placeholder || ''}" rows="4"></textarea>
            `;
        }

        if (question.allowCustom) {
            html += `
                <div class="custom-input-container">
                    <input type="text" name="${question.id}_custom" class="custom-input" placeholder="Describe...">
                </div>
            `;
        }

        if (question.skipOption) {
            html += `
                <div class="skip-option">
                    <label class="option-label skip-label">
                        <input type="radio" name="${question.id}" value="skip" class="option-input">
                        <span class="option-text">Skip</span>
                    </label>
                    <label class="option-label skip-label">
                        <input type="radio" name="${question.id}" value="prefer_not_to_say" class="option-input">
                        <span class="option-text">Prefer not to say</span>
                    </label>
                </div>
            `;
        }

        html += `
                </div>
            </div>
        `;

        questionContainer.innerHTML = html;

        // Set previous response if exists
        if (responses[question.id]) {
            const inputs = questionContainer.querySelectorAll(`input[name="${question.id}"]`);
            inputs.forEach(input => {
                if (input.value === responses[question.id]) {
                    input.checked = true;
                }
            });
        }

        updateProgress();
    }

    function collectCurrentResponse() {
        const filteredQuestions = getFilteredQuestions();
        const question = filteredQuestions[currentStep];
        
        if (!question) return;

        const formData = new FormData();
        const inputs = questionContainer.querySelectorAll(`input[name="${question.id}"], textarea[name="${question.id}"]`);
        
        let response = null;
        
        if (question.type === 'single') {
            const selected = questionContainer.querySelector(`input[name="${question.id}"]:checked`);
            if (selected) {
                response = selected.value;
            }
        } else if (question.type === 'multiple') {
            const selected = Array.from(questionContainer.querySelectorAll(`input[name="${question.id}"]:checked`));
            response = selected.map(input => input.value);
        } else if (question.type === 'text') {
            const textarea = questionContainer.querySelector(`textarea[name="${question.id}"]`);
            if (textarea) {
                response = textarea.value;
            }
        }

        if (response && response !== 'skip' && response !== 'prefer_not_to_say') {
            responses[question.id] = response;
            
            // Update onboarding level if this is the onboarding_level question
            if (question.id === 'onboarding_level') {
                onboardingLevel = response;
            }
        }
    }

    function showNextQuestion() {
        collectCurrentResponse();
        
        const filteredQuestions = getFilteredQuestions();
        
        if (currentStep < filteredQuestions.length - 1) {
            currentStep++;
            showQuestion(currentStep);
            
            prevBtn.style.display = 'inline-block';
            
            if (currentStep === filteredQuestions.length - 1) {
                nextBtn.style.display = 'none';
                submitBtn.style.display = 'inline-block';
            } else {
                nextBtn.style.display = 'inline-block';
                submitBtn.style.display = 'none';
            }
        }
    }

    function showPreviousQuestion() {
        if (currentStep > 0) {
            currentStep--;
            showQuestion(currentStep);
            
            if (currentStep === 0) {
                prevBtn.style.display = 'none';
            }
            
            nextBtn.style.display = 'inline-block';
            submitBtn.style.display = 'none';
        }
    }

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

    async function submitOnboarding() {
        collectCurrentResponse();
        
        console.log('Submitting onboarding data:', {
            onboarding_data: responses,
            onboarding_level: onboardingLevel
        });
        
        // Authentication is already handled by the server-side route
        
        try {
            console.log('Sending onboarding data:', responses);

            const response = await fetch('/api/onboarding/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({
                    onboarding_data: responses,
                    onboarding_level: onboardingLevel
                })
            });
            
            console.log('Onboarding response status:', response.status);
            const data = await response.json();
            console.log('Onboarding response data:', data);
            
            if (response.ok) {
                showAlert('Onboarding completed successfully!', 'success');
                console.log('Redirecting to dashboard in 2 seconds...');
                setTimeout(() => {
                    console.log('Redirecting to dashboard now...');
                    // Try dashboard first, fallback to home
                    window.location.href = '/dashboard';
                }, 2000);
            } else {
                console.error('Onboarding failed:', data);
                showAlert(data.error || 'Failed to complete onboarding. Status: ' + response.status);
            }
        } catch (error) {
            console.error('Onboarding network error:', error);
            showAlert('Network error. Please try again.');
        }
    }

    // Event listeners
    nextBtn.addEventListener('click', showNextQuestion);
    prevBtn.addEventListener('click', showPreviousQuestion);
    submitBtn.addEventListener('click', submitOnboarding);

    // Initialize
    showQuestion(0);
});