#!/usr/bin/env python3
"""
Simple Flask app runner that bypasses the ast.Str issue
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Change to project directory
os.chdir(project_root)

# Set environment variables
os.environ.setdefault('FLASK_ENV', 'development')

try:
    from flask import Flask, request, jsonify, render_template, make_response, redirect, url_for
    from flask_cors import CORS
    import os
    from dotenv import load_dotenv
    import requests
    import uuid
    from datetime import datetime

    # Load environment variables
    load_dotenv()

    # Import JSON database and auth
    from api.json_db import db, get_db
    from api.auth import hash_password, verify_password, create_jwt_token, jwt_required, get_current_user_id
    from api.scoring_engine import scoring_engine

    app = Flask(__name__, template_folder='templates', static_folder='static')
    CORS(app)

    # Initialize database tables
    db.init_tables()
    
    # Add mood tracking table if it doesn't exist
    try:
        mood_records = db._read_table("mood_records")
    except:
        db._write_table("mood_records", [])

    # Gemini API helper
    def call_gemini(prompt):
        """Call Gemini API with the given prompt"""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return "AI service not configured. Please set GEMINI_API_KEY in your environment."
        
        try:
            # Try Gemini 2.0 Flash model
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return "AI service error: Invalid API key or model not available. Please check your GEMINI_API_KEY."
            elif e.response.status_code == 403:
                return "AI service error: API key does not have permission. Please check your GEMINI_API_KEY."
            elif e.response.status_code == 503:
                return "AI service error: HTTP 503 - Service temporarily overloaded. Please try again later."
            else:
                return f"AI service error: HTTP {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"AI service error: {str(e)}"

    # Routes
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/test-auth')
    @jwt_required
    def test_auth():
        user_id = get_current_user_id()
        user = db.get_user_by_id(user_id)
        return jsonify({
            'user_id': user_id,
            'onboarding_done': user.get('onboarding_done', False) if user else None,
            'user_exists': user is not None
        })

    @app.route('/api/register', methods=['POST'])
    def register():
        try:
            data = request.get_json()
            email = data.get('email')
            phone = data.get('phone')
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            password = data.get('password')
            
            # Validation
            if not first_name or not last_name or not password:
                return jsonify({'error': 'Missing required fields'}), 400
            image.png
            if not email and not phone:
                return jsonify({'error': 'Either email or phone is required'}), 400
            
            # Check if user already exists
            existing_user = None
            if email:
                existing_user = db.get_user_by_email(email)
            elif phone:
                users = db._read_table("user_registration")
                for user in users:
                    if user.get("phone") == phone:
                        existing_user = user
                        break
            
            if existing_user:
                return jsonify({'error': 'User already exists'}), 409
            
            # Create new user
            hashed_password = hash_password(password)
            user_data = {
                "email": email,
                "phone": phone,
                "first_name": first_name,
                "last_name": last_name,
                "password_hash": hashed_password,
                "onboarding_done": False
            }
            
            user_id = db.create_user(user_data)
            
            # Create JWT token
            token = create_jwt_token(user_id, email or phone)
            
            # Set HTTP-only cookie
            response = make_response(jsonify({
                'message': 'User registered successfully',
                'user_id': user_id,
                'onboarding_done': False
            }))
            response.set_cookie('jwt_token', token, httponly=True, secure=False, samesite='Lax')
            
            return response
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/login', methods=['POST'])
    def login():
        try:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return jsonify({'error': 'Email and password are required'}), 400
            
            # Find user by email
            user = db.get_user_by_email(email)
            
            if not user or not verify_password(password, user.get('password_hash')):
                return jsonify({'error': 'Invalid credentials'}), 401
            
            # Create JWT token
            token = create_jwt_token(user.get('id'), user.get('email'))
            
            # Set HTTP-only cookie
            onboarding_done = user.get('onboarding_done', False)
            print(f"Login - User onboarding_done status: {onboarding_done}")
            response = make_response(jsonify({
                'message': 'Login successful',
                'user_id': user.get('id'),
                'onboarding_done': onboarding_done
            }))
            response.set_cookie('jwt_token', token, httponly=True, secure=False, samesite='Lax')
            
            return response
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/logout', methods=['POST'])
    def logout():
        response = make_response(jsonify({'message': 'Logged out successfully'}))
        response.set_cookie('jwt_token', '', expires=0)
        return response

    @app.route('/logout')
    def logout_page():
        response = make_response(redirect('/login'))
        response.set_cookie('jwt_token', '', expires=0)
        return response

    @app.route('/api/onboarding/questions', methods=['GET'])
    @jwt_required
    def get_onboarding_questions():
        # Return empty list for now - questions will be added later
        return jsonify({'questions': []})

    @app.route('/api/onboarding/submit', methods=['POST'])
    @jwt_required
    def submit_onboarding():
        try:
            data = request.get_json()
            onboarding_data = data.get('onboarding_data', {})
            onboarding_level = data.get('onboarding_level', 'balanced')
            
            user_id = get_current_user_id()
            print(f"Processing onboarding for user: {user_id}")
            
            # Create comprehensive onboarding record
            onboarding_record = {
                'user_id': user_id,
                'onboarding_level': onboarding_level,
                'tier_1_demographics': {
                    'employment_status': onboarding_data.get('employment_status'),
                    'living_situation': onboarding_data.get('living_situation'),
                    'therapy_history': {
                        'previous_therapy': onboarding_data.get('therapy_history'),
                        'therapy_type': onboarding_data.get('medication')
                    }
                },
                'tier_2_emotional_state': {
                    'primary_affect': onboarding_data.get('primary_affect'),
                    'emotion_description': onboarding_data.get('primary_affect_custom'),
                    'affect_confidence': onboarding_data.get('affect_duration'),
                    'emotion_intensity': 'medium',  # Default
                    'mood_trend_start': onboarding_data.get('morning_mood')
                },
                'tier_3_cognitive_themes': {
                    'belief_safety_negative': {
                        'present': onboarding_data.get('belief_safety') in ['sometimes', 'rarely'],
                        'confidence': 'medium'
                    },
                    'belief_trust_negative': {
                        'present': onboarding_data.get('belief_trust') in ['depends', 'not_really'],
                        'confidence': 'medium'
                    },
                    'belief_control_low': {
                        'present': onboarding_data.get('belief_control') in ['sometimes', 'not_much'],
                        'confidence': 'medium'
                    },
                    'belief_self_low': {
                        'present': onboarding_data.get('belief_self') in ['depends', 'very_critical'],
                        'confidence': 'medium'
                    },
                    'belief_intimacy_low': {
                        'present': onboarding_data.get('belief_intimacy') in ['a_bit_hard', 'very_difficult'],
                        'confidence': 'medium'
                    }
                },
                'tier_4_functional_impact': {
                    'sleep_quality': onboarding_data.get('sleep_quality'),
                    'energy_level': onboarding_data.get('energy_level'),
                    'focus_level': onboarding_data.get('focus_level'),
                    'social_withdrawal': onboarding_data.get('social_withdrawal'),
                    'appetite_change': onboarding_data.get('appetite_change')
                },
                'tier_5_risk_and_protective_factors': {
                    'protective_factors': {
                        'social_support': onboarding_data.get('social_support'),
                        'coping_skills': onboarding_data.get('coping_skills', []),
                        'purposeful_activities': onboarding_data.get('purposeful_activities')
                    },
                    'risk_factors': {
                        'recent_trauma': onboarding_data.get('recent_trauma') == 'yes',
                        'suicidal_thoughts': onboarding_data.get('suicidal_thoughts') in ['yes_briefly', 'yes_often']
                    }
                },
                'tier_7_ai_summary_card': {
                    'personalization_goal': onboarding_data.get('personalization_goal')
                },
                'tier_8_temporal_tracking': {
                    'mood_trend_start': onboarding_data.get('morning_mood')
                },
                'next_module': onboarding_data.get('start_preference', 'just_chat'),
                'metadata': {
                    'reviewed_by_clinician': False,
                    'created_at': datetime.now().isoformat()
                }
            }
            
            # Process onboarding data through scoring engine
            insights = scoring_engine.process_onboarding_data(onboarding_data)
            
            # Add insights to onboarding record
            onboarding_record['insights'] = insights
            
            # Save onboarding data
            print("Creating onboarding record...")
            record_id = db.create_onboarding_record(onboarding_record)
            print(f"Onboarding record created with ID: {record_id}")
            
            # Mark onboarding as done
            print("Updating user onboarding status...")
            update_success = db.update_user(user_id, {'onboarding_done': True})
            print(f"User update successful: {update_success}")
            
            # Verify the update
            user = db.get_user_by_id(user_id)
            print(f"User onboarding_done status: {user.get('onboarding_done')}")
            
            # Return insights along with success message
            return jsonify({
                'message': 'Onboarding completed successfully',
                'insights': insights
            })
            
        except Exception as e:
            print(f"Onboarding submission error: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/journal/private', methods=['POST'])
    @jwt_required
    def create_private_journal():
        try:
            data = request.get_json()
            content = data.get('content')
            
            if not content:
                return jsonify({'error': 'Content is required'}), 400
            
            user_id = get_current_user_id()
            
            entry_id = db.create_private_journal(
                user_id=user_id,
                content=content
            )
            
            return jsonify({
                'message': 'Journal entry created successfully',
                'entry_id': entry_id
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/journal/private', methods=['GET'])
    @jwt_required
    def get_private_journals():
        try:
            user_id = get_current_user_id()
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            
            all_journals = db.get_user_private_journals(user_id)
            
            # Sort by created_at descending
            all_journals.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            # Simple pagination
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            journals_page = all_journals[start_idx:end_idx]
            
            return jsonify({
                'journals': [{
                    'id': journal.get('id'),
                    'content': journal.get('content'),
                    'ai_summary': journal.get('ai_summary'),
                    'created_at': journal.get('created_at')
                } for journal in journals_page],
                'total': len(all_journals),
                'pages': (len(all_journals) + per_page - 1) // per_page,
                'current_page': page
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/journal/private/<journal_id>/summarize', methods=['POST'])
    @jwt_required
    def summarize_private_journal(journal_id):
        try:
            user_id = get_current_user_id()
            
            # Get the journal entry
            journal = db.get_private_journal_by_id(journal_id)
            if not journal or journal.get('user_id') != user_id:
                return jsonify({'error': 'Journal entry not found'}), 404
            
            # Generate "What Talksoup thinks" - personal analysis with actionable steps
            journal_content = journal.get('content')
            emotional_analysis = analyze_journal_emotions(journal_content)
            
            prompt = f"""You are Talksoup, an emotionally intelligent AI companion. Analyze this journal entry and provide your personal thoughts in this exact format:

