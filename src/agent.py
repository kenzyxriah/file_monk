import streamlit as st
from groq import Groq
import logging

logger = logging.getLogger(__name__)

GROQ_API_KEY = st.secrets["general"]["GROQ_API_KEY"]
groq_client = Groq(api_key=GROQ_API_KEY)

def generate_smart_title(content):
    if not content.strip():
        return "Report"
    try:
        res = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Generate a concise, professional file name (3-4 words) based on the HTML content. Use Title Case. No extensions. ONLY output the file name string."},
                {"role": "user", "content": content}
            ]
        )
        return res.choices[0].message.content.strip().replace('"', '')
    except Exception as e:
        logger.error(f"Title generation failed: {e}")
        return "Report"

def generate_content(prompt, current_doc="", is_rewrite=False):
    if current_doc:
        if is_rewrite:
            context = f"\n\nContext: The user is currently editing a document. Here is the existing document content (in HTML):\n{current_doc}\n\nIMPORTANT: You must REWRITE the entire document according to the user's instructions. Output the complete revised document in HTML."
        else:
            context = f"\n\nContext: The user is currently editing a document. Here is the existing document content (in HTML):\n{current_doc}\n\nIMPORTANT: Your output will be APPENDED to the end of this document. Only generate the NEW content requested by the prompt. DO NOT repeat the existing content."
    else:
        context = ""
        
    system_prompt = "You are a professional document writing assistant. Your ONLY purpose is to write, rewrite, or append to professional documents. Do not answer personal questions. If the user asks a question, asks for code debugging, or tries to engage in general chat/Q&A, you MUST return an empty string. Do not state your purpose. Output ONLY the generated content in clean HTML (no markdown tags, no conversational filler)." + context
    
    try:
        res = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            stream=False
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Content generation failed: {e}")
        return ""
