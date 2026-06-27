from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from pathlib import Path
import json
import uuid
import re

import db
from resume_utils import extract_text_from_file, extract_skills
from llm_utils import call_llm, build_interviewer_question_prompt
from rag_utils import (
    chunk_text,
    build_faiss_index,
    save_index,
    load_index,
    retrieve
)
import auth_utils

# ---------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------

app = FastAPI(title="AI Interview Simulator with RAG")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # OK for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# In-memory session store (fine for demo / academic use)
SESSIONS: dict[str, dict] = {}

# ---------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------

class QuestionRequest(BaseModel):
    session_id: str

class AnswerRequest(BaseModel):
    session_id: str
    question: str
    answer: str

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# ---------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------

@app.on_event("startup")
def on_startup():
    db.init_db()
    print("FastAPI application started and Database initialized")

# ---------------------------------------------------------------------
# Authentication Endpoints
# ---------------------------------------------------------------------

@app.post("/api/auth/register")
async def register(user: UserRegister):
    hashed_pw = auth_utils.get_password_hash(user.password)
    success = db.create_user(user.username, user.email, hashed_pw)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )
    return {"message": "User registered successfully"}

@app.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.get_user_by_username(form_data.username)
    if not user or not auth_utils.verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_utils.create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me")
async def read_users_me(current_user: dict = Depends(auth_utils.get_current_user)):
    return {"username": current_user["username"], "email": current_user["email"]}

# ---------------------------------------------------------------------
# Resume Upload + RAG Indexing
# ---------------------------------------------------------------------

@app.post("/upload_resume")
async def upload_resume(
    file: UploadFile = File(...),
    current_user: dict = Depends(auth_utils.get_current_user)
):
    session_id = str(uuid.uuid4())

    resume_path = UPLOAD_DIR / f"{session_id}_{file.filename}"
    with open(resume_path, "wb") as f:
        f.write(await file.read())

    resume_text = extract_text_from_file(resume_path)
    skills = extract_skills(resume_text)

    # ---------------- RAG PIPELINE ----------------
    chunks = chunk_text(resume_text)

    if not chunks:
        raise HTTPException(status_code=400, detail="Could not extract text from resume")

    index, _ = build_faiss_index(chunks)

    rag_path = UPLOAD_DIR / session_id
    rag_path.mkdir(exist_ok=True)

    save_index(index, chunks, rag_path)
    # ---------------------------------------------

    # Save to Database for persistence
    db.save_session(
        session_id=session_id,
        user_id=current_user["id"],
        resume_text=resume_text,
        skills=skills,
        rag_path=str(rag_path),
        history=[]
    )

    # Keep in memory for fast access (optional)
    SESSIONS[session_id] = {
        "resume_text": resume_text,
        "skills": skills,
        "rag_path": str(rag_path),
        "questions": [],
        "history": []
    }

    return {
        "session_id": session_id,
        "filename": file.filename,
        "skills": skills[:20],
        "message": "Resume uploaded and indexed successfully."
    }

# ---------------------------------------------------------------------
# Generate Next Question (RAG-Aware)
# ---------------------------------------------------------------------

@app.post("/next_question")
async def next_question(
    req: QuestionRequest,
    current_user: dict = Depends(auth_utils.get_current_user)
):
    # Try cache then database
    session = SESSIONS.get(req.session_id)
    if not session:
        db_session = db.get_session_details(req.session_id)
        if not db_session or db_session["user_id"] != current_user["id"]:
            raise HTTPException(status_code=404, detail="Session not found or access denied")
        
        # Hydrate cache
        session = {
            "resume_text": db_session["resume_text"],
            "skills": db_session["skills"],
            "rag_path": db_session["rag_path"],
            "questions": [], # We don't track questions in DB specifically, but history has them
            "history": db_session["history"]
        }
        SESSIONS[req.session_id] = session

    index, chunks = load_index(Path(session["rag_path"]))
    skills = session["skills"]

    retrieval_query = "Interview questions for skills: " + ", ".join(skills[:10])
    context_chunks = retrieve(retrieval_query, index, chunks, top_k=5)

    context = "\n---\n".join(context_chunks)

    prompt = build_interviewer_question_prompt(
        full_resume=session["resume_text"],
        deep_dive_context=context,
        skills=skills,
        history=session["history"]
    )

    question = call_llm(prompt)

    # -------- SAFETY FALLBACK --------
    if not question or not question.strip():
        question = (
            "Can you explain one project from your resume and "
            "the technologies you used in it?"
        )
    # ---------------------------------

    if "questions" not in session: session["questions"] = []
    session["questions"].append(question)

    return {"question": question}