Journal entry: "{journal_content}"

Respond in this structure:

**[Title: Create a descriptive, empathetic title that captures the essence of their day/experience]**

[Paragraph 1: Describe their day/experience with empathy and understanding. Focus on what they accomplished, felt, or went through. Be specific about their activities, emotions, and experiences. Use "You" to address them directly.]

[Paragraph 2: Offer interpretation and encouragement. Analyze their emotional state, patterns, or growth. Provide gentle insights about their behavior, feelings, or situation. Frame their experiences positively and offer supportive guidance.]

**Key Insight:** [One clear, actionable principle or takeaway that they can apply to their life]

Guidelines:
- Be warm, empathetic, and supportive like a caring friend
- Use "You" to address them directly
- Focus on understanding and validating their experience
- Be non-judgmental and encouraging
- Make the title descriptive and emotionally resonant
- Keep paragraphs substantial but readable
- End with a clear, actionable insight they can use

Example format:
**Whirlwind of Productivity and Exploration**

You had a day filled with a dynamic mix of productivity and digital exploration, seamlessly balancing your academic responsibilities with creative and technical pursuits. From diving into nursing notes to crafting event ideas and exploring AI tools, you managed to keep your curiosity alive while ticking off tasks and finding satisfaction in your achievements.

Your ability to juggle various interests and tasks, from academic to creative, shows a strong adaptability and enthusiasm for learning. Embrace the productive chaos and continue to harness your digital tools and platforms to fuel your curiosity and creativity, as they seem to be valuable allies in your journey.

