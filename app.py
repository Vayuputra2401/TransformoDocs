import streamlit as st
import mimetypes
import pandas as pd
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re
from collections import Counter
import io

# Set page config
st.set_page_config(page_title="Transformo-Docs", layout="wide")

# Try to import optional dependencies
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

import subprocess
import sys
import spacy


# Load spaCy model if available, otherwise download and load it
@st.cache_resource
def load_nlp_model():
    try:
        # Try to load the spaCy model
        return spacy.load("en_core_web_sm")
    except OSError:  # Model not found
        # Download the model
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
        # Load the model after downloading
        return spacy.load("en_core_web_sm")

# Use the loaded model
nlp = load_nlp_model()

#from transformers import pipeline

# # Load a smaller LLM, like GPT-2 or GPT-J
# @st.cache_resource
# def load_llm_model():
#     return pipeline("text-generation", model="gpt2")  # You can use a different model if needed

#llm_model = load_llm_model()

def ask_question_to_document(question, document_text):
    prompt = f"Document: {document_text}\n\nQuestion: {question}\nAnswer:"
    
    # # Use the LLM to generate a response
    # response = llm_model(prompt, max_length=600, num_return_sequences=1)
    # return response[0]['generated_text'].split("Answer:")[1].strip()
    response = "Sorry , LLM disabled at the moment for prototype."
    return response




def validate_document(file):
    file_type, _ = mimetypes.guess_type(file.name)
    
    allowed_types = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                     'text/plain', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
    
    if file_type not in allowed_types:
        raise ValueError(f"Unsupported file type: {file_type}")
        
    return file_type

def extract_text(file, file_type):
    if file_type == 'application/pdf':
        if PDF_AVAILABLE:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        else:
            raise ImportError("PyPDF2 is not installed. Cannot process PDF files.")
    elif file_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
        if DOCX_AVAILABLE:
            doc = Document(file)
            return ' '.join([paragraph.text for paragraph in doc.paragraphs])
        else:
            raise ImportError("python-docx is not installed. Cannot process DOCX files.")
    elif file_type == 'text/plain':
        return file.getvalue().decode('utf-8')
    elif file_type in ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
        df = pd.read_excel(file)
        return df.to_json()
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

def clean_text(text):
    text = ''.join(char for char in text if char.isprintable())
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return text

def structure_text(text):
    if SPACY_AVAILABLE and nlp:
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
    else:
        # Fallback to basic text analysis if spaCy is not available
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        
        structured_data = {
            "entities": [],
            "sentences": [clean_text(sent) for sent in sentences if sent.strip()],
            "keywords": [],
            "word_count": len(words),
            "sentence_count": len(sentences),
        }
    
    return structured_data

def analyze_document(structured_data, full_text):
    analytics = {
        "word_count": structured_data["word_count"],
        "sentence_count": structured_data["sentence_count"],
        "average_sentence_length": round(structured_data["word_count"] / structured_data["sentence_count"], 2) if structured_data["sentence_count"] > 0 else 0,
        "entity_count": len(structured_data["entities"]),
        "keyword_count": len(structured_data["keywords"]),
    }
    
    if SPACY_AVAILABLE and nlp:
        doc = nlp(full_text)
        analytics["most_common_entities"] = Counter([ent["label"] for ent in structured_data["entities"]]).most_common(5)
        analytics["most_common_words"] = Counter([token.text.lower() for token in doc if not token.is_stop and token.is_alpha]).most_common(10)
    else:
        # Fallback to basic word frequency if spaCy is not available
        words = [word.lower() for word in re.findall(r'\w+', full_text)]
        analytics["most_common_words"] = Counter(words).most_common(10)
    
    return analytics

def generate_json_output(structured_data, analytics):
    output = {
        "structured_data": structured_data,
        "analytics": analytics
    }
    return json.dumps(output, indent=2, ensure_ascii=False)

def generate_xml_output(structured_data, analytics):
    root = ET.Element("document")
    
    struct_data = ET.SubElement(root, "structured_data")
    
    entities = ET.SubElement(struct_data, "entities")
    for entity in structured_data["entities"]:
        ent = ET.SubElement(entities, "entity")
        ET.SubElement(ent, "text").text = entity["text"]
        ET.SubElement(ent, "label").text = entity["label"]
    
    sentences = ET.SubElement(struct_data, "sentences")
    for sentence in structured_data["sentences"]:
        ET.SubElement(sentences, "sentence").text = sentence
    
    keywords = ET.SubElement(struct_data, "keywords")
    for keyword in structured_data["keywords"]:
        ET.SubElement(keywords, "keyword").text = keyword
    
    analytics_elem = ET.SubElement(root, "analytics")
    for key, value in analytics.items():
        if isinstance(value, list):
            list_elem = ET.SubElement(analytics_elem, key)
            for item in value:
                if isinstance(item, tuple):
                    item_elem = ET.SubElement(list_elem, "item")
                    ET.SubElement(item_elem, "name").text = str(item[0])
                    ET.SubElement(item_elem, "value").text = str(item[1])
                else:
                    ET.SubElement(list_elem, "item").text = str(item)
        else:
            ET.SubElement(analytics_elem, key).text = str(value)
    
    xml_str = minidom.parseString(ET.tostring(root, encoding='unicode')).toprettyxml(indent="  ")
    return xml_str

