import spacy
from resume_utils import extract_skills

test_text = """
Experienced software engineer with skills in Python, React, and AWS. 
Knowledge of machine learning, NLP, and Docker. 
Familiar with Javascript, TypeScript, and SQL databases like PostgreSQL.
Also worked with Git, Jenkins, and Agile methodologies.
"""

skills = extract_skills(test_text)
print(f"Extracted skills: {skills}")
