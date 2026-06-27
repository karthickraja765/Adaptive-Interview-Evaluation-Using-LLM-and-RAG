# backend/llm_utils.py
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3:8b"

def call_llm(prompt: str) -> str:
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
    r = requests.post(OLLAMA_URL, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    return data.get("response", "").strip()

def build_interviewer_question_prompt(full_resume: str, deep_dive_context: str, skills: list[str], history: list[dict]) -> str:
    """
    Builds a context-rich prompt for a Senior Technical Interviewer.
    full_resume: The entire text of the candidate's resume (for identity/general context).
    deep_dive_context: Specific relevant chunks retrieved via RAG (for technical depth).
    history: list of {"role": "interviewer"|"candidate", "content": str}
    """
    history_str = ""
    if history:
        history_str = "\n".join([f"{h['role'].capitalize()}: {h['content']}" for h in history[-6:]])
    
    skills_str = ", ".join(skills)
    
    return f"""
You are a seasoned Senior Technical Interviewer at a top-tier tech company. 
Your goal is to conduct a professional, engaging, and rigorous interview.

### CANDIDATE IDENTITY & BACKGROUND:
(Use this to identify the candidate's name and overall experience level)
{full_resume[:2000]} 

### TECHNICAL DEEP-DIVE CONTEXT (RAG):
(Use this for specific technical follow-up details)
{deep_dive_context}

### INTERVIEW HISTORY (Most Recent):
{history_str if history_str else "No conversation yet. This is the start of the interview."}

### YOUR TASK:
1. Identify the candidate's name and primary background from the 'CANDIDATE IDENTITY' section.
2. Based on the candidate's skills and previous answers (if any), generate ONE conversational but challenging interview question.
3. If there are previous answers, briefly acknowledge or follow up on them before asking the next question.
4. Use the 'TECHNICAL DEEP-DIVE CONTEXT' to ask about specific projects or technologies in detail.
5. Keep the tone professional, insightful, and natural.

Return ONLY your conversational response (no labels like 'Interviewer:', no numbering).
"""

def build_grading_prompt(question: str, answer: str, resume_text: str) -> str:
    return f"""
You are an interviewer evaluating a candidate's answer.

Question:
{question}

Candidate's answer:
{answer}

Relevant resume/context:
{resume_text}

Evaluate the answer on a 1–10 scale using these criteria:
1. Relevance
2. Technical depth
3. Clarity of explanation
4. Structure and organisation
5. Practical examples

Return your response in this JSON format (no extra text):

{{
  "score": <integer 1-10>,
  "feedback": "<2-4 sentence clear feedback>"
}}
"""

def extract_skills_from_text(resume_text: str) -> list[str]:
    """
    Uses the LLM to identify technical skills from the resume text.
    """
    prompt = f"""
Identify all technical professional skills (programming languages, frameworks, databases, tools, cloud services, and methodologies) mentioned in the resume text below.

RESUME TEXT:
{resume_text[:4000]}

Your response must be ONLY a comma-separated list of skills (e.g. Python, React, AWS, SQL). 
Do NOT include any introduction, explanations, or labels.
Skills:
"""
    response = call_llm(prompt)
    
    if not response:
        return []
    
    # Split by comma and clean up
    skills = [s.strip() for s in response.split(",") if s.strip()]
    
    # Filter out common filler or failed response text
    filtered = []
    for s in skills:
        if len(s) < 20 and not s.lower().startswith("here are"):
            filtered.append(s)
            
    return sorted(list(set(filtered)))