def process_document(file):
    try:
        file_type = validate_document(file)
        extracted_text = extract_text(file, file_type)
        structured_data = structure_text(extracted_text)
        analytics = analyze_document(structured_data, extracted_text)
        json_output = generate_json_output(structured_data, analytics)
        xml_output = generate_xml_output(structured_data, analytics)
        
        return {
            "structured_data": structured_data,
            "analytics": analytics,
            "json_output": json_output,
            "xml_output": xml_output,
            "extracted_text": extracted_text
        }
    except Exception as e:
        return {"error": str(e)}

def main():
    
    st.title("📄 Transformo Docs")

    st.write("""
        ### 🚀 Transformo Docs: Empowering Document Management

    Transformo Docs is a powerful solution designed to tackle the challenge of non-machine-readable documents like PDFs and Word files. 🌐 This app automates the conversion of such documents into machine-readable formats, making them searchable, accessible, and ready for AI integration. 🤖

    Whether you’re working with scanned documents or files generated through software, Transformo Docs ensures your data is always organized and easily accessible. 📊 Unlock the potential of automation, advanced analytics, and compliance with Transformo Docs—streamline your document management and boost productivity. 📈
    """)


    if not SPACY_AVAILABLE:
        st.warning("spaCy is not installed. Some advanced text analysis features will be limited.")
    if not DOCX_AVAILABLE:
        st.warning("python-docx is not installed. DOCX file processing will not be available.")
    if not PDF_AVAILABLE:
        st.warning("PyPDF2 is not installed. PDF file processing will not be available.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📤 Upload Document")
        uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx", "txt", "xlsx"])

    result = None
    if uploaded_file is not None:
        with st.spinner("Processing document..."):
            result = process_document(uploaded_file)

        if "error" in result:
            st.error(f"Error: {result['error']}")
        else:
            st.success("Document processed successfully!")
            
    with col2:
        st.subheader("💾 Export Options")
        export_format = st.selectbox("Choose export format", ["JSON", "XML"])
        
        if result:
            if export_format == "JSON":
                download_content = result['json_output']
                file_extension = "json"
            else:
                download_content = result['xml_output']
                file_extension = "xml"

            download_filename = f"{uploaded_file.name}_processed.{file_extension}"
            st.download_button(
                label=f"Download {export_format} File",
                data=download_content,
                file_name=download_filename,
                mime=f"application/{file_extension}"
            )

            with st.expander("View Processed Output"):
                st.code(download_content, language=file_extension.lower())

    if result and "error" not in result:
        st.subheader("📊 Document Analytics")
        col3, col4 = st.columns(2)

        with col3:
            st.markdown("### 📏 Basic Metrics")
            st.write(f"**Word Count:** {result['analytics']['word_count']}")
            st.write(f"**Sentence Count:** {result['analytics']['sentence_count']}")
            st.write(f"**Average Sentence Length:** {result['analytics']['average_sentence_length']:.2f} words")

            if SPACY_AVAILABLE:
                st.markdown("### 🏷️ Named Entities")
                st.write(f"**Entity Count:** {result['analytics']['entity_count']}")
                st.write("**Most Common Entities:**")
                for entity, count in result['analytics']['most_common_entities']:
                    st.write(f"- {entity}: {count}")

        with col4:
            if SPACY_AVAILABLE:
                st.markdown("### 🔑 Keywords")
                st.write(f"**Keyword Count:** {result['analytics']['keyword_count']}")

            st.markdown("### 📊 Word Frequency")
            st.write("**Most Common Words:**")
            for word, count in result['analytics']['most_common_words']:
                st.write(f"- {word}: {count}")

        with st.expander("📝 Document Preview"):
            preview_text = result['extracted_text'][:500] + "..." if len(result['extracted_text']) > 500 else result['extracted_text']
            st.text_area("First 500 characters", preview_text, height=200)
    
    # Display chat interface
    st.subheader("💬 Chat with Your Document")

    # Initialize session state to store chat history
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # Input box for user queries
    user_query = st.text_input("Ask a question about the document:")

    # Check if there is a user query and process it
    if user_query:
        document_text = result["extracted_text"]
        answer = ask_question_to_document(user_query, document_text)
        
        # Append the user query and the generated answer to the chat history
        st.session_state["chat_history"].append({"question": user_query, "answer": answer})

    # Display the chat history
    if st.session_state["chat_history"]:
        st.write("### 🗨️ Chat History")
        for chat in st.session_state["chat_history"]:
            st.markdown(f"**You:** {chat['question']}")
            st.markdown(f"**Transformo Docs:** {chat['answer']}")

    # Option to clear chat history
    if st.button("Clear Chat History"):
        st.session_state["chat_history"] = []
    

if __name__ == "__main__":
    main()