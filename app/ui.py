import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from extractor import validate_document, extract_text
from processor import process_document, ask_question_to_document
from database import save_to_database, get_saved_documents, delete_document
from datetime import datetime
import json
from PIL import Image
import io
import os

# Function to calculate file sizes
def calculate_file_sizes(uploaded_file, result):
    original_size_mb = uploaded_file.size / (1024 * 1024)
    extracted_size_mb = len(json.dumps(result['json_output'])) / (1024 * 1024)
    return original_size_mb, extracted_size_mb

# Function to load and display the logo
def load_logo():
    global logo_path
    logo_path = os.path.join("assets", "logo-white.png")
    print(logo_path)
    if os.path.exists(logo_path):
        return Image.open(logo_path)
    return None

# Main page setup function
def setup_page():
    st.set_page_config(page_title="Transformo-Docs", layout="wide")
    
    # Load and display logo
    logo = load_logo()
    if logo:
        st.sidebar.image(logo, width=250)
    else:
        st.warning(logo_path)
    st.sidebar.title("📄 Transformo Docs")
    pages = {
        "Home": home_page,
        "Upload Document and Processing": document_processing_page,
        "Saved Documents Storage": saved_documents_page,
        "Chat Interface": chat_interface_page,
    }
    page = st.sidebar.radio("Navigate", list(pages.keys()))
    pages[page]()

# Home page function
def home_page():
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.title("🏠 Welcome to Transformo Docs")
        st.markdown("""
        <style>
        .big-font {
            font-size:20px !important;
            color: #1E88E5;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<p class="big-font">🚀 Empowering Document Management</p>', unsafe_allow_html=True)
        
        st.write("""
        Transformo Docs is a powerful solution designed to tackle the challenge of non-machine-readable documents like PDFs and Word files. 
        
        🌐 This app automates the conversion of such documents into machine-readable formats, making them:
        - 🔍 Searchable
        - 📄 Accessible
        - 🤖 Ready for AI integration
        
        Whether you're working with scanned documents or files generated through software, Transformo Docs ensures your data is always organized and easily accessible.
        """)
        
        st.markdown("""
        ---
        ### 🎯 Key Features
        - 📊 Advanced Analytics
        - 🔄 Automated Conversion
        - 🔐 Compliance Ready
        - 📈 Productivity Boost
        """)

    
    st.info("Use the sidebar to navigate through different features of the application.")

    # Custom button styling
    st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        height: 3em;
        background-color: #4CAF50;
        color: white;
        font-size: 16px;
        font-weight: bold;
        border: none;
        border-radius: 5px;
        cursor: pointer;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    </style>
    """, unsafe_allow_html=True)

# Document processing page function
def document_processing_page():
    st.title("🔄 Document Processing")
    
    uploaded_file = upload_document()
    template = st.selectbox(
        "Choose a template for extraction",
        ["Default", "Data Only", "Analytics Only", "Specific Entities"],
        help="Select a predefined template for structuring the output."
    )
    custom_fields = st.multiselect(
        "Select custom fields to extract",
        ["Persons", "Organizations", "Locations", "Dates"],
        help="Choose specific entity types you want to extract from the document."
    )
    
    result = None
    if uploaded_file is not None:
        with st.spinner("Processing document..."):
            try:
                # Validate and extract text from the document
                file_type = validate_document(uploaded_file)
                extracted_text = extract_text(uploaded_file, file_type)
                
                # Process the document with selected template and custom fields
                template = template.lower().replace(" ", "_") if template != "Default" else None
                custom_fields = [field.lower() for field in custom_fields] if custom_fields else None
                result = process_document(extracted_text, template, custom_fields)
                
                if result["warnings"]:
                    st.warning("Processing completed with warnings:")
                    for warning in result["warnings"]:
                        st.write(warning)
                else:
                    st.success("Document processed successfully!")
                
                # Save result in session state
                st.session_state.result = result
            except Exception as e:
                st.error(f"Error: {str(e)}")

    if 'result' in st.session_state:
        display_export_options(st.session_state.result, uploaded_file)
        display_analytics(st.session_state.result)
        display_graphs(st.session_state.result, uploaded_file)
        display_database_options(st.session_state.result, uploaded_file.name)

# Function to handle document upload
def upload_document():
    st.subheader("📤 Upload Document")
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
    
    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx", "txt", "xlsx"])
    
    if uploaded_file is not None:
        st.session_state.uploaded_file = uploaded_file
        st.info(f"File '{uploaded_file.name}' uploaded successfully. Choose a template and custom fields for extraction.")
    
    return st.session_state.uploaded_file

# Function to display export options
def display_export_options(result, uploaded_file):
    st.subheader("💾 Export Options")
    export_format = st.selectbox("Choose export format", ["JSON", "XML"])
    
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

# Function to display analytics
def display_analytics(result):
    st.subheader("📊 Document Analytics")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📏 Basic Metrics")
        st.write(f"**Word Count:** {result['analytics']['word_count']}")
        st.write(f"**Sentence Count:** {result['analytics']['sentence_count']}")
        st.write(f"**Average Sentence Length:** {result['analytics']['average_sentence_length']:.2f} words")

        st.markdown("### 🏷️ Named Entities")
        st.write(f"**Entity Count:** {result['analytics']['entity_count']}")
        st.write("**Most Common Entities:**")
        for entity, count in result['analytics']['most_common_entities']:
            st.write(f"- {entity}: {count}")

    with col2:
        st.markdown("### 🔑 Keywords")
        st.write(f"**Keyword Count:** {result['analytics']['keyword_count']}")

        st.markdown("### 📊 Word Frequency")
        st.write("**Most Common Words:**")
        for word, count in result['analytics']['most_common_words']:
            st.write(f"- {word}: {count}")

    with st.expander("📝 Document Preview"):
        preview_text = result['extracted_text'][:500] + "..." if len(result['extracted_text']) > 500 else result['extracted_text']
        st.text_area("First 500 characters", preview_text, height=200)

