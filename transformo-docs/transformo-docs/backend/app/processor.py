import spacy
import re
from collections import Counter
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom

nlp = spacy.load("en_core_web_sm")

def clean_text(text):
    text = ''.join(char for char in text if char.isprintable())
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return text

def structure_text(text):
    doc = nlp(text)
    
    structured_data = {
        "entities": [],
        "sentences": [],
        "keywords": [],
        "word_count": len(doc),
        "sentence_count": len(list(doc.sents)),
    }
    
    for ent in doc.ents:
        structured_data["entities"].append({
            "text": clean_text(ent.text),
            "label": ent.label_
        })
    
    for sent in doc.sents:
        structured_data["sentences"].append(clean_text(sent.text))
    
    keywords = [clean_text(chunk.root.lemma_) for chunk in doc.noun_chunks]
    structured_data["keywords"] = list(set(keywords))
    
    return structured_data

def apply_template(data, template):
    if template == "data_only":
        return {
            "entities": data["entities"],
            "keywords": data["keywords"]
        }
    elif template == "analytics_only":
        return {
            "word_count": data["word_count"],
            "sentence_count": data["sentence_count"],
            "entity_count": len(data["entities"]),
            "keyword_count": len(data["keywords"])
        }
    elif template == "specific_entities":
        return {
            "persons": [ent["text"] for ent in data["entities"] if ent["label"] == "PERSON"],
            "organizations": [ent["text"] for ent in data["entities"] if ent["label"] == "ORG"],
            "locations": [ent["text"] for ent in data["entities"] if ent["label"] in ["GPE", "LOC"]]
        }
    else:
        return data

def extract_custom_fields(structured_data, fields):
    result = {}
    for field in fields:
        if field == "persons":
            result[field] = [ent["text"] for ent in structured_data["entities"] if ent["label"] == "PERSON"]
        elif field == "organizations":
            result[field] = [ent["text"] for ent in structured_data["entities"] if ent["label"] == "ORG"]
        elif field == "locations":
            result[field] = [ent["text"] for ent in structured_data["entities"] if ent["label"] in ["GPE", "LOC"]]
        elif field == "dates":
            result[field] = [ent["text"] for ent in structured_data["entities"] if ent["label"] == "DATE"]
    return result

def analyze_document(structured_data, full_text):
    analytics = {
        "word_count": structured_data["word_count"],
        "sentence_count": structured_data["sentence_count"],
        "average_sentence_length": round(structured_data["word_count"] / structured_data["sentence_count"], 2) if structured_data["sentence_count"] > 0 else 0,
        "entity_count": len(structured_data["entities"]),
        "keyword_count": len(structured_data["keywords"]),
    }
    
    doc = nlp(full_text)
    analytics["most_common_entities"] = Counter([ent["label"] for ent in structured_data["entities"]]).most_common(5)
    analytics["most_common_words"] = Counter([token.text.lower() for token in doc if not token.is_stop and token.is_alpha]).most_common(10)
    
    return analytics

def generate_json_output(data):
    return json.dumps(data, indent=2, ensure_ascii=False)

def generate_xml_output(data):
    def dict_to_xml(tag, d):
        elem = ET.Element(tag)
        for key, val in d.items():
            child = ET.Element(key)
            if isinstance(val, dict):
                child = dict_to_xml(key, val)
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, dict):
                        child.append(dict_to_xml('item', item))
                    else:
                        ET.SubElement(child, 'item').text = str(item)
            else:
                child.text = str(val)
            elem.append(child)
        return elem

    root = dict_to_xml('document', data)
    xml_str = minidom.parseString(ET.tostring(root, encoding='unicode')).toprettyxml(indent="  ")
    return xml_str

def process_document(extracted_text, template=None, custom_fields=None):
    warnings = []
    
    # Always process the full structured data
    full_structured_data = structure_text(extracted_text)
    full_analytics = analyze_document(full_structured_data, extracted_text)
    
    # Apply template or custom fields if specified
    if template:
        output_data = apply_template(full_structured_data, template)
    elif custom_fields:
        output_data = extract_custom_fields(full_structured_data, custom_fields)
    else:
        output_data = full_structured_data
    
    # Always include analytics in the output
    output_data['analytics'] = full_analytics
    
    # Check for null or zero values in the output data
    for key, value in output_data.items():
        if value in (None, 0, [], {}):
            warnings.append(f"Warning: {key} has no value or is empty.")
    
    json_output = generate_json_output(output_data)
    xml_output = generate_xml_output(output_data)
    
    return {
        "structured_data": output_data,
        "analytics": full_analytics,
        "json_output": json_output,
        "xml_output": xml_output,
        "extracted_text": extracted_text,
        "warnings": warnings
    }

def ask_question_to_document(question, document_text):
    # Placeholder for LLM functionality
    return "Sorry, LLM disabled at the moment for prototype."