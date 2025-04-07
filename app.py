import streamlit as st
from bs4 import BeautifulSoup
import requests
from huggingface_hub import InferenceClient
from urllib.parse import urlparse
from datetime import datetime
from collections import defaultdict
import os
import re


from extracter import (
    parse_user_input,
    get_relevant_feeds,
    process_articles,
    generate_newsletter_md,
    save_newsletter_to_file
)
import datetime

# Set page config
st.set_page_config(
    page_title="AI Newsletter Generator",
    page_icon="📰",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS for better appearance
st.markdown("""
<style>
    .stTextInput input {
        font-size: 18px;
    }
    .stButton button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        width: 100%;
    }
    .stButton button:hover {
        background-color: #45a049;
    }
    .newsletter-preview {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 1rem;
        margin-top: 1rem;
        background-color: #f9f9f9;
    }
    .section-header {
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.3rem;
    }
</style>
""", unsafe_allow_html=True)

# App header
st.title("📰 AI-Powered Personalized Newsletter Generator")
st.markdown("Create custom news digests tailored to your profession, interests, and location.")

# Sidebar with instructions and examples
with st.sidebar:
    st.header("Instructions")
    st.markdown("""
    1. Enter your details in the format:  
       `Name(Profession/Interest, Age, Country)`  
    2. Example inputs:  
       - `Alex Parker(Software Engineer, 35, India)`  
       - `Maria Chen(Environmental Science, 28, Canada)`  
       - `John Smith(Football, 42, UK)`  
    3. Click "Generate Newsletter"  
    4. View and download your personalized newsletter
    """)
    st.markdown("---")
    st.markdown("**How it works:**")
    st.markdown("- AI selects relevant news sources based on your profile")
    st.markdown("- Extracts and summarizes articles using NLP")
    st.markdown("- Combines professional and local news")
    st.markdown("---")
    st.markdown(f"© {datetime.datetime.now().year} AI Newsletter Generator")

# Main content area
col1, col2 = st.columns([3, 1])
with col1:
    user_input = st.text_input(
        "Enter your details:",
        placeholder="Alex Parker(Software Engineer, 35, India)",
        help="Format: Name(Profession/Interest, Age, Country)"
    )

generate_btn = st.button("✨ Generate Newsletter")

if generate_btn and user_input:
    try:
        with st.spinner("Analyzing your profile..."):
            user = parse_user_input(user_input)
            
        st.success(f"Profile loaded: {user['name']}, {user['profession']}, {user['age']}, {user['country'].capitalize()}")
        
        with st.spinner("Finding the best news sources for you..."):
            profession_feed, country_feed = get_relevant_feeds(user)
            
        with st.spinner("Fetching and processing articles (this may take a minute)..."):
            profession_articles, country_articles = process_articles(profession_feed, country_feed)
            
        if profession_articles or country_articles:
            with st.spinner("Generating your personalized newsletter..."):
                newsletter = generate_newsletter_md(user, profession_articles, country_articles)
                
            st.subheader("Your Personalized Newsletter")
            st.markdown("---")
            
            # Display newsletter preview
            with st.expander("📄 View Full Newsletter", expanded=True):
                st.markdown(newsletter, unsafe_allow_html=True)
            
            # Download button
            filename = f"{user['name'].replace(' ', '_')}_Newsletter.md"
            st.download_button(
                label="⬇️ Download Newsletter",
                data=newsletter,
                file_name=filename,
                mime="text/markdown"
            )
            
            st.success("Newsletter generated successfully!")
        else:
            st.error("Could not fetch any articles. Please try again later.")
            
    except ValueError as e:
        st.error(f"Invalid input format: {e}")
        st.info("Please use the format: Name(Profession/Interest, Age, Country)")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
elif generate_btn:
    st.warning("Please enter your details in the input field above.")

# Footer
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #777;">
        <p>AI Newsletter Generator | Powered by Hugging Face & BeautifulSoup</p>
    </div>
""", unsafe_allow_html=True)