**Key Insight:** Balancing diverse interests and tasks fuels both productivity and satisfaction."""
            
            # Try to get AI response with better error handling
            summary = call_gemini(prompt)
            
            # If AI service fails, provide a fallback response
            if not summary or "error" in summary.lower() or "503" in summary or "unavailable" in summary.lower():
                summary = generate_fallback_soupie_response(journal_content, emotional_analysis)
            
            # Update the journal entry with the summary
            db.update_private_journal(journal_id, {'ai_summary': summary})
            
            return jsonify({
                'message': 'Summary generated successfully',
                'summary': summary
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/journal/open', methods=['POST'])
    @jwt_required
    def create_open_journal():
        try:
            data = request.get_json()
            content = data.get('content')
            emotion_tag = data.get('emotion_tag')
            
            if not content:
                return jsonify({'error': 'Content is required'}), 400
            
            user_id = get_current_user_id()
            
            entry_id = db.create_open_journal(
                user_id=user_id,
                content=content,
                emotion_tag=emotion_tag
            )
            
            return jsonify({
                'message': 'Open journal entry created successfully',
                'entry_id': entry_id
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/journal/open', methods=['GET'])
    def get_open_journals():
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            
            all_journals = db.get_all_open_journals()
            
            # Sort by created_at descending
            all_journals.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            # Simple pagination
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            journals_page = all_journals[start_idx:end_idx]
            
            return jsonify({
                'journals': [{
                    'id': journal.get('id'),
                    'content': journal.get('content'),
                    'emotion_tag': journal.get('emotion_tag'),
                    'created_at': journal.get('created_at')
                } for journal in journals_page],
                'total': len(all_journals),
                'pages': (len(all_journals) + per_page - 1) // per_page,
                'current_page': page
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    def calculate_journal_streak(journal_entries):
        """Calculate consecutive days of journaling streak"""
        if not journal_entries:
            return 0
        
        from datetime import datetime, date, timedelta
        
        # Group entries by date
        entries_by_date = {}
        for entry in journal_entries:
            try:
                # Parse the created_at timestamp
                entry_date = datetime.fromisoformat(entry.get('created_at', '')).date()
                if entry_date not in entries_by_date:
                    entries_by_date[entry_date] = []
                entries_by_date[entry_date].append(entry)
            except (ValueError, TypeError):
                # Skip entries with invalid dates
                continue
        
        if not entries_by_date:
            return 0
        
        # Start from today and count backwards
        today = date.today()
        streak = 0
        current_date = today
        
        while current_date in entries_by_date:
            streak += 1
            current_date -= timedelta(days=1)
        
        return streak

    # Dashboard endpoint
    @app.route('/api/dashboard', methods=['GET'])
    @jwt_required
    def get_dashboard():
        try:
            user_id = get_current_user_id()
            
            # Get user info
            user = db.get_user_by_id(user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Get journal counts
            private_journals = db.get_user_private_journals(user_id)
            open_journals = db.get_user_open_journals(user_id)
            
            # Calculate streak
            streak = calculate_journal_streak(private_journals + open_journals)
            
            # Get recent activity (last 3 private journals)
            recent_private = private_journals[:3] if private_journals else []
            
            # Get today's mood
            today_mood = "—"
            try:
                from datetime import datetime, date
                today = date.today().isoformat()
                all_mood_records = db._read_table("mood_records")
                user_mood_records = [record for record in all_mood_records if record.get('user_id') == user_id]
                
                # Find today's mood record
                for record in user_mood_records:
                    record_date = record.get('created_at', '')
                    if record_date.startswith(today):
                        today_mood = record.get('mood', '—').title()
                        break
            except Exception as e:
                print(f"Error getting today's mood: {e}")
            
            return jsonify({
                'user': {
                    'first_name': user.get('first_name', 'User'),
                    'last_name': user.get('last_name', ''),
                    'onboarding_done': user.get('onboarding_done', False)
                },
                'stats': {
                    'private_journals': len(private_journals),
                    'open_journals': len(open_journals),
                    'total_journals': len(private_journals) + len(open_journals),
                    'streak': streak,
                    'today_mood': today_mood
                },
                'recent_activity': [{
                    'id': journal.get('id'),
                    'content': journal.get('content', '')[:100] + '...' if len(journal.get('content', '')) > 100 else journal.get('content', ''),
                    'created_at': journal.get('created_at')
                } for journal in recent_private]
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Profile API endpoints
    @app.route('/api/profile', methods=['GET'])
    @jwt_required
    def get_profile():
        try:
            user_id = get_current_user_id()
            user = db.get_user_by_id(user_id)
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Get user preferences (default values)
            preferences = {
                'journal_reminders': user.get('journal_reminders', 'daily'),
                'theme': user.get('theme', 'light'),
                'privacy_level': user.get('privacy_level', 'private'),
                'ai_insights': user.get('ai_insights', True),
                'email_notifications': user.get('email_notifications', True)
            }
            
            return jsonify({
                'user': {
                    'first_name': user.get('first_name', ''),
                    'last_name': user.get('last_name', ''),
                    'email': user.get('email', ''),
                    'phone': user.get('phone', '')
                },
                'preferences': preferences
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/profile/update', methods=['POST'])
    @jwt_required
    def update_profile():
        try:
            user_id = get_current_user_id()
            data = request.get_json()
            
            # Validate required fields
            if not data.get('first_name') or not data.get('last_name'):
                return jsonify({'error': 'First name and last name are required'}), 400
            
            # Check if email is being changed and if it's already taken
            if data.get('email'):
                existing_user = db.get_user_by_email(data['email'])
                if existing_user and existing_user.get('id') != user_id:
                    return jsonify({'error': 'Email already in use'}), 409
            
            # Update user data
            update_data = {
                'first_name': data.get('first_name'),
                'last_name': data.get('last_name'),
                'email': data.get('email'),
                'phone': data.get('phone', '')
            }
            
            db.update_user(user_id, update_data)
            
            return jsonify({'message': 'Profile updated successfully'})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/profile/preferences', methods=['POST'])
    @jwt_required
    def update_preferences():
        try:
            user_id = get_current_user_id()
            data = request.get_json()
            
            # Update preferences
            preferences_data = {
                'journal_reminders': data.get('journal_reminders', 'daily'),
                'theme': data.get('theme', 'light'),
                'privacy_level': data.get('privacy_level', 'private'),
                'ai_insights': data.get('ai_insights', True),
                'email_notifications': data.get('email_notifications', True)
            }
            
            db.update_user(user_id, preferences_data)
            
            return jsonify({'message': 'Preferences updated successfully'})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/profile/password', methods=['POST'])
    @jwt_required
    def change_password():
        try:
            user_id = get_current_user_id()
            data = request.get_json()
            
            current_password = data.get('current_password')
            new_password = data.get('new_password')
            
            if not current_password or not new_password:
                return jsonify({'error': 'Current password and new password are required'}), 400
            
            # Get user and verify current password
            user = db.get_user_by_id(user_id)
            if not user or not verify_password(current_password, user.get('password_hash')):
                return jsonify({'error': 'Current password is incorrect'}), 401
            
            # Update password
            hashed_password = hash_password(new_password)
            db.update_user(user_id, {'password_hash': hashed_password})
            
            return jsonify({'message': 'Password changed successfully'})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/profile/export', methods=['GET'])
    @jwt_required
    def export_data():
        try:
            user_id = get_current_user_id()
            
            # Get all user data
            user = db.get_user_by_id(user_id)
            private_journals = db.get_user_private_journals(user_id)
            open_journals = db.get_user_open_journals(user_id)
            question_answers = db.get_user_question_answers(user_id)
            
            export_data = {
                'export_date': datetime.now().isoformat(),
                'user_info': {
                    'first_name': user.get('first_name'),
                    'last_name': user.get('last_name'),
                    'email': user.get('email'),
                    'created_at': user.get('created_at')
                },
                'private_journals': private_journals,
                'open_journals': open_journals,
                'question_answers': question_answers
            }
            
            # Create JSON response
            response = make_response(jsonify(export_data))
            response.headers['Content-Disposition'] = 'attachment; filename=soupie-data-export.json'
            response.headers['Content-Type'] = 'application/json'
            
            return response
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/profile/delete', methods=['DELETE'])
    @jwt_required
    def delete_account():
        try:
            user_id = get_current_user_id()
            
            # Delete all user data
            db.delete_user(user_id)
            
            # Clear JWT token
            response = make_response(jsonify({'message': 'Account deleted successfully'}))
            response.set_cookie('jwt_token', '', expires=0)
            
            return response
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Profile insights endpoints
    @app.route('/api/profile/insights', methods=['GET'])
    @jwt_required
    def get_profile_insights():
        try:
            user_id = get_current_user_id()
            
            # Get user's onboarding record
            onboarding_record = db.get_user_onboarding_record(user_id)
            
            if not onboarding_record:
                return jsonify({'error': 'No onboarding data found'}), 404
            
            # Return insights if available
            insights = onboarding_record.get('insights', {})
            
            return jsonify({
                'insights': insights,
                'onboarding_completed': True
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/profile/score', methods=['POST'])
    @jwt_required
    def recalculate_profile_score():
        try:
            user_id = get_current_user_id()
            
            # Get user's onboarding record
            onboarding_record = db.get_user_onboarding_record(user_id)
            
            if not onboarding_record:
                return jsonify({'error': 'No onboarding data found'}), 404
            
            # Extract onboarding data for reprocessing
            onboarding_data = {}
            for tier in ['tier_1_demographics', 'tier_2_emotional_state', 'tier_3_cognitive_themes', 
                        'tier_4_functional_impact', 'tier_5_risk_and_protective_factors']:
                if tier in onboarding_record:
                    tier_data = onboarding_record[tier]
                    if isinstance(tier_data, dict):
                        for key, value in tier_data.items():
                            if isinstance(value, dict):
                                # Handle nested dictionaries
                                for nested_key, nested_value in value.items():
                                    onboarding_data[f"{key}_{nested_key}"] = nested_value
                            else:
                                onboarding_data[key] = value
            
            # Reprocess through scoring engine
            insights = scoring_engine.process_onboarding_data(onboarding_data)
            
            # Update the record with new insights
            onboarding_record['insights'] = insights
            onboarding_record['updated_at'] = datetime.now().isoformat()
            
            # Save updated record
            records = db._read_table("onboarding_records")
            for i, record in enumerate(records):
                if record.get('user_id') == user_id:
                    records[i] = onboarding_record
                    break
            db._write_table("onboarding_records", records)
            
            return jsonify({
                'message': 'Profile score recalculated successfully',
                'insights': insights
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/emergency', methods=['POST'])
    def handle_emergency():
        try:
            data = request.get_json()
            user_id = data.get('user_id')
            emergency_type = data.get('emergency_type', 'suicidal_thoughts')
            
            # Log emergency for tracking
            emergency_record = {
                'user_id': user_id,
                'emergency_type': emergency_type,
                'timestamp': datetime.now().isoformat(),
                'handled': False
            }
            
            # In a real application, this would trigger:
            # - Immediate notification to crisis team
            # - Emergency contact protocols
            # - Resource delivery to user
            
            return jsonify({
                'message': 'Emergency resources have been activated',
                'resources': {
                    'crisis_hotline': '988',
                    'crisis_text': 'Text HOME to 741741',
                    'emergency_services': '911',
                    'immediate_support': 'You are not alone. Help is available 24/7.'
                }
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Page routes
    @app.route('/register')
    def register_page():
        return render_template('register.html')

    @app.route('/login')
    def login_page():
        return render_template('login.html')

    @app.route('/onboarding')
    @jwt_required
    def onboarding_page():
        try:
            user_id = get_current_user_id()
            user = db.get_user_by_id(user_id)
            if not user:
                return redirect('/login')
            
            # Check if user has already completed onboarding
            if user.get('onboarding_done'):
                return redirect('/dashboard')
            
            return render_template('onboarding.html')
        except Exception as e:
            print(f"Onboarding page error: {str(e)}")
            return redirect('/login')

    @app.route('/dashboard')
    @jwt_required
    def dashboard_page():
        try:
            user_id = get_current_user_id()
            print(f"Dashboard access - User ID: {user_id}")
            user = db.get_user_by_id(user_id)
            if not user:
                print("Dashboard - User not found, redirecting to login")
                return redirect('/login')
            print(f"Dashboard - User onboarding_done: {user.get('onboarding_done')}")
            
            return render_template('dashboard.html', 
                                 user_first_name=user.get('first_name', 'User'))
        except Exception as e:
            print(f"Dashboard error: {str(e)}")
            return redirect('/login')

    @app.route('/private-journal')
    @jwt_required
    def private_journal_page():
        try:
            user_id = get_current_user_id()
            user = db.get_user_by_id(user_id)
            return render_template('private-journal.html', user_first_name=user.get('first_name', 'User'))
        except Exception:
            return redirect('/login')

    @app.route('/open-journal')
    @jwt_required
    def open_journal_page():
        try:
            user_id = get_current_user_id()
            user = db.get_user_by_id(user_id)
            return render_template('open-journal.html', user_first_name=user.get('first_name', 'User'))
        except Exception:
            return redirect('/login')

    @app.route('/profile')
    @jwt_required
    def profile_page():
        try:
            user_id = get_current_user_id()
            user = db.get_user_by_id(user_id)
            return render_template('profile.html', user_first_name=user.get('first_name', 'User'))
        except Exception:
            return redirect('/login')

    # AI Chat endpoint
    @app.route('/api/chat', methods=['POST'])
    @jwt_required
    def chat_with_ai():
        try:
            data = request.get_json()
            message = data.get('message', '').strip()
            chat_history = data.get('chat_history', [])
            
            if not message:
                return jsonify({'error': 'Message is required'}), 400
            
            # Get user context
            user_id = get_current_user_id()
            user_context = get_user_context(user_id)
            
            # Get user's emotional state and risk profile
            user_emotional_state = get_user_emotional_state(user_context)
            emergency_mode = detect_emergency_indicators(user_context, chat_history)
            
            # Create improved system prompt with context awareness
            system_prompt = create_ai_system_prompt(user_context, chat_history)
            
            # Combine system prompt with user message and context
            full_prompt = f"{system_prompt}\n\nUser message: {message}"
            
            # Get AI response with fallback
            ai_response = call_gemini(full_prompt)
            
            # Check if AI response is valid, otherwise use fallback
            if not ai_response or ai_response in ["AI service not configured", "AI service error"]:
                ai_response = get_fallback_response(message, user_context, user_emotional_state, emergency_mode)
            
            # Analyze message for feature suggestions
            suggested_features = analyze_message_for_features(message, user_context)
            
            # Generate session insights for logging
            session_insights = generate_session_insights(message, ai_response, user_emotional_state, emergency_mode)
            
            # Log session insights (in production, this would go to a database)
            log_session_insights(user_id, session_insights)
            
            return jsonify({
                'response': ai_response,
                'suggested_features': suggested_features,
                'session_insights': session_insights
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    def get_user_context(user_id):
        """Get user context for better AI responses"""
        try:
            # Get user's journal entries count
            private_journals = db._read_table("private_journals")
            user_private_count = len([j for j in private_journals if j.get('user_id') == user_id])
            
            open_journals = db._read_table("open_journals")
            user_open_count = len([j for j in open_journals if j.get('user_id') == user_id])
            
            # Get recent mood if available
            mood_records = db._read_table("mood_records")
            recent_moods = [m for m in mood_records if m.get('user_id') == user_id]
            recent_mood = recent_moods[-1]['mood'] if recent_moods else None
            
            # Get user insights if available
            user_insights = None
            try:
                insights_response = requests.get(f'http://localhost:5000/api/profile/insights', 
                                               headers={'Authorization': f'Bearer {request.headers.get("Authorization")}'})
                if insights_response.status_code == 200:
                    user_insights = insights_response.json().get('insights')
            except:
                pass
            
            return {
                'private_journal_count': user_private_count,
                'open_journal_count': user_open_count,
                'total_entries': user_private_count + user_open_count,
                'recent_mood': recent_mood,
                'has_insights': user_insights is not None,
                'is_new_user': (user_private_count + user_open_count) == 0
            }
        except Exception as e:
            return {
                'private_journal_count': 0,
                'open_journal_count': 0,
                'total_entries': 0,
                'recent_mood': None,
                'has_insights': False,
                'is_new_user': True
            }

    def create_ai_system_prompt(user_context, chat_history):
        """Create a context-aware system prompt for the AI based on the Talksoup blueprint"""
        
        # Get user's emotional state and risk profile
        user_emotional_state = get_user_emotional_state(user_context)
        emergency_mode = detect_emergency_indicators(user_context, chat_history)
        
        # Base system role
        base_prompt = """You are Talksoup, an emotionally intelligent AI companion designed to help users reflect on their thoughts, track their emotions, and build psychological resilience — without diagnosing or labeling.

