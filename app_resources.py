import streamlit as st
from google import genai


@st.cache_resource
def get_gemini_client(api_key: str) -> genai.Client:
    """Reuse an API client per key without caching prompts or responses."""
    return genai.Client(api_key=api_key)
