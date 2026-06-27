import spacy

nlp = spacy.load("en_core_web_sm")
ruler = nlp.add_pipe("entity_ruler", before="ner")

# Improved patterns using token attributes
patterns = [
    # Case-insensitive matches for single words
    {"label": "SKILL", "pattern": [{"LOWER": "python"}], "id": "Python"},
    {"label": "SKILL", "pattern": [{"LOWER": "java"}], "id": "Java"},
    {"label": "SKILL", "pattern": [{"LOWER": "react"}], "id": "React"},
    
    # Handling specific abbreviations with boundaries (using POS/context or just exact lower)
    {"label": "SKILL", "pattern": [{"LOWER": "aws"}], "id": "AWS"},
    
    # Multi-token patterns
    {"label": "SKILL", "pattern": [{"LOWER": "machine"}, {"LOWER": "learning"}], "id": "Machine Learning"},
    {"label": "SKILL", "pattern": [{"LOWER": "deep"}, {"LOWER": "learning"}], "id": "Deep Learning"},
    
    # Handling "C" (difficult because it's a single letter)
    {"label": "SKILL", "pattern": [{"TEXT": "C", "IS_UPPER": True, "IS_PUNCT": False, "IS_SPACE": False}], "id": "C"},
    {"label": "SKILL", "pattern": [{"LOWER": "c++"}], "id": "C++"},
    {"label": "SKILL", "pattern": [{"LOWER": "c#"}], "id": "C#"},
]

ruler.add_patterns(patterns)

test_text = "I am a Python developer who knows C and Machine Learning. I use AWS and C++."
doc = nlp(test_text)

for ent in doc.ents:
    print(f"Text: {ent.text}, Label: {ent.label_}, ID: {ent.ent_id_}")
