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
from api.models import get_db, create_tables
from api.auth import hash_password, verify_password, create_jwt_token, jwt_required, get_current_user_id

app = Flask(__name__, template_folder='../templates', static_folder='../static')
CORS(app)

# Initialize database tables
create_tables()

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
        else:
            return f"AI service error: HTTP {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"AI service error: {str(e)}"

# Health check endpoint
@app.route('/api/health')
def health_check():
    return jsonify({"status": "healthy", "message": "Talksoup API is running"})

# Authentication endpoints
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
        
        if not email and not phone:
            return jsonify({'error': 'Either email or phone is required'}), 400
        
        # Check if user already exists
        db_instance = get_db()
        existing_user = None
        if email:
            existing_user = db_instance.get_user_by_email(email)
        elif phone:
            # Check by phone if no email
            users = db_instance._read_table("user_registration")
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
        
        user_id = db_instance.create_user(user_data)
        
        # Create JWT token
        token = create_jwt_token(user_id, email or phone)
        
        # Return token in response body for localStorage
        return jsonify({
            'message': 'User registered successfully',
            'user_id': user_id,
            'onboarding_done': False,
            'token': token
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find user by email
        db_instance = get_db()
        user = db_instance.get_user_by_email(email)
        
        if not user or not verify_password(password, user.get('password_hash')):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Create JWT token
        token = create_jwt_token(user.get('id'), user.get('email'))
        
        # Return token in response body for localStorage
        return jsonify({
            'message': 'Login successful',
            'user_id': user.get('id'),
            'onboarding_done': user.get('onboarding_done', False),
            'token': token
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

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

# Onboarding endpoints
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
        questions_answers = data.get('questions_answers', [])
        
        user_id = get_current_user_id()
        db_instance = get_db()
        
        # Save Q&A pairs
        for qa in questions_answers:
            db_instance.create_question_answer(
                user_id=user_id,
                question=qa.get('question'),
                answer=qa.get('answer')
            )
        
        # Mark onboarding as done
        db_instance.update_user(user_id, {'onboarding_done': True})
        
        return jsonify({'message': 'Onboarding completed successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Private Journal endpoints
@app.route('/api/journal/private', methods=['POST'])
@jwt_required
def create_private_journal():
    try:
        data = request.get_json()
        content = data.get('content')
        
        if not content:
            return jsonify({'error': 'Content is required'}), 400
        
        user_id = get_current_user_id()
        db_instance = get_db()
        
        entry_id = db_instance.create_private_journal(
            user_id=user_id,
            content=content
        )
        
        return jsonify({
            'message': 'Journal entry created successfully',
            'entry_id': entry_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/journal/private', methods=['GET'])
@jwt_required
def get_private_journals():
    try:
        user_id = get_current_user_id()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        db_instance = get_db()
        all_journals = db_instance.get_user_private_journals(user_id)
        
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
    finally:
        db.close()

@app.route('/api/journal/private/<journal_id>/summarize', methods=['POST'])
@jwt_required
def summarize_private_journal(journal_id):
    try:
        user_id = get_current_user_id()
        db = next(get_db())
        
        journal = db.query(PrivateJournal).filter(
            PrivateJournal.id == journal_id,
            PrivateJournal.user_id == user_id
        ).first()
        
        if not journal:
            return jsonify({'error': 'Journal entry not found'}), 404
        
        # Generate AI summary with human-like, empathetic tone
        prompt = f"""You are a caring friend reading someone's personal journal entry. Respond naturally and empathetically, as if you're a trusted confidant who truly understands and cares.

Journal entry: "{journal.content}"

Write a warm, human response that:
- Acknowledges their feelings without judgment
- Shows genuine understanding and empathy
- Offers gentle, practical support
- Uses natural, conversational language
- Avoids clinical or AI-like phrasing
- Feels like advice from a wise, caring friend

Keep it brief (2-3 sentences) and focus on being supportive and understanding."""
        summary = call_gemini(prompt)
        
        journal.ai_summary = summary
        db.commit()
        
        return jsonify({
            'message': 'Summary generated successfully',
            'summary': summary
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

# Open Journal endpoints
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
        db_instance = get_db()
        
        entry_id = db_instance.create_open_journal(
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
    finally:
        db.close()

@app.route('/api/journal/open', methods=['GET'])
def get_open_journals():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        db_instance = get_db()
        all_journals = db_instance.get_all_open_journals()
        
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
    finally:
        db.close()

# Open Journal reaction and flagging endpoints
@app.route('/api/journal/open/<journal_id>/react', methods=['POST'])
def react_to_open_journal(journal_id):
    try:
        data = request.get_json()
        reaction_type = data.get('reaction_type')
        
        if not reaction_type:
            return jsonify({'error': 'Reaction type is required'}), 400
        
        # For now, just return success - reactions can be implemented later
        return jsonify({'message': 'Reaction added successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/journal/open/<journal_id>/flag', methods=['POST'])
def flag_open_journal(journal_id):
    try:
        # For now, just return success - flagging can be implemented later
        return jsonify({'message': 'Post flagged for moderation'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Dashboard endpoint
@app.route('/api/dashboard', methods=['GET'])
@jwt_required
def get_dashboard():
    try:
        user_id = get_current_user_id()
        db = next(get_db())
        
        # Get user info
        user = db.query(UserRegistration).filter(UserRegistration.id == user_id).first()
        
        # Get journal counts
        private_count = db.query(PrivateJournal).filter(PrivateJournal.user_id == user_id).count()
        open_count = db.query(OpenJournal).filter(OpenJournal.user_id == user_id).count()
        
        # Get recent activity
        recent_private = db.query(PrivateJournal).filter(
            PrivateJournal.user_id == user_id
        ).order_by(PrivateJournal.created_at.desc()).limit(3).all()
        
        return jsonify({
            'user': {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'onboarding_done': user.onboarding_done
            },
            'stats': {
                'private_journals': private_count,
                'open_journals': open_count,
                'total_journals': private_count + open_count
            },
            'recent_activity': [{
                'id': str(journal.id),
                'content': journal.content[:100] + '...' if len(journal.content) > 100 else journal.content,
                'created_at': journal.created_at.isoformat()
            } for journal in recent_private]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

# Serve static files and templates
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/onboarding')
def onboarding_page():
    return render_template('onboarding.html')

@app.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html')

@app.route('/private-journal')
def private_journal_page():
    return render_template('private-journal.html')

@app.route('/open-journal')
def open_journal_page():
    return render_template('open-journal.html')

if __name__ == '__main__':
    app.run(debug=True)