You are inspired by CBT (Cognitive Behavioral Therapy), CPT (Cognitive Processing Therapy), and empathic human conversation.

You act as a guide, not a therapist. Your job is to help users feel understood, not fixed.

CORE PRINCIPLES:
- Empathy First: Always prioritize emotional validation before offering any reflection or suggestion
- No Diagnosis: Never use clinical terms like "depression," "anxiety," or "disorder"
- Emotion-Aware: Detect and respond to tone shifts in mood or intent
- Human Safety: If user expresses self-harm or hopelessness, respond with empathy first, then provide helpline resources
- CBT Micro-Coaching: Use short, thought-provoking questions that help users reframe thoughts
- Progressive Reflection: Gradually deepen conversation based on user comfort level"""

        # Add context-specific guidance based on user state
        context_guidance = get_context_guidance(user_context, user_emotional_state, emergency_mode)
        
        # Add conversation memory context
        if chat_history:
            recent_context = "Recent conversation context:\n"
            for msg in chat_history[-3:]:  # Last 3 messages
                role = "User" if msg.get('isUser') else "You"
                recent_context += f"{role}: {msg.get('content', '')}\n"
            context_guidance += f"\n{recent_context}"

        # Add response guidelines based on user's emotional state
        response_guidelines = get_response_guidelines(user_emotional_state, emergency_mode)
        
        # Add conversation flow guidance
        conversation_guidance = get_conversation_flow_guidance(chat_history)
        
        return f"{base_prompt}\n\n{context_guidance}\n\n{response_guidelines}\n\n{conversation_guidance}"

    def get_user_emotional_state(user_context):
        """Analyze user's emotional state based on context"""
        emotional_state = {
            'mood': 'neutral',
            'energy_level': 'medium',
            'stress_level': 'low',
            'support_level': 'medium'
        }
        
        # Analyze based on recent mood data
        if user_context.get('recent_mood'):
            mood = user_context['recent_mood'].lower()
            if mood in ['sad', 'depressed', 'down']:
                emotional_state['mood'] = 'low'
                emotional_state['energy_level'] = 'low'
            elif mood in ['anxious', 'worried', 'stressed']:
                emotional_state['mood'] = 'anxious'
                emotional_state['stress_level'] = 'high'
            elif mood in ['happy', 'excited', 'good']:
                emotional_state['mood'] = 'positive'
                emotional_state['energy_level'] = 'high'
        
        # Analyze based on journaling patterns
        if user_context.get('total_entries', 0) == 0:
            emotional_state['support_level'] = 'low'  # New user needs more support
        
        return emotional_state

    def detect_emergency_indicators(user_context, chat_history):
        """Detect if user is in crisis or needs immediate support"""
        emergency_indicators = [
            'suicide', 'kill myself', 'end it all', 'not worth living',
            'hopeless', 'no point', 'give up', 'can\'t go on',
            'self harm', 'hurt myself', 'cut myself'
        ]
        
        # Check recent messages for emergency indicators
        if chat_history:
            recent_messages = [msg.get('content', '').lower() for msg in chat_history[-5:] if msg.get('isUser')]
            for message in recent_messages:
                if any(indicator in message for indicator in emergency_indicators):
                    return True
        
        return False

    def get_context_guidance(user_context, emotional_state, emergency_mode):
        """Get context-specific guidance based on user state"""
        
        if emergency_mode:
            return """
EMERGENCY MODE ACTIVATED:
- Respond immediately with compassion and safety protocol
- Use phrases like: "I hear how heavy this feels. You don't have to go through this alone."
- Offer helpline resources: "Would you like me to share some free and confidential helplines?"
- Never leave them feeling alone or unsupported
- Focus on immediate safety and connection"""
        
        if user_context['is_new_user']:
            return """
NEW USER GUIDANCE:
- Welcome them warmly and explain your role as a reflection companion
- Use light, gentle tone initially
- Explain how journaling can help with emotional processing
- Suggest starting with simple reflection: "Would you like to explore what's on your mind today?"
- Be encouraging about beginning their wellness journey"""
        
        elif emotional_state['mood'] == 'low':
            return """
LOW MOOD DETECTED:
- Use extra empathy and validation
- Focus on understanding rather than fixing
- Ask gentle questions: "What's been weighing on you lately?"
- Suggest light journaling: "Sometimes writing about difficult feelings can help process them"
- Avoid pushing for positivity"""
        
        elif emotional_state['mood'] == 'anxious':
            return """
ANXIOUS STATE DETECTED:
- Use calming, grounding language
- Help them slow down and breathe
- Ask grounding questions: "What's one thing you can see or hear right now?"
- Suggest gentle reflection: "Would it help to write about what's making you feel anxious?"
- Focus on present moment awareness"""
        
        else:
            return """
BALANCED STATE:
- Use supportive, curious tone
- Encourage deeper reflection
- Ask thought-provoking questions
- Suggest journaling for growth and insight
- Help them explore patterns and connections"""

    def get_response_guidelines(emotional_state, emergency_mode):
        """Get response guidelines based on emotional state"""
        
        if emergency_mode:
            return """
EMERGENCY RESPONSE GUIDELINES:
1. Lead with empathy: "I hear how heavy this feels"
2. Provide immediate safety: "You don't have to go through this alone"
3. Offer resources: "Would you like me to share some helplines?"
4. Never minimize their feelings
5. Focus on connection and safety
6. End with: "I'm really glad you reached out. You're not alone in this." """
        
        elif emotional_state['mood'] == 'low':
            return """
LOW MOOD RESPONSE GUIDELINES:
1. Validate their feelings: "That sounds really hard"
2. Use gentle, understanding tone
3. Ask open questions: "What's been on your mind lately?"
4. Suggest gentle reflection: "Sometimes writing about difficult feelings can help"
5. Avoid pushing for positivity
6. Continue the conversation naturally - only end with reflection questions when the conversation is actually concluding"""
        
        elif emotional_state['mood'] == 'anxious':
            return """
ANXIOUS STATE RESPONSE GUIDELINES:
1. Use calming, grounding language
2. Help them slow down: "Let's take this one step at a time"
3. Ask grounding questions: "What's one thing you can focus on right now?"
4. Suggest gentle reflection: "Would it help to write about what's making you feel anxious?"
5. Focus on present moment awareness
6. Continue the conversation naturally - only end with reflection questions when the conversation is actually concluding"""
        
        else:
            return """
BALANCED STATE RESPONSE GUIDELINES:
1. Use supportive, curious tone
2. Ask thought-provoking questions: "What might you tell a friend feeling this way?"
3. Encourage deeper reflection: "Has this feeling shown up before?"
4. Only suggest journaling if user explicitly wants to process or reflect: "Would you like to explore this further in your journal?"
5. Help identify patterns: "It seems this feeling often shows up after..."
6. Focus on conversation and understanding, not pushing features
7. Continue the conversation naturally - only end with reflection questions when the conversation is actually concluding"""

    def analyze_message_for_features(message, user_context):
        """Analyze user message to suggest appropriate features only when genuinely helpful"""
        message_lower = message.lower()
        suggested_features = []
        
        # Only suggest features when user explicitly indicates they want to process, reflect, or track something
        # Not just because they mention emotions or experiences
        
        # Private journaling - only when user shows intent to process or reflect
        private_journal_indicators = [
            'want to write', 'need to process', 'want to reflect', 'should journal',
            'write about', 'put into words', 'capture this', 'record this',
            'work through', 'figure out', 'understand better', 'make sense of'
        ]
        
        if any(indicator in message_lower for indicator in private_journal_indicators):
            suggested_features.append('private-journal')
        
        # Community journaling - only when user mentions sharing or community
        community_indicators = [
            'share with others', 'community', 'other people', 'connect with',
            'not alone', 'others might', 'help someone', 'relate to'
        ]
        
        if any(indicator in message_lower for indicator in community_indicators):
            suggested_features.append('open-journal')
        
        # Mood tracking - only when user wants to track or monitor
        mood_tracking_indicators = [
            'track my mood', 'monitor my mood', 'log my mood', 'record my mood',
            'mood patterns', 'track feelings', 'mood over time', 'mood changes'
        ]
        
        if any(indicator in message_lower for indicator in mood_tracking_indicators):
            suggested_features.append('mood-tracker')
        
        # Progress/insights - only when user wants to see their data or progress
        progress_indicators = [
            'my progress', 'my data', 'my insights', 'my patterns',
            'how i\'ve been', 'my journey', 'see my growth', 'my stats'
        ]
        
        if any(indicator in message_lower for indicator in progress_indicators):
            suggested_features.append('weekly-progress')
        
        # Tips and advice - only when user asks for help or guidance
        advice_indicators = [
            'help me', 'what should i do', 'how do i', 'advice',
            'tips for', 'guidance', 'what can i do', 'suggestions'
        ]
        
        if any(indicator in message_lower for indicator in advice_indicators):
            suggested_features.append('tips-advice')
        
        return suggested_features

    def get_conversation_flow_guidance(chat_history):
        """Provide guidance on conversation flow and when to use ending phrases"""
        
        # Check if this seems like a conversation ending
        is_conversation_ending = False
        
        if chat_history:
            # Look for ending indicators in recent messages
            recent_messages = [msg.get('content', '').lower() for msg in chat_history[-2:] if msg.get('isUser')]
            
            ending_indicators = [
                'thanks', 'thank you', 'bye', 'goodbye', 'see you', 'talk later',
                'that\'s all', 'nothing else', 'i\'m done', 'that\'s it',
                'gotta go', 'have to go', 'need to go', 'time to go'
            ]
            
            if any(indicator in ' '.join(recent_messages) for indicator in ending_indicators):
                is_conversation_ending = True
        
        if is_conversation_ending:
            return """
CONVERSATION ENDING DETECTED:
- Use reflection questions like "Thanks for sharing that with me — how are you feeling now?"
- Acknowledge the conversation and their openness
- End on a supportive, warm note
- Only use these ending phrases when the conversation is actually concluding"""
        else:
            return """
CONVERSATION CONTINUING:
- Keep responses natural and conversational
- Ask follow-up questions to continue the dialogue
- Avoid ending phrases like "Thanks for sharing that with me — how are you feeling now?"
- Focus on understanding and exploring their thoughts further
- Only use reflection questions when the conversation is actually ending"""

    def get_fallback_response(message, user_context, emotional_state, emergency_mode):
        """Provide sophisticated fallback responses when AI is not available"""
        message_lower = message.lower()
        
        # Emergency mode responses
        if emergency_mode:
            return "I hear how heavy this feels. You don't have to go through this alone. Would you like me to share some free and confidential helplines? You're not alone in this, and I'm really glad you reached out."
        
        # Greeting responses based on emotional state
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
            if user_context['is_new_user']:
                return "Hello! Welcome to Talksoup. I'm here to help you reflect on your thoughts and build emotional resilience. Would you like to explore what's on your mind today?"
            elif emotional_state['mood'] == 'low':
                return "Hello! I can sense you might be going through a tough time. I'm here to listen and help you process whatever you're feeling. How are you doing today?"
            elif emotional_state['mood'] == 'anxious':
                return "Hello! I'm here to help you feel more grounded. Sometimes it helps to slow down and focus on one thing at a time. What's on your mind?"
            else:
                return "Hello! How are you feeling today? I'm here to listen and help you reflect on your experiences."
        
        # Emotional support responses with CBT-style guidance
        elif any(word in message_lower for word in ['sad', 'depressed', 'down', 'upset', 'hurt', 'empty', 'numb']):
            return "That sounds really hard. It's completely human to feel this way sometimes. What's been weighing on you lately? I'm here to listen and help you process whatever you're feeling."
        
        elif any(word in message_lower for word in ['stressed', 'anxious', 'worried', 'overwhelmed', 'panic']):
            return "I can hear how overwhelming this feels. Let's take this one step at a time. What's one thing you can focus on right now? Sometimes it helps to slow down and breathe."
        
        elif any(word in message_lower for word in ['happy', 'excited', 'good', 'great', 'wonderful', 'grateful']):
            return "That's wonderful to hear! I'm so glad you're feeling good. What's making you feel this way? It's great to celebrate positive moments."
        
        # CBT-style reflection prompts
        elif any(word in message_lower for word in ['frustrated', 'angry', 'mad', 'irritated']):
            return "That sounds really frustrating. What's the story your mind tells you when this happens? Sometimes it helps to step back and ask: what might you tell a friend feeling this way?"
        
        elif any(word in message_lower for word in ['lonely', 'isolated', 'alone', 'disconnected']):
            return "That sounds really painful. Feeling disconnected can be exhausting. Do you remember the last time you felt even a small spark of connection? Sometimes writing about these feelings can help us understand them better."
        
        # General responses with progressive reflection
        elif any(word in message_lower for word in ['day', 'today', 'yesterday', 'weekend', 'happened']):
            return "It sounds like you have something to share about your day. What stood out to you most? I'm here to listen and help you process whatever you're experiencing."
        
        elif any(word in message_lower for word in ['help', 'advice', 'what should i do', 'stuck']):
            return "I'm here to help you work through whatever you're facing. What's one thing that might help you feel a little better right now? Sometimes talking through things can help us see them differently."
        
        # Default response with emotional awareness
        else:
            if user_context['is_new_user']:
                return "I'm here to listen and help you on your mental health journey. What's on your mind today? I'm here to support you in whatever way feels right."
            elif emotional_state['mood'] == 'low':
                return "I'm here to listen. Sometimes when we're feeling low, it helps to talk about what's on our mind. What's been weighing on you?"
            elif emotional_state['mood'] == 'anxious':
                return "I'm here to help you feel more grounded. What's on your mind? Sometimes talking through things can help us feel more centered."
            else:
                return "I'm here to listen. What's on your mind? I'm here to support you in whatever way feels helpful."

    def generate_session_insights(message, ai_response, emotional_state, emergency_mode):
        """Generate session insights for logging and analysis"""
        insights = {
            'timestamp': datetime.now().isoformat(),
            'dominant_emotion': detect_dominant_emotion(message),
            'energy_shift': calculate_energy_shift(message, emotional_state),
            'reflective_depth': determine_reflective_depth(message),
            'risk_flag': emergency_mode,
            'summary_text': generate_session_summary(message, ai_response, emotional_state)
        }
        return insights

    def detect_dominant_emotion(message):
        """Detect the dominant emotion in the user's message"""
        message_lower = message.lower()
        
        emotion_keywords = {
            'sadness': ['sad', 'depressed', 'down', 'upset', 'hurt', 'crying', 'tears'],
            'anxiety': ['anxious', 'worried', 'stressed', 'nervous', 'panic', 'overwhelmed'],
            'anger': ['angry', 'mad', 'frustrated', 'irritated', 'annoyed'],
            'joy': ['happy', 'excited', 'good', 'great', 'wonderful', 'amazing'],
            'fear': ['scared', 'afraid', 'terrified', 'fearful'],
            'loneliness': ['lonely', 'alone', 'isolated', 'disconnected'],
            'confusion': ['confused', 'lost', 'unclear', 'unsure']
        }
        
        for emotion, keywords in emotion_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return emotion
        
        return 'neutral'

    def calculate_energy_shift(message, emotional_state):
        """Calculate the energy shift in the user's message"""
        message_lower = message.lower()
        
        high_energy_words = ['excited', 'energetic', 'motivated', 'pumped', 'thrilled']
        low_energy_words = ['tired', 'exhausted', 'drained', 'lethargic', 'sluggish']
        
        if any(word in message_lower for word in high_energy_words):
            return '+15%'
        elif any(word in message_lower for word in low_energy_words):
            return '-15%'
        else:
            return '0%'

    def determine_reflective_depth(message):
        """Determine the reflective depth of the user's message"""
        message_lower = message.lower()
        
        deep_reflection_words = ['understand', 'realize', 'aware', 'insight', 'pattern', 'meaning']
        surface_words = ['fine', 'okay', 'good', 'bad', 'tired']
        
        if any(word in message_lower for word in deep_reflection_words):
            return 'deep'
        elif any(word in message_lower for word in surface_words):
            return 'light'
        else:
            return 'balanced'

    def generate_session_summary(message, ai_response, emotional_state):
        """Generate a summary of the session for logging"""
        dominant_emotion = detect_dominant_emotion(message)
        
        if emotional_state['mood'] == 'low':
            return f"User discussed {dominant_emotion} feelings, showing awareness and seeking support. Provided empathetic response and gentle reflection prompts."
        elif emotional_state['mood'] == 'anxious':
            return f"User expressed {dominant_emotion} concerns, showing need for grounding. Provided calming response and present-moment awareness guidance."
        else:
            return f"User shared {dominant_emotion} experiences, showing openness to reflection. Provided supportive response and encouraged deeper exploration."

    def log_session_insights(user_id, session_insights):
        """Log session insights (in production, this would go to a database)"""
        # For now, just print to console - in production this would be stored in a database
        print(f"Session insights for user {user_id}: {session_insights}")
        
        # In production, you would store this in a database table like:
        # INSERT INTO session_insights (user_id, timestamp, dominant_emotion, energy_shift, reflective_depth, risk_flag, summary_text)
        # VALUES (user_id, session_insights['timestamp'], session_insights['dominant_emotion'], ...)

    def analyze_journal_emotions(journal_entry):
        """Analyze journal entry for emotional patterns and mood indicators"""
        entry_lower = journal_entry.lower()
        
        # Emotional indicators
        emotions = {
            'sadness': ['sad', 'depressed', 'down', 'upset', 'hurt', 'crying', 'tears', 'empty', 'numb'],
            'anxiety': ['anxious', 'worried', 'stressed', 'nervous', 'panic', 'overwhelmed', 'scared'],
            'anger': ['angry', 'mad', 'frustrated', 'irritated', 'annoyed', 'rage'],
            'joy': ['happy', 'excited', 'good', 'great', 'wonderful', 'amazing', 'grateful', 'blessed'],
            'fear': ['scared', 'afraid', 'terrified', 'fearful', 'worried'],
            'loneliness': ['lonely', 'alone', 'isolated', 'disconnected', 'empty'],
            'confusion': ['confused', 'lost', 'unclear', 'unsure', 'mixed up']
        }
        
        detected_emotions = []
        for emotion, keywords in emotions.items():
            if any(keyword in entry_lower for keyword in keywords):
                detected_emotions.append(emotion)
        
        return detected_emotions

    def generate_fallback_soupie_response(journal_content, emotional_analysis):
        """Generate a fallback response when AI service is unavailable"""
        
        # Analyze the emotional content
        emotions = emotional_analysis if emotional_analysis else ['neutral']
        primary_emotion = emotions[0] if emotions else 'neutral'
        
        # Create title based on emotional state
        if primary_emotion == 'sadness':
            title = "**A Day of Reflection and Growth**"
        elif primary_emotion == 'anxiety':
            title = "**Navigating Through Challenges**"
        elif primary_emotion == 'joy':
            title = "**Celebrating Your Positive Energy**"
        elif primary_emotion == 'anger':
            title = "**Processing Strong Emotions**"
        elif primary_emotion == 'loneliness':
            title = "**Finding Connection in Solitude**"
        else:
            title = "**Your Journey of Self-Discovery**"
        
        # Create empathetic response based on emotion
        if primary_emotion == 'sadness':
            paragraph1 = "You've shared something deeply personal, and I can sense the weight of what you're carrying. It takes courage to express difficult emotions, and I want you to know that your feelings are completely valid and understandable."
            paragraph2 = "What strikes me is your willingness to be honest about your experience. This kind of self-awareness, even during challenging times, shows remarkable strength. Remember that it's okay to feel this way, and you don't have to navigate these feelings alone."
            insight = "Acknowledging difficult emotions is the first step toward healing and growth."
        elif primary_emotion == 'anxiety':
            paragraph1 = "I can feel the energy and intensity in what you've written. It sounds like you're dealing with a lot of thoughts and concerns that are weighing on your mind. Your willingness to process these feelings shows real self-awareness."
            paragraph2 = "Anxiety often comes from caring deeply about things that matter to you. The fact that you're taking time to reflect on these feelings shows you're already taking positive steps toward managing them."
            insight = "Taking time to process anxious thoughts helps create mental clarity and reduces overwhelm."
        elif primary_emotion == 'joy':
            paragraph1 = "What a wonderful energy you're sharing! I can feel the positivity and enthusiasm radiating from your words. It's beautiful to see you celebrating the good moments and recognizing what brings you happiness."
            paragraph2 = "Your ability to notice and appreciate positive experiences shows a healthy mindset. These moments of joy are precious, and it's wonderful that you're taking time to acknowledge and savor them."
            insight = "Celebrating positive moments helps build resilience and creates lasting happiness."
        elif primary_emotion == 'anger':
            paragraph1 = "I can sense the intensity of what you're feeling, and I want you to know that your emotions are completely valid. Anger often comes from a place of caring deeply about something important to you."
            paragraph2 = "The fact that you're taking time to process these feelings shows emotional intelligence. Anger can be a powerful signal that something needs attention or change in your life."
            insight = "Processing anger constructively can lead to positive change and personal growth."
        elif primary_emotion == 'loneliness':
            paragraph1 = "I can feel the weight of isolation in your words, and I want you to know that you're not alone in feeling this way. Loneliness is one of the most human experiences, and sharing it takes courage."
            paragraph2 = "Your willingness to express these feelings shows self-awareness and strength. Sometimes the bravest thing we can do is acknowledge when we need connection and support."
            insight = "Reaching out and sharing feelings of loneliness is the first step toward building meaningful connections."
        else:
            paragraph1 = "Thank you for sharing your thoughts and experiences with me. I can sense the depth of reflection in your words, and it's clear you're taking time to process what's happening in your life."
            paragraph2 = "Your willingness to engage in this kind of self-reflection shows emotional intelligence and self-awareness. These are valuable qualities that will serve you well in your personal growth journey."
            insight = "Regular self-reflection builds emotional intelligence and personal understanding."
        
        return f"""{title}

{paragraph1}

{paragraph2}

**Key Insight:** {insight}"""

    # Mood tracking endpoints
    @app.route('/api/mood/track', methods=['POST'])
    @jwt_required
    def track_mood():
        try:
            data = request.get_json()
            mood = data.get('mood')
            notes = data.get('notes', '')
            
            if not mood:
                return jsonify({'error': 'Mood is required'}), 400
            
            user_id = get_current_user_id()
            
            # Create mood record
            mood_record = {
                'id': str(uuid.uuid4()),
                'user_id': user_id,
                'mood': mood,
                'notes': notes,
                'created_at': datetime.now().isoformat()
            }
            
            # Save to database
            mood_records = db._read_table("mood_records")
            mood_records.append(mood_record)
            db._write_table("mood_records", mood_records)
            
            return jsonify({
                'message': 'Mood tracked successfully',
                'mood_record': mood_record
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/mood/history', methods=['GET'])
    @jwt_required
    def get_mood_history():
        try:
            user_id = get_current_user_id()
            days = request.args.get('days', 7, type=int)
            
            # Get user's mood records
            all_mood_records = db._read_table("mood_records")
            user_mood_records = [record for record in all_mood_records if record.get('user_id') == user_id]
            
            # Sort by date (newest first)
            user_mood_records.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            # Limit to requested days
            if days > 0:
                user_mood_records = user_mood_records[:days]
            
            return jsonify({
                'mood_records': user_mood_records,
                'total_records': len(user_mood_records)
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/mood/weekly-report', methods=['GET'])
    @jwt_required
    def get_weekly_mood_report():
        try:
            user_id = get_current_user_id()
            
            # Get last 7 days of mood records
            all_mood_records = db._read_table("mood_records")
            user_mood_records = [record for record in all_mood_records if record.get('user_id') == user_id]
            
            # Filter to last 7 days
            from datetime import datetime, timedelta
            week_ago = datetime.now() - timedelta(days=7)
            recent_records = []
            
            for record in user_mood_records:
                record_date = datetime.fromisoformat(record.get('created_at', ''))
                if record_date >= week_ago:
                    recent_records.append(record)
            
            # Calculate mood statistics
            mood_counts = {}
            for record in recent_records:
                mood = record.get('mood', 'unknown')
                mood_counts[mood] = mood_counts.get(mood, 0) + 1
            
            # Find most common mood
            most_common_mood = max(mood_counts.items(), key=lambda x: x[1]) if mood_counts else ('none', 0)
            
            # Calculate average mood score (if we had numeric values)
            mood_scores = {
                'excellent': 5,
                'good': 4,
                'okay': 3,
                'poor': 2,
                'terrible': 1
            }
            
            total_score = 0
            valid_records = 0
            for record in recent_records:
                mood = record.get('mood', '')
                if mood in mood_scores:
                    total_score += mood_scores[mood]
                    valid_records += 1
            
            average_score = total_score / valid_records if valid_records > 0 else 0
            
            return jsonify({
                'weekly_summary': {
                    'total_entries': len(recent_records),
                    'most_common_mood': most_common_mood[0],
                    'mood_frequency': most_common_mood[1],
                    'average_mood_score': round(average_score, 2),
                    'mood_distribution': mood_counts
                },
                'recent_records': recent_records
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Test Gemini integration
    @app.route('/api/test/gemini', methods=['POST'])
    def test_gemini():
        try:
            data = request.get_json()
            prompt = data.get('prompt', 'Hello, how are you?')
            
            result = call_gemini(prompt)
            
            return jsonify({
                'status': 'success',
                'prompt': prompt,
                'response': result,
                'gemini_configured': os.getenv('GEMINI_API_KEY') is not None
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e),
                'gemini_configured': os.getenv('GEMINI_API_KEY') is not None
            }), 500

    if __name__ == '__main__':
        print("Starting Talksoup development server...")
        print("Server will be available at: http://localhost:5000")
        print("Auto-reload enabled for development")
        print("Press Ctrl+C to stop the server")
        print("-" * 50)
        
        app.run(debug=True, host='0.0.0.0', port=5000)

except Exception as e:
    print(f"Error starting server: {e}")
    print("This might be due to Python 3.14 compatibility issues.")
    print("Try using Python 3.11 or 3.12 instead.")
    sys.exit(1)
