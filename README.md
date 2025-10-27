# Soupie - AI-Powered Mental Health Companion

A web application that helps users reflect, journal, and understand emotional patterns through natural conversation and guided self-insight.

## Features

- **Secure Authentication**: JWT-based login with bcrypt password hashing
- **Onboarding Flow**: Personalized questionnaire for new users
- **Private Journal**: Personal reflection entries with AI summaries
- **Open Journal Space**: Anonymous community posts with empathy reactions
- **AI Insights**: Powered by Gemini API for emotional pattern analysis
- **Dashboard**: Personalized overview of mental health journey

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: NeonDB (PostgreSQL)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **AI**: Google Gemini API
- **Deployment**: Vercel

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `env.example` to `.env` and fill in your environment variables
4. Set up your NeonDB database with the provided SQL schema
5. Deploy to Vercel or run locally with `python api/app.py`

## Environment Variables

- `DATABASE_URL`: Your NeonDB PostgreSQL connection string
- `JWT_SECRET`: Secret key for JWT token signing
- `SECRET_KEY`: Flask secret key
- `GEMINI_API_KEY`: Google Gemini API key (see AI Setup below)
- `FLASK_ENV`: Set to 'production' for deployment

## AI Features Setup

Soupie includes several AI-powered features that require a Google Gemini API key:

### Getting a Gemini API Key
1. Visit [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click "Get API Key" → "Create API Key"
4. Copy the generated key to your `.env` file

### AI Features
- **Journal Summarization**: AI-generated summaries of private journal entries
- **Mental Health Insights**: Personalized assessments and recommendations  
- **Emotional Pattern Analysis**: AI analysis of user's emotional patterns
- **Supportive Recommendations**: AI-generated wellness suggestions

### Testing AI Features
Run the test script to verify your AI setup:
```bash
python test_ai.py
```

For detailed setup instructions, see `setup_gemini_api.md`.

## Database Schema

See the SQL schema in the project documentation for table structures.