# Function to display graphs
def display_graphs(result, uploaded_file):
    st.subheader("📈 Visualizations")
    col1, col2 = st.columns(2)

    with col1:
        # Word Frequency Graph
        word_freq = result['analytics']['most_common_words'][:10]  # Top 10 words
        fig = px.bar(
            x=[word for word, _ in word_freq],
            y=[count for _, count in word_freq],
            labels={'x': 'Word', 'y': 'Frequency'},
            title='Top 10 Most Frequent Words'
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Named Entities Graph
        entity_freq = result['analytics']['most_common_entities'][:10]  # Top 10 entities
        fig = px.bar(
            x=[entity for entity, _ in entity_freq],
            y=[count for _, count in entity_freq],
            labels={'x': 'Entity', 'y': 'Frequency'},
            title='Top 10 Most Common Named Entities'
        )
        st.plotly_chart(fig, use_container_width=True)

    # Basic Metrics Graph
    metrics = {
        'Word Count': result['analytics']['word_count'],
        'Sentence Count': result['analytics']['sentence_count'],
        'Avg Sentence Length': round(result['analytics']['average_sentence_length'], 2)
    }
    fig = go.Figure(data=[
        go.Bar(name=metric, x=[metric], y=[value])
        for metric, value in metrics.items()
    ])
    fig.update_layout(title_text='Basic Document Metrics', barmode='group')
    st.plotly_chart(fig, use_container_width=True)

    # File Size Comparison Graph
    original_size, extracted_size = calculate_file_sizes(uploaded_file, result)
    size_diff = original_size - extracted_size
    size_diff_percentage = (size_diff / original_size) * 100

    fig = go.Figure(data=[
        go.Bar(name='Original Size', x=['Document Size'], y=[original_size]),
        go.Bar(name='Extracted Size', x=['Document Size'], y=[extracted_size])
    ])
    fig.update_layout(title_text='Document Size Comparison (MB)', barmode='group')
    st.plotly_chart(fig, use_container_width=True)

    st.info(f"Size reduction: {size_diff:.2f} MB ({size_diff_percentage:.2f}%)")
    
    # Keyword Information
    st.subheader("🔑 Keyword Information")
    st.write(f"**Total Keywords:** {result['analytics']['keyword_count']}")
    st.write("**Top Keywords:**")
    keyword_data = pd.DataFrame(result['analytics']['most_common_words'], columns=['Keyword', 'Count'])
    st.dataframe(keyword_data)

# Function to display database options
def display_database_options(result, filename):
    st.subheader("💽 Database Options")
    st.info("Choose a database to save the processed document. Currently, only local storage is available.")
    database_options = ["Local Storage", "MongoDB (Disabled)", "PostgreSQL (Disabled)", "MySQL (Disabled)"]
    selected_db = st.selectbox("Select Database", database_options)
    
    if selected_db == "Local Storage":
        if st.button("Save to Local Storage"):
            save_to_database(result, filename)
            st.success("Document saved to local storage successfully!")
    else:
        st.warning("Selected database option is currently disabled.")

# Function for saved documents page
def saved_documents_page():
    st.title("💾 Saved Documents")
    st.info("This page displays all documents saved in the local storage.")
    
    documents = get_saved_documents()
    if not documents:
        st.warning("No saved documents found.")
        return
    
    df = pd.DataFrame(documents)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date', ascending=False)
    
    for _, row in df.iterrows():
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            st.write(f"**{row['filename']}** - {row['date'].strftime('%Y-%m-%d %H:%M:%S')}")
        with col2:
            if st.button("Preview", key=f"preview_{row['id']}"):
                st.json(row['data'])
        with col3:
            if st.button("Download", key=f"download_{row['id']}"):
                st.download_button(
                    label="Download JSON",
                    data=row['data'],
                    file_name=f"{row['filename']}_processed.json",
                    mime="application/json"
                )
        with col4:
            if st.button("Delete", key=f"delete_{row['id']}"):
                delete_document(row['id'])
                st.experimental_rerun()


# Function for chat interface page
def chat_interface_page():
    st.title("💬 Chat with Your Document")
    st.info("This feature allows you to ask questions about your processed documents.")

    documents = get_saved_documents()
    if not documents:
        st.warning("No saved documents found. Process and save a document first.")
        return

    selected_doc = st.selectbox("Select a document to chat with", [doc['filename'] for doc in documents])
    selected_data = next(doc for doc in documents if doc['filename'] == selected_doc)

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    user_query = st.text_input("Ask a question about the document:")

    if user_query:
        document_text = json.loads(selected_data['data'])['extracted_text']
        answer = ask_question_to_document(user_query, document_text)
        st.session_state["chat_history"].append({"question": user_query, "answer": answer})

    if st.session_state["chat_history"]:
        st.write("### 🗨️ Chat History")
        for chat in st.session_state["chat_history"]:
            st.markdown(f"**You:** {chat['question']}")
            st.markdown(f"**Transformo Docs:** {chat['answer']}")

    if st.button("Clear Chat History"):
        st.session_state["chat_history"] = []
        st.success("Chat history cleared!")

# Main function to run the Streamlit app
def main():
    setup_page()

# Entry point of the script
if __name__ == "__main__":
    main()