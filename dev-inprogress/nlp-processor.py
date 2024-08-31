import spacy
import re

nlp = spacy.load("en_core_web_sm")

def structure_text(text):
    doc = nlp(text)
    
    structured_data = {
        "entities": [],
        "sentences": [],
        "keywords": []
    }
    
    # Extract entities
    for ent in doc.ents:
        structured_data["entities"].append({
            "text": ent.text,
            "label": ent.label_
        })
    
    # Extract sentences
    for sent in doc.sents:
        structured_data["sentences"].append(sent.text)
    
    # Extract keywords (simple approach using noun chunks)
    keywords = [chunk.text for chunk in doc.noun_chunks]
    structured_data["keywords"] = list(set(keywords))  # Remove duplicates
    
    return structured_data

def clean_text(text):
    # Remove special characters and extra whitespace
    cleaned_text = re.sub(r'[^\w\s]', '', text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    return cleaned_text

def process_text(text):
    cleaned_text = clean_text(text)
    return structure_text(cleaned_text)
