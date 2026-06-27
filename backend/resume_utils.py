# backend/resume_utils.py
from pathlib import Path
import pdfplumber
import docx
from llm_utils import extract_skills_from_text

def extract_text_from_file(file_path: Path) -> str:
    """
    Extracts plain text from PDF, DOCX, or text files.
    """
    if file_path.suffix.lower() == ".pdf":
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"
        return text
    elif file_path.suffix.lower() in [".docx", ".doc"]:
        doc = docx.Document(str(file_path))
        return "\n".join(p.text for p in doc.paragraphs)
    else:
        return file_path.read_text(encoding="utf-8", errors="ignore")

def extract_skills(text: str) -> list[str]:
    """
    Extracts skills by passing the resume text to the LLM.
    This was the original method preferred by the user.
    """
    try:
        return extract_skills_from_text(text)
    except Exception as e:
        print(f"LLM skill extraction failed: {e}")
        # Final fallback: return empty list or could do simple regex if needed
        return []
