import streamlit as st
from src.ui import apply_premium_theme

apply_premium_theme(is_home=True)

st.markdown("""
<style>
    .hero-title {
        font-size: 4rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -1px;
    }

    .hero-subtitle {
        font-size: 1.5rem;
        font-weight: 300;
        color: #a0aec0;
        margin-bottom: 2.5rem;
        max-width: 600px;
        line-height: 1.4;
    }

    .feature-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 1.5rem 1.5rem;
        transition: all 0.3s ease;
        text-align: left;
        position: relative;
        overflow: hidden;
        height: 100%;
        margin-bottom: 1rem;
    }

    .feature-card:hover {
        transform: translateY(-10px);
        background: rgba(255, 255, 255, 0.08);
        border-color: rgba(255, 255, 255, 0.2);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
    }

    /* Subtle glow effect on hover */
    .feature-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.05), transparent);
        transition: left 0.5s ease;
    }
    .feature-card:hover::before {
        left: 100%;
    }

    .card-icon {
        font-size: 2rem;
        margin-bottom: 1.5rem;
    }

    .card-title {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: #ffffff;
    }

    .card-text {
        font-size: 1rem;
        color: #8a94a6;
        line-height: 1.5;
        margin-bottom: 1.5rem;
    }
    
    /* Hide Streamlit page_link native styling to wrap our cards */
    div[data-testid="stPageLink"] a {
        text-decoration: none !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero-title">File Monk</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">The ultimate AI-powered workspace to create, annotate, and convert documents flawlessly.</div>', unsafe_allow_html=True)

# Feature Cards using Streamlit columns
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("""
    <div class="feature-card">
        <div class="card-icon">📝</div>
        <div class="card-title">AI Creator</div>
        <div class="card-text">Draft professional documents instantly with an integrated AI assistant. Export seamlessly to PDF or DOCX.</div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/creator.py", label="Open Creator →")

with c2:
    st.markdown("""
    <div class="feature-card">
        <div class="card-icon">🔄</div>
        <div class="card-title">Format Converter</div>
        <div class="card-text">Instantly convert PDFs to Word, images to PDF, or PPTX files flawlessly with our advanced engine.</div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/converter.py", label="Open Converter →")

with c3:
    st.markdown("""
    <div class="feature-card">
        <div class="card-icon">🖌️</div>
        <div class="card-title">PDF Annotator</div>
        <div class="card-text">Draw, highlight, and transform your documents interactively. Save your annotations directly to a new PDF.</div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/annotator.py", label="Open Annotator →")

st.markdown("""
<div style='margin-top: 3rem; padding-bottom: 1rem; font-size: 0.9rem; color: #4a5568; letter-spacing: 1px; font-weight: 300;'>
    Made with Love from <span style='color: #4facfe; font-weight: 600;'>Qahhar</span>
</div>
""", unsafe_allow_html=True)
