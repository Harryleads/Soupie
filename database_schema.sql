-- Talksoup Database Schema
-- Run this SQL in your NeonDB PostgreSQL database

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- User registration table
CREATE TABLE user_registration (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE,
    phone TEXT UNIQUE,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    onboarding_done BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Onboarding questions and answers
CREATE TABLE question_answer (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES user_registration(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Private journal entries
CREATE TABLE private_journal (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES user_registration(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    ai_summary TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Open journal entries (anonymous community posts)
CREATE TABLE open_journal (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES user_registration(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    emotion_tag TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Create indexes for better performance
CREATE INDEX idx_user_registration_email ON user_registration(email);
CREATE INDEX idx_user_registration_phone ON user_registration(phone);
CREATE INDEX idx_question_answer_user_id ON question_answer(user_id);
CREATE INDEX idx_private_journal_user_id ON private_journal(user_id);
CREATE INDEX idx_private_journal_created_at ON private_journal(created_at DESC);
CREATE INDEX idx_open_journal_created_at ON open_journal(created_at DESC);
CREATE INDEX idx_open_journal_emotion_tag ON open_journal(emotion_tag);
