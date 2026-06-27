# Adaptive-Interview-Evaluation-Using-LLM-and-RAG

## Overview

The **Adaptive Interview Evaluation System** (or Smart Resume Ranker) is an end-to-end intelligent recruitment and interview preparation framework. It processes candidate resumes, extracts technical and soft skills, and generates highly personalized, domain-specific interview questions.

Unlike traditional cloud-based platforms, this system operates entirely on local machines using locally deployed Large Language Models (LLMs) via Ollama. By integrating a Retrieval-Augmented Generation (RAG) architecture with semantic similarity modeling, the system provides secure, offline, and highly accurate interview simulations while completely protecting user data privacy.

## Key Features

**Intelligent Resume Parsing:** Automatically extracts text from PDF and DOCX formats using `pdfplumber` and `python-docx`.

**Advanced Skill Extraction:** Utilizes `spaCy`'s Named Entity Recognition (NER) combined with a custom domain-specific skill dictionary to categorize programming languages, frameworks, databases, and soft skills.

**Contextual Candidate Ranking:** Converts resume content into semantic representations using MiniLM sentence embeddings and ranks candidates against job descriptions using cosine similarity.

**Adaptive Question Generation:** Uses a FAISS-based RAG framework to retrieve relevant technical knowledge, allowing local LLMs to generate adaptive conceptual, scenario-based, and behavioral questions.

**Automated Answer Evaluation:** Assesses candidate responses using a rubric-based scoring framework that grades technical correctness, completeness, relevance, and communication clarity.

**Performance Analytics:** Tracks user progress across multiple interview sessions, storing session metadata and evaluation feedback in SQLite and Redis databases.

**Privacy-First & Offline:** Runs entirely locally without transmitting sensitive candidate information to external cloud APIs.


## System Architecture

The system follows a sequential and modular pipeline:

**1. FastAPI Controller Layer:** Handles `/upload_resume`, `/next_question`, and `/submit_answer` endpoints for seamless user interaction.


**2. Core Processing Pipeline:** Parses documents, extracts skills, and chunks text into semantic embeddings.


**3. Knowledge Retrieval (RAG):** Uses `FAISS` to fetch contextual knowledge based on the candidate's skill profile.


**4. Local LLM Integration:** Processes the retrieved context alongside candidate data through locally running models (like Llama3:8B) to generate questions and evaluate answers.


## Tech Stack

**Backend & API**

* Python 


* FastAPI 



**Natural Language Processing & Machine Learning**

* `spaCy` (Resume parsing and skill extraction) 

* `Sentence Transformers` (MiniLM semantic embeddings) 

* `Scikit-learn` (TF-IDF vectorization and cosine similarity computation) 

* `Pandas` & `NumPy` (Data structuring and numerical operations) 


**Vector Database & RAG**

* `FAISS` (Facebook AI Similarity Search for RAG context retrieval) 


**Local LLMs**

* `Ollama` (Local deployment for models like Llama3:8B, Phi3:Mini, and Gemma2:2B) 


**Database Management**

* SQLite (Persistent storage for scoring and feedback) 


* Redis (In-memory temporary session data management) 


## Getting Started

### Prerequisites

* Python 3.8+
* [Ollama](https://ollama.com/) installed on your local machine.

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/ai-interview-simulator.git
cd ai-interview-simulator

```


2. **Install Python dependencies:**
```bash
pip install -r requirements.txt

```


3. **Download the required spaCy model:**
```bash
python -m spacy download en_core_web_sm

```


4. **Pull Local LLM via Ollama:**


(The project demonstrated best results with Llama3:8B )


```bash
ollama run llama3

```


5. **Run the FastAPI Application:**
```bash
uvicorn main:app --reload

```



## Experimental Results & Performance

During testing, **Llama3:8B** achieved the highest performance in skill classification (approx. 50% accuracy, 74% recall, and 66% F1-score) and demonstrated the strongest semantic alignment for question generation. The integration of TF-IDF and MiniLM successfully improved candidate ranking precision over traditional keyword-based screening methods.

## Contributors

**Deepanshu Mohanty** 

**Karthick Raja MK** 
 
**V Dakshin Aditya** 

**Supervised by:** Dr. E. Ganesh, Rajalakshmi Institute of Technology.
