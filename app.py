#!/usr/bin/env python3
"""
MCQ Generator - Web Application
"""

import streamlit as st
import requests
import os
import re
import tempfile
import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
import google.generativeai as genai
import fitz
import textract
import chardet
from pathlib import Path

# Configuration
SECRET_KEY = "your-super-secret-key-here"
DATABASE_URL = "sqlite:///./simple_mcq.db"

# Initialize database
def init_db():
    conn = sqlite3.connect('simple_mcq.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, email TEXT UNIQUE, 
                  hashed_password TEXT, api_key TEXT, 
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# User management
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed

def create_user(email, password, api_key):
    conn = sqlite3.connect('simple_mcq.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (email, hashed_password, api_key) VALUES (?, ?, ?)',
                 (email, hash_password(password), api_key))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(email, password):
    conn = sqlite3.connect('simple_mcq.db')
    c = conn.cursor()
    c.execute('SELECT hashed_password, api_key FROM users WHERE email = ?', (email,))
    result = c.fetchone()
    conn.close()
    
    if result and verify_password(password, result[0]):
        return result[1]  # Return API key
    return None

# Text extraction
def extract_text(file_path, page_range=None):
    try:
        # Try PDF extraction first
        try:
            with fitz.open(file_path) as doc:
                if page_range:
                    start_page = max(0, page_range[0] - 1)
                    end_page = min(len(doc), page_range[1])
                    text = " ".join(doc[page].get_text() for page in range(start_page, end_page))
                else:
                    text = " ".join(page.get_text() for page in doc)
                if text and text.strip():
                    return text
        except Exception:
            pass

        # Fallback to textract
        raw_data = textract.process(str(file_path))
        detected = chardet.detect(raw_data)
        text = raw_data.decode(detected['encoding'] if detected['encoding'] else 'utf-8', errors='replace')
        return text.strip()
    except Exception as e:
        raise ValueError(f"Text extraction failed: {str(e)}")

# MCQ generation
def generate_mcqs(text, num_questions, difficulty, api_key):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        diff_instructions = {
            'easy': "Ask basic, clear questions. Keep language simple.",
            'medium': "Ask questions requiring interpretation. Options should be plausible.",
            'hard': "Ask deep, thought-provoking questions using nuanced options."
        }
        
        prompt = f"""Generate {num_questions} spiritual MCQs from this text.
For each MCQ, use this format exactly:
Q1. [Question]
a) Option 1
b) Option 2
c) Option 3
d) Option 4
Answer: [Correct letter]

Instructions:
- Focus on spiritual concepts and ideas from the text.
- {diff_instructions.get(difficulty, '')}
- Make sure to use this format for every question.

Text: {text[:30000]}"""  # Limit text length

        response = model.generate_content(prompt)
        return format_mcqs(response.text)
    except Exception as e:
        raise ValueError(f"AI generation failed: {str(e)}")

def format_mcqs(raw_text):
    text = raw_text.replace('\\n', '\n')
    pattern = re.compile(
        r'Q\d+\.\s*(.*?)\n'
        r'a\)\s*(.*?)\n'
        r'b\)\s*(.*?)\n'
        r'c\)\s*(.*?)\n'
        r'd\)\s*(.*?)\n'
        r'Answer:\s*([A-Da-d])',
        re.DOTALL
    )
    
    matches = pattern.findall(text)
    formatted_mcqs = []
    for idx, (question, a, b, c, d, answer) in enumerate(matches, 1):
        formatted = [
            f"Q{idx}. {question.strip()}",
            f"a) {a.strip()}",
            f"b) {b.strip()}",
            f"c) {c.strip()}",
            f"d) {d.strip()}",
            f"Answer: {answer.upper()}",
            "-" * 50
        ]
        formatted_mcqs.append("\n".join(formatted))
    
    if not formatted_mcqs:
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
    
    return "\n\n".join(formatted_mcqs)

# Streamlit app
def main():
    st.set_page_config(
        page_title="MCQ Generator",
        page_icon="🧘",
        layout="wide"
    )
    
    # Initialize database
    init_db()
    
    # Session state
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "api_key" not in st.session_state:
        st.session_state.api_key = None
    
    st.title("🧘 Spiritual MCQ Generator")
    st.markdown("Generate Multiple Choice Questions from your documents using AI")
    
    # Authentication
    if not st.session_state.logged_in:
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            with st.form("login"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    api_key = verify_user(email, password)
                    if api_key:
                        st.session_state.logged_in = True
                        st.session_state.api_key = api_key
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid email or password")
        
        with tab2:
            with st.form("register"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                api_key = st.text_input("Gemini API Key", type="password", 
                                      help="Get your free API key from https://makersuite.google.com/app/apikey")
                if st.form_submit_button("Register"):
                    if create_user(email, password, api_key):
                        st.success("Registration successful! Please login.")
                    else:
                        st.error("Email already registered")
    
    else:
        # Main interface
        st.success(f"Welcome! You are logged in.")
        
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.api_key = None
            st.rerun()
        
        st.markdown("---")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload Document (PDF, DOC, DOCX, PPT, PPTX, TXT)",
            type=["pdf", "txt", "doc", "docx", "ppt", "pptx"]
        )
        
        # Settings
        col1, col2, col3 = st.columns(3)
        with col1:
            num_questions = st.slider("Number of Questions", 1, 50, 10)
        with col2:
            difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"])
        with col3:
            col3a, col3b = st.columns(2)
            with col3a:
                start_page = st.number_input("Start Page", min_value=1, value=1)
            with col3b:
                end_page = st.number_input("End Page", min_value=1, value=1)
        
        # Generate MCQs
        if uploaded_file and st.button("Generate MCQs", type="primary"):
            with st.spinner("Processing document and generating MCQs..."):
                try:
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name
                    
                    # Extract text
                    page_range = (start_page, end_page) if start_page and end_page else None
                    text = extract_text(tmp_path, page_range)
                    
                    if not text.strip():
                        st.error("No text could be extracted from the file")
                        return
                    
                    # Generate MCQs
                    mcqs = generate_mcqs(text, num_questions, difficulty, st.session_state.api_key)
                    
                    # Display results
                    st.success("MCQs Generated Successfully!")
                    
                    # Download button
                    st.download_button(
                        label="Download MCQs",
                        data=mcqs,
                        file_name=f"mcqs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
                    
                    # Display MCQs
                    st.markdown("### Generated MCQs:")
                    st.text_area("MCQs", mcqs, height=400)
                    
                    # Cleanup
                    os.unlink(tmp_path)
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    if "API key" in str(e):
                        st.info("Please check your Gemini API key in the registration")
        
        # Instructions
        with st.expander("ℹ️ How to use"):
            st.markdown("""
            1. **Register** with your email and Gemini API key
            2. **Get API Key**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey) for free API key
            3. **Upload Document**: PDF, DOC, DOCX, PPT, PPTX, or TXT files
            4. **Configure Settings**: Choose number of questions and difficulty
            5. **Generate**: Click the button to create MCQs
            6. **Download**: Save the generated MCQs as a text file
            """)

if __name__ == "__main__":
    main() 
