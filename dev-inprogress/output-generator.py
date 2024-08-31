import json
import xml.etree.ElementTree as ET
from xml.dom import minidom

def generate_json_output(structured_data):
    return json.dumps(structured_data, indent=2)

def generate_xml_output(structured_data):
    root = ET.Element("document")
    
    entities = ET.SubElement(root, "entities")
    for entity in structured_data["entities"]:
        ent = ET.SubElement(entities, "entity")
        ET.SubElement(ent, "text").text = entity["text"]
        ET.SubElement(ent, "label").text = entity["label"]
    
    sentences = ET.SubElement(root, "sentences")
    for sentence in structured_data["sentences"]:
        ET.SubElement(sentences, "sentence").text = sentence
    
    keywords = ET.SubElement(root, "keywords")
    for keyword in structured_data["keywords"]:
        ET.SubElement(keywords, "keyword").text = keyword
    
    xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    return xml_str

def generate_machine_readable_output(structured_data, output_format="json"):
    if output_format == "json":
        return generate_json_output(structured_data)
    elif output_format == "xml":
        return generate_xml_output(structured_data)
    else:
        raise ValueError(f"Unsupported output format: {output_format}")