def parse_llm_json(raw: str) -> dict:
    """
    Robustly parse JSON from LLM response.
    Handles conversational filler, markdown blocks, and literal newlines.
    """
    # 1. Clean up markdown and common minor issues
    text = raw.replace("```json", "").replace("```", "").strip()
    
    # Remove trailing commas in objects (e.g. {"a": 1,})
    text = re.sub(r',\s*}', '}', text)
    
    # 2. Extract block between { and }
    start_idx = text.find("{")
    end_idx = text.rfind("}")
    
    if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
        return {
            "score": extract_regex_score(raw),
            "feedback": extract_regex_feedback(raw) or raw
        }

    json_str = text[start_idx:end_idx+1]
    
    try:
        # Try standard parse
        return json.loads(json_str)
    except json.JSONDecodeError:
        # 3. Fallback to regex extraction if JSON is malformed
        return {
            "score": extract_regex_score(json_str) or extract_regex_score(raw),
            "feedback": extract_regex_feedback(json_str) or raw
        }

def extract_regex_score(text: str) -> int:
    """
    Exhaustively search for a numerical score in LLM text.
    """
    # 1. High-confidence JSON-like patterns
    patterns = [
        r'["\']?score["\']?\s*(?::|=|is)\s*["\']?(\d+)["\']?',
        r'["\']?(?:grade|rating|mark|points)["\']?\s*(?::|=|is)\s*["\']?(\d+)["\']?',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))

    # 2. Look for "7/10" format anywhere
    match = re.search(r'(\d+)\s*/\s*10', text)
    if match:
        return int(match.group(1))

    # 3. Looser proximity search: "grade ... 8" or "score ... 9"
    # Look for keyword, then some characters, then a number 0-10
    match = re.search(r'(?:score|grade|rating|mark|points).{0,30}?\b([0-9]|10)\b', text, re.IGNORECASE | re.DOTALL)
    if match:
        return int(match.group(1))
    
    # 4. Last resort: if the response is very short (e.g. "7"), just take the first number
    if len(text.strip()) < 15:
        match = re.search(r'(\d+)', text)
        if match:
            return int(match.group(1))
            
    return 0

def extract_regex_feedback(text: str) -> str:
    # Use re.DOTALL to match across newlines inside the feedback string
    match = re.search(r'"feedback":\s*"(.*?)"', text, re.DOTALL)
    if not match:
        match = re.search(r'feedback:\s*"(.*?)"', text, re.DOTALL | re.IGNORECASE)
    if match:
        # Clean up literal newlines for display
        return match.group(1).replace("\n", " ").strip()
    return ""

# ---------------------------------------------------------------------
# Submit Answer + RAG-Based Evaluation
# ---------------------------------------------------------------------

@app.post("/submit_answer")
async def submit_answer(
    req: AnswerRequest,
    current_user: dict = Depends(auth_utils.get_current_user)
):
    session = SESSIONS.get(req.session_id)
    if not session:
        db_session = db.get_session_details(req.session_id)
        if not db_session or db_session["user_id"] != current_user["id"]:
            raise HTTPException(status_code=404, detail="Session not found")
        session = {
            "resume_text": db_session["resume_text"],
            "skills": db_session["skills"],
            "rag_path": db_session["rag_path"],
            "history": db_session["history"]
        }
        SESSIONS[req.session_id] = session

    if not req.question or not req.answer:
        raise HTTPException(status_code=400, detail="Question and answer are required")

    index, chunks = load_index(Path(session["rag_path"]))

    retrieval_query = f"{req.question} {req.answer}"
    context_chunks = retrieve(retrieval_query, index, chunks, top_k=5)

    context = "\n---\n".join(context_chunks)

    prompt = f"""
You are a strict technical interviewer.

Question:
{req.question}

Candidate Answer:
{req.answer}

Relevant resume/context:
{context}

Evaluate the answer based on:
- Technical correctness
- Depth
- Clarity
- Practical relevance

Return JSON ONLY:
{{
  "score": <integer 1-10>,
  "feedback": "<clear, concise feedback>"
}}
"""

    raw = call_llm(prompt)

    parsed = parse_llm_json(raw)
    score = int(parsed.get("score", 0))
    feedback = parsed.get("feedback", raw)

    # Update history for next question
    if "history" not in session: session["history"] = []
    session["history"].append({"role": "interviewer", "content": req.question})
    session["history"].append({"role": "candidate", "content": req.answer})

    # Sync to DB
    db.save_answer(
        session_id=req.session_id,
        question=req.question,
        answer=req.answer,
        score=score,
        feedback=feedback
    )

    return {
        "score": score,
        "feedback": feedback
    }

@app.get("/api/history")
async def get_history(current_user: dict = Depends(auth_utils.get_current_user)):
    return db.get_user_sessions(current_user["id"])

# ---------------------------------------------------------------------
# Session Summary
# ---------------------------------------------------------------------

@app.get("/session_summary")
async def session_summary(session_id: str):
    answers = db.get_session_summary(session_id)

    avg_score = (
        sum(a["score"] for a in answers) / len(answers)
        if answers else 0
    )

    return {
        "session_id": session_id,
        "average_score": round(avg_score, 2),
        "answers": answers
    }
