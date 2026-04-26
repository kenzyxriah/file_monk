# File Monk 📁

**File Monk** is a premium, AI-powered workspace designed to streamline document workflows. Whether you need to draft professional reports, annotate PDFs with custom signatures, or convert between complex file formats, File Monk provides a seamless, glassmorphic experience.

## ✨ Features

- **📝 AI Creator**: Draft professional documents instantly with an integrated AI assistant (powered by Llama 3.3). Export directly to PDF or DOCX.
- **🖌️ PDF Annotator**: Draw, highlight, and transform your documents. Add stamps, signatures, or passports with a single click and export the enhanced PDF.
- **🔄 Format Converter**: High-fidelity conversion between PDF, DOCX, PPTX, and all major image formats.
- **🚀 Premium UI**: A modern, dark-mode glassmorphic interface designed for clarity and speed.

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **Document Processing**: PyMuPDF (fitz), Pillow (PIL), python-docx
- **AI Engine**: Groq (Llama 3.3 70B)
- **Styling**: Vanilla CSS (Glassmorphism)

## 🏗️ Getting Started

### Prerequisites
- Python 3.10+
- Streamlit

### Installation
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your `.streamlit/secrets.toml` with:
   - `GROQ_API_KEY`
   - Authentication endpoints and credentials.

### Running the App
```bash
streamlit run app.py
```

---
Made with Love from **Qahhar**